from typing import cast

from sqlalchemy.orm import Session

from app.models import Device, FraudAlert, LoginEvent, Transaction, User
from app.services.explanation_engine import generate_explanation
from app.services.friction_engine import determine_friction_action
from app.services.log_engine import create_security_log
from app.services.message_service import create_bank_message
from app.services.mule_engine import create_mule_ring
from app.services.risk_engine import calculate_login_risk, calculate_transaction_risk
from app.services.token_engine import detect_token_theft
from app.services.trust_engine import update_trust_score


def _user_from_input(db: Session, input_data, fallback_user: User | None = None):
    user_id = getattr(input_data, "user_id", None)
    if user_id is not None:
        return db.get(User, user_id)
    return fallback_user


def simulate_login(db: Session, input_data, fallback_user: User | None = None):
    user = _user_from_input(db, input_data, fallback_user)
    if user is None:
        raise ValueError("User not found")

    previous_login = (
        db.query(LoginEvent)
        .filter(LoginEvent.user_id == user.id)
        .order_by(LoginEvent.created_at.desc())
        .first()
    )
    risk = calculate_login_risk(input_data, user, previous_login)

    device = db.query(Device).filter(Device.device_hash == input_data.device_hash).first()
    if device is None:
        device = Device(
            user_id=user.id,
            device_hash=input_data.device_hash,
            device_label=input_data.device_label,
            browser=input_data.browser,
            os=input_data.os,
            is_trusted=False,
        )
        db.add(device)

    event = LoginEvent(
        user_id=user.id,
        device_hash=input_data.device_hash,
        ip_address=input_data.ip_address,
        country=input_data.country,
        city=input_data.city,
        is_vpn=input_data.is_vpn,
        is_proxy=input_data.is_proxy,
        success=input_data.success,
        failed_attempts=input_data.failed_attempts,
        risk_score=risk["risk_score"],
    )
    db.add(event)

    alert = None
    if risk["risk_score"] >= 61:
        explanation = generate_explanation(
            "LOGIN_RISK",
            risk["risk_score"],
            risk["severity"],
            risk["reasons"],
        )
        alert = FraudAlert(
            user_id=user.id,
            alert_type="LOGIN_RISK",
            severity=risk["severity"],
            risk_score=risk["risk_score"],
            title=f"{risk['severity']} login risk detected",
            explanation=explanation["summary"],
            recommended_action=explanation["recommended_action"],
            status="OPEN",
        )
        db.add(alert)
        update_trust_score(db, user, risk["reasons"], "login_risk")
    elif risk["risk_score"] <= 30:
        update_trust_score(db, user, ["Trusted device normal login"], "normal_login")

    db.commit()
    db.refresh(event)
    return {"login_event": event, "risk": risk, "alert": alert}


def simulate_transaction(db: Session, input_data, fallback_user: User | None = None):
    user = _user_from_input(db, input_data, fallback_user)
    if user is None:
        raise ValueError("User not found")

    latest_login = (
        db.query(LoginEvent)
        .filter(LoginEvent.user_id == user.id)
        .order_by(LoginEvent.created_at.desc())
        .first()
    )
    risk = calculate_transaction_risk(input_data, user, latest_login, db=db)
    risk_score = int(risk["risk_score"])
    trust_score = cast(int, user.trust_score)
    friction = determine_friction_action(risk_score, trust_score)
    status_map = {
        "ALLOW": "ALLOWED",
        "REQUIRE_2FA": "REQUIRE_2FA",
        "HOLD_FOR_REVIEW": "HELD",
        "BLOCK_AND_ALERT": "BLOCKED",
    }
    amount = float(input_data.amount)
    sender_balance_before = float(cast(float, user.balance))
    recipient = (
        db.query(User)
        .filter(User.account_number == input_data.to_account)
        .first()
    )
    recipient_balance_before = (
        float(cast(float, recipient.balance)) if recipient is not None else None
    )
    balance_applied = False
    balance_message = "Balance unchanged while the transaction is pending review."
    transaction_status = status_map[friction["action"]]

    if transaction_status == "ALLOWED":
        if sender_balance_before >= amount:
            user.balance = sender_balance_before - amount
            if recipient is not None:
                recipient.balance = recipient_balance_before + amount
            balance_applied = True
            balance_message = "Transfer posted to the account balance."
        else:
            transaction_status = "DECLINED"
            friction = {
                **friction,
                "action": "DECLINED_INSUFFICIENT_FUNDS",
                "label": "Declined",
                "message": "Insufficient available balance.",
                "customer_message": "Insufficient available balance.",
                "analyst_message": "Low-risk transaction declined because the source account lacks available funds.",
            }
            balance_message = "Transfer declined because the source account has insufficient funds."

    transaction = Transaction(
        user_id=user.id,
        from_account=user.account_number or "UNKNOWN",
        to_account=input_data.to_account,
        amount=amount,
        currency=input_data.currency,
        recipient_name=input_data.recipient_name,
        recipient_is_new=input_data.recipient_is_new,
        status=transaction_status,
        risk_score=risk["risk_score"],
    )
    db.add(transaction)

    if transaction_status in {"REQUIRE_2FA", "HELD", "BLOCKED"}:
        create_bank_message(
            db,
            user_id=user.id,
            channel="IN_APP",
            title="Transaction security review",
            body=(
                "Your transfer was held or blocked for security review. "
                "Please open the banking app to review the status."
            ),
            message_type="TRANSACTION_ALERT",
            risk_level="CRITICAL" if transaction_status == "BLOCKED" else "HIGH",
        )

    alert = None
    if risk["risk_score"] >= 61:
        explanation = generate_explanation(
            "TRANSACTION_RISK",
            risk["risk_score"],
            risk["severity"],
            risk["reasons"],
        )
        alert = FraudAlert(
            user_id=user.id,
            alert_type="TRANSACTION_RISK",
            severity=risk["severity"],
            risk_score=risk["risk_score"],
            title=f"{risk['severity']} transaction risk detected",
            explanation=explanation["summary"],
            recommended_action=explanation["recommended_action"],
            status="OPEN",
        )
        db.add(alert)
        db.flush()
        create_bank_message(
            db,
            user_id=user.id,
            channel="IN_APP",
            title="Security alert on your account",
            body=(
                "AEGIS detected unusual activity on your account. "
                "Please review your account from inside the banking app."
            ),
            message_type="FRAUD_ALERT",
            risk_level="CRITICAL" if risk["risk_score"] >= 81 else "HIGH",
            related_alert_id=alert.id,
        )
        update_trust_score(db, user, ["High-risk transaction", *risk["reasons"]], "high_risk_transaction")
    elif risk["risk_score"] <= 30:
        update_trust_score(db, user, ["Normal transaction"], "normal_transaction")

    db.commit()
    db.refresh(transaction)
    db.refresh(user)
    if recipient is not None:
        db.refresh(recipient)
    return {
        "transaction": transaction,
        "risk": risk,
        "friction": friction,
        "alert": alert,
        "balance": {
            "applied": balance_applied,
            "message": balance_message,
            "from_account": user.account_number,
            "from_before": sender_balance_before,
            "from_after": float(cast(float, user.balance)),
            "to_account": input_data.to_account,
            "to_before": recipient_balance_before,
            "to_after": float(cast(float, recipient.balance)) if recipient is not None else None,
        },
    }


def simulate_security_log(db: Session, input_data, fallback_user: User | None = None):
    user = _user_from_input(db, input_data, fallback_user)
    return create_security_log(db, input_data, user)


def simulate_token_theft(db: Session, input_data, fallback_user: User | None = None):
    user = _user_from_input(db, input_data, fallback_user)
    return detect_token_theft(db, input_data, user)


def simulate_mule_ring(db: Session, input_data):
    mule_account = input_data.mule_account or "AL472091000000009999"
    return create_mule_ring(db, mule_account, input_data.amount)

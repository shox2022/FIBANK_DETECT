from datetime import datetime, timedelta

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import (
    AnalystNote,
    BankMessage,
    Device,
    FraudAlert,
    LoginEvent,
    MuleEdge,
    RiskRule,
    SecurityLog,
    Transaction,
    TrustScoreHistory,
    User,
)


SEED_START = datetime(2026, 5, 20, 9, 0, 0)


def upsert_user(db, data):
    user = db.query(User).filter(User.email == data["email"]).first()
    if user is None:
        user = User(**data, password_hash=hash_password("password123"))
        db.add(user)
        db.flush()
        return user

    for key, value in data.items():
        setattr(user, key, value)
    return user


def ensure_device(db, user, **data):
    device = db.query(Device).filter(Device.device_hash == data["device_hash"]).first()
    if device is None:
        device = Device(user_id=user.id, **data)
        db.add(device)
    return device


def ensure_login_event(db, user, created_at, **data):
    event = (
        db.query(LoginEvent)
        .filter(
            LoginEvent.user_id == user.id,
            LoginEvent.device_hash == data["device_hash"],
            LoginEvent.ip_address == data["ip_address"],
            LoginEvent.created_at == created_at,
        )
        .first()
    )
    if event is None:
        event = LoginEvent(user_id=user.id, created_at=created_at, **data)
        db.add(event)
    return event


def ensure_transaction(db, user, created_at, **data):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user.id,
            Transaction.from_account == data["from_account"],
            Transaction.to_account == data["to_account"],
            Transaction.amount == data["amount"],
            Transaction.created_at == created_at,
        )
        .first()
    )
    if transaction is None:
        transaction = Transaction(user_id=user.id, created_at=created_at, **data)
        db.add(transaction)
    return transaction


def ensure_alert(db, created_at, **data):
    alert = (
        db.query(FraudAlert)
        .filter(FraudAlert.title == data["title"], FraudAlert.created_at == created_at)
        .first()
    )
    if alert is None:
        alert = FraudAlert(created_at=created_at, **data)
        db.add(alert)
    return alert


def ensure_log(db, created_at, **data):
    log = (
        db.query(SecurityLog)
        .filter(
            SecurityLog.event_type == data["event_type"],
            SecurityLog.endpoint == data["endpoint"],
            SecurityLog.payload_sample == data["payload_sample"],
            SecurityLog.created_at == created_at,
        )
        .first()
    )
    if log is None:
        log = SecurityLog(created_at=created_at, **data)
        db.add(log)
    return log


def ensure_trust_history(db, user, created_at, **data):
    history = (
        db.query(TrustScoreHistory)
        .filter(
            TrustScoreHistory.user_id == user.id,
            TrustScoreHistory.reason == data["reason"],
            TrustScoreHistory.created_at == created_at,
        )
        .first()
    )
    if history is None:
        history = TrustScoreHistory(user_id=user.id, created_at=created_at, **data)
        db.add(history)
    return history


def ensure_mule_edge(db, created_at, **data):
    edge = (
        db.query(MuleEdge)
        .filter(
            MuleEdge.from_account == data["from_account"],
            MuleEdge.to_account == data["to_account"],
            MuleEdge.amount == data["amount"],
            MuleEdge.created_at == created_at,
        )
        .first()
    )
    if edge is None:
        edge = MuleEdge(created_at=created_at, **data)
        db.add(edge)
    return edge


def ensure_bank_message(db, user, created_at, **data):
    message = (
        db.query(BankMessage)
        .filter(
            BankMessage.user_id == user.id,
            BankMessage.title == data["title"],
            BankMessage.body == data["body"],
        )
        .first()
    )
    if message is None:
        message = BankMessage(user_id=user.id, created_at=created_at, **data)
        db.add(message)
        return message

    for key, value in data.items():
        setattr(message, key, value)
    message.created_at = created_at
    return message


def upsert_risk_rule(db, **data):
    rule = db.query(RiskRule).filter(RiskRule.code == data["code"]).first()
    if rule is None:
        rule = RiskRule(**data)
        db.add(rule)
        return rule

    rule.description = data["description"]
    rule.points = data["points"]
    rule.enabled = data["enabled"]
    return rule


def ensure_analyst_note(db, alert, analyst, **data):
    note = (
        db.query(AnalystNote)
        .filter(
            AnalystNote.alert_id == alert.id,
            AnalystNote.analyst_user_id == analyst.id,
            AnalystNote.action_type == data["action_type"],
            AnalystNote.note == data["note"],
        )
        .first()
    )
    if note is None:
        note = AnalystNote(alert_id=alert.id, analyst_user_id=analyst.id, **data)
        db.add(note)
    return note


def seed_users(db):
    users = [
        {
            "name": "Ardit Hoxha",
            "email": "customer@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Tirana",
            "trust_score": 78,
            "average_transaction_amount": 120.0,
            "account_number": "AL472091000000000001",
            "balance": 8500.0,
        },
        {
            "name": "Elena Marku",
            "email": "analyst@aegis.test",
            "role": "ANALYST",
            "home_country": "Albania",
            "home_city": "Tirana",
            "trust_score": 90,
            "average_transaction_amount": 0.0,
            "account_number": None,
            "balance": 0.0,
        },
        {
            "name": "Bank Security Admin",
            "email": "admin@aegis.test",
            "role": "ADMIN",
            "home_country": "Albania",
            "home_city": "Tirana",
            "trust_score": 95,
            "average_transaction_amount": 0.0,
            "account_number": None,
            "balance": 0.0,
        },
        {
            "name": "Lira Kola",
            "email": "lira.kola@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Durres",
            "trust_score": 72,
            "average_transaction_amount": 80.0,
            "account_number": "AL472091000000000002",
            "balance": 2200.0,
        },
        {
            "name": "Besnik Dervishi",
            "email": "besnik.dervishi@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Shkoder",
            "trust_score": 66,
            "average_transaction_amount": 150.0,
            "account_number": "AL472091000000000003",
            "balance": 3900.0,
        },
        {
            "name": "Mira Leka",
            "email": "mira.leka@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Vlore",
            "trust_score": 81,
            "average_transaction_amount": 95.0,
            "account_number": "AL472091000000000004",
            "balance": 4600.0,
        },
        {
            "name": "Dritan Sula",
            "email": "dritan.sula@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Elbasan",
            "trust_score": 58,
            "average_transaction_amount": 210.0,
            "account_number": "AL472091000000000005",
            "balance": 3100.0,
        },
        {
            "name": "Nora Basha",
            "email": "nora.basha@aegis.test",
            "role": "CUSTOMER",
            "home_country": "Albania",
            "home_city": "Korce",
            "trust_score": 74,
            "average_transaction_amount": 110.0,
            "account_number": "AL472091000000000006",
            "balance": 5300.0,
        },
    ]
    return {data["email"]: upsert_user(db, data) for data in users}


def seed_demo_foundation(db, users):
    customer = users["customer@aegis.test"]

    ensure_device(
        db,
        customer,
        device_hash="dev_hash_ardit_trusted_laptop",
        device_label="Ardit's trusted laptop",
        browser="Chrome",
        os="Windows",
        is_trusted=True,
        first_seen_at=SEED_START - timedelta(days=30),
        last_seen_at=SEED_START,
        created_at=SEED_START - timedelta(days=30),
    )

    ensure_login_event(
        db,
        customer,
        SEED_START - timedelta(days=3),
        device_hash="dev_hash_ardit_trusted_laptop",
        ip_address="185.53.12.10",
        country="Albania",
        city="Tirana",
        is_vpn=False,
        is_proxy=False,
        success=True,
        failed_attempts=0,
        risk_score=5,
    )
    ensure_login_event(
        db,
        customer,
        SEED_START - timedelta(hours=2),
        device_hash="dev_hash_ardit_trusted_laptop",
        ip_address="185.53.12.11",
        country="Albania",
        city="Tirana",
        is_vpn=False,
        is_proxy=False,
        success=True,
        failed_attempts=0,
        risk_score=3,
    )

    ensure_transaction(
        db,
        customer,
        SEED_START - timedelta(days=2),
        from_account="AL472091000000000001",
        to_account="AL472091000000000010",
        amount=65.0,
        currency="EUR",
        recipient_name="Utility Provider",
        recipient_is_new=False,
        status="ALLOWED",
        risk_score=8,
    )
    ensure_transaction(
        db,
        customer,
        SEED_START - timedelta(days=1),
        from_account="AL472091000000000001",
        to_account="AL472091000000000011",
        amount=120.0,
        currency="EUR",
        recipient_name="Rent Account",
        recipient_is_new=False,
        status="ALLOWED",
        risk_score=10,
    )

    suspicious_time = SEED_START + timedelta(hours=1)
    ensure_alert(
        db,
        suspicious_time,
        user_id=customer.id,
        alert_type="IMPOSSIBLE_TRAVEL",
        severity="HIGH",
        risk_score=78,
        title="Impossible travel login pattern detected",
        explanation=(
            "A login from Germany appeared shortly after a normal Albania login, "
            "using a new device and VPN metadata."
        ),
        recommended_action="Require step-up authentication and review recent activity.",
        status="OPEN",
    )
    ensure_alert(
        db,
        suspicious_time + timedelta(minutes=20),
        user_id=customer.id,
        alert_type="HIGH_RISK_TRANSACTION",
        severity="CRITICAL",
        risk_score=92,
        title="High-value transfer to new beneficiary blocked",
        explanation=(
            "The customer attempted a transfer far above their normal amount after "
            "a suspicious login event."
        ),
        recommended_action="Block transfer, contact customer, and investigate account access.",
        status="OPEN",
    )

    ensure_log(
        db,
        suspicious_time + timedelta(minutes=35),
        user_id=customer.id,
        event_type="SQL_INJECTION_ATTEMPT",
        endpoint="/api/auth/login",
        ip_address="91.220.33.44",
        payload_sample="' OR '1'='1 --",
        risk_score=95,
        severity="CRITICAL",
    )

    ensure_trust_history(
        db,
        customer,
        suspicious_time + timedelta(minutes=5),
        old_score=78,
        new_score=53,
        reason="Impossible travel login with new device and VPN",
    )

    mule_account = "AL472091000000009999"
    mule_edges = [
        ("AL472091000000000002", mule_account, 420.0, 85),
        ("AL472091000000000003", mule_account, 610.0, 88),
        ("AL472091000000000004", mule_account, 390.0, 82),
        (mule_account, "AL472091000000008888", 1180.0, 91),
    ]
    for index, (from_account, to_account, amount, risk_score) in enumerate(mule_edges):
        ensure_mule_edge(
            db,
            suspicious_time + timedelta(minutes=45 + index),
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            risk_score=risk_score,
        )


def seed_risk_rules(db):
    rules = [
        ("LOGIN_NEW_DEVICE", "New device used during login", 20),
        ("LOGIN_VPN_DETECTED", "VPN detected during login", 20),
        ("LOGIN_PROXY_DETECTED", "Proxy detected during login", 15),
        ("LOGIN_VPN", "VPN detected during login", 20),
        ("LOGIN_PROXY", "Proxy detected during login", 15),
        ("LOGIN_NEW_COUNTRY", "Login from country outside customer baseline", 15),
        ("LOGIN_IMPOSSIBLE_TRAVEL", "Geographically impossible login sequence", 35),
        ("LOGIN_FAILED_ATTEMPTS", "Multiple failed login attempts", 15),
        ("LOGIN_UNUSUAL_HOUR", "Login at an unusual hour", 10),
        ("TX_AMOUNT_5X_AVERAGE", "Transaction amount exceeds 5x customer average", 25),
        ("TX_AMOUNT_SPIKE", "Transaction amount sharply exceeds customer baseline", 25),
        ("TX_NEW_BENEFICIARY", "Transfer to a new beneficiary", 15),
        ("TX_AFTER_SUSPICIOUS_LOGIN", "Transaction after suspicious login", 25),
        ("TX_BURST_ACTIVITY", "Many transactions in a short time", 20),
        ("TX_FLAGGED_RECIPIENT", "Recipient account already flagged", 30),
        ("TX_VPN_BEFORE_TRANSFER", "VPN login before transaction", 20),
        ("LOG_SQL_INJECTION", "SQL injection pattern detected", 80),
        ("LOG_BRUTE_FORCE", "Brute force pattern detected", 50),
        ("LOG_SUSPICIOUS_ENDPOINT", "Suspicious endpoint access", 35),
        ("LOG_TOKEN_REUSE", "Token reuse detected", 70),
        ("TOKEN_DIFFERENT_IP", "Same token used from a different IP", 35),
        ("TOKEN_DIFFERENT_COUNTRY", "Same token used from a different country", 40),
        ("TOKEN_DIFFERENT_DEVICE", "Same token used from a different device", 35),
        ("TOKEN_VPN_PROXY", "Same token used with VPN or proxy metadata", 50),
        ("MULE_FAN_IN", "One account receives funds from unrelated accounts", 30),
        ("MULE_PASS_THROUGH", "Account sends out most received funds quickly", 35),
        ("TRUST_VPN_DECREASE", "Trust decreases when VPN activity appears in risky context", 10),
        ("TRUST_NORMAL_INCREASE", "Trust can increase after normal verified behavior", 2),
        ("ML_XGBOOST_SCORE", "XGBoost fraud probability contributes to final transaction risk when enabled", 35),
    ]
    for code, description, points in rules:
        upsert_risk_rule(
            db,
            code=code,
            description=description,
            points=points,
            enabled=True,
        )


def seed_analyst_notes(db, users):
    analyst = users["analyst@aegis.test"]
    alerts = (
        db.query(FraudAlert)
        .filter(FraudAlert.severity.in_(["HIGH", "CRITICAL"]))
        .order_by(FraudAlert.created_at.asc())
        .limit(2)
        .all()
    )
    for alert in alerts:
        ensure_analyst_note(
            db,
            alert,
            analyst,
            note="Initial triage opened. Reviewing customer login, transaction, and trust timeline.",
            action_type="NOTE",
            old_status=None,
            new_status=None,
            created_at=alert.created_at + timedelta(minutes=2),
        )
        ensure_analyst_note(
            db,
            alert,
            analyst,
            note="Case queued for investigation due to elevated severity and risk score.",
            action_type="ESCALATED",
            old_status=None,
            new_status=None,
            created_at=alert.created_at + timedelta(minutes=4),
        )


def seed_bank_messages(db, users):
    customer = users["customer@aegis.test"]
    messages = [
        {
            "created_at": SEED_START - timedelta(hours=6),
            "channel": "SMS",
            "title": "New login detected",
            "body": (
                "AEGIS detected a new login to your banking account from Tirana, Albania. "
                "If this was not you, open the official banking app and review your account security."
            ),
            "message_type": "SECURITY_ALERT",
            "risk_level": "LOW",
        },
        {
            "created_at": SEED_START - timedelta(days=2),
            "channel": "EMAIL",
            "title": "Transfer confirmation",
            "body": (
                "Your transfer of 65.00 EUR was processed successfully. "
                "You can view details inside your banking app."
            ),
            "message_type": "TRANSACTION_ALERT",
            "risk_level": "LOW",
        },
        {
            "created_at": SEED_START + timedelta(hours=1, minutes=20),
            "channel": "IN_APP",
            "title": "Transaction held for review",
            "body": (
                "Your transfer was held for security review. Please open the banking app "
                "to complete verification."
            ),
            "message_type": "TRANSACTION_ALERT",
            "risk_level": "HIGH",
        },
        {
            "created_at": SEED_START - timedelta(hours=1),
            "channel": "IN_APP",
            "title": "Protect yourself from phishing",
            "body": (
                "The bank will never ask for your password, PIN, card number, CVV, or OTP "
                "through email or SMS. Always verify messages inside the official banking app."
            ),
            "message_type": "GENERAL_NOTICE",
            "risk_level": "LOW",
        },
    ]
    for message in messages:
        created_at = message.pop("created_at")
        ensure_bank_message(db, customer, created_at, **message, official=True)


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = seed_users(db)
        seed_demo_foundation(db, users)
        seed_risk_rules(db)
        seed_bank_messages(db, users)
        seed_analyst_notes(db, users)
        db.commit()
        print("AEGIS seed complete. Demo users and risk rules are ready.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

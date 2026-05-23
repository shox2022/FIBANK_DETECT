from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy.orm import Session

from app.models import LoginEvent, MuleEdge, Transaction, User
from app.services.ml_feature_builder import build_transaction_features
from app.services.ml_score_engine import get_ml_transaction_score


def cap_score(score: int) -> int:
    return max(0, min(100, score))


def get_severity(risk_score: int) -> str:
    if risk_score <= 30:
        return "LOW"
    if risk_score <= 60:
        return "MEDIUM"
    if risk_score <= 80:
        return "HIGH"
    return "CRITICAL"


def _value(input_data: Any, field: str, default=None):
    if isinstance(input_data, dict):
        return input_data.get(field, default)
    return getattr(input_data, field, default)


def _as_datetime(value: Any, default: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        return value
    return default or datetime.utcnow()


def calculate_login_risk(input_data: Any, user: User, previous_login: LoginEvent | None):
    score = 0
    reasons = []

    device_hash = cast(str | None, _value(input_data, "device_hash"))
    country = cast(str | None, _value(input_data, "country"))
    is_vpn = bool(_value(input_data, "is_vpn", False))
    is_proxy = bool(_value(input_data, "is_proxy", False))
    failed_attempts = int(_value(input_data, "failed_attempts", 0) or 0)
    created_at = _as_datetime(_value(input_data, "created_at", datetime.utcnow()))

    known_device = any(cast(str, device.device_hash) == device_hash for device in user.devices)
    if not known_device:
        score += 20
        reasons.append("New device")

    if is_vpn:
        score += 20
        reasons.append("VPN detected")

    if is_proxy:
        score += 15
        reasons.append("Proxy detected")

    home_country = cast(str | None, user.home_country)
    if country and home_country and country != home_country:
        score += 15
        reasons.append("New country")

    if previous_login and cast(str | None, previous_login.country) != country:
        previous_created_at = cast(datetime, previous_login.created_at)
        if created_at - previous_created_at <= timedelta(hours=4):
            score += 35
            reasons.append("Impossible travel")

    if failed_attempts >= 3:
        score += 15
        reasons.append("Multiple failed login attempts")

    if created_at.hour < 6 or created_at.hour > 23:
        score += 10
        reasons.append("Login from unusual hour")

    risk_score = cap_score(score)
    return {
        "risk_score": risk_score,
        "severity": get_severity(risk_score),
        "reasons": reasons or ["Known login pattern"],
    }


def calculate_transaction_risk(
    input_data: Any,
    user: User,
    latest_login: LoginEvent | None,
    db: Session | None = None,
):
    rule_score = 0
    reasons = []

    amount = float(_value(input_data, "amount", 0) or 0)
    to_account = cast(str | None, _value(input_data, "to_account"))
    recipient_is_new = bool(_value(input_data, "recipient_is_new", False))
    created_at = _as_datetime(_value(input_data, "created_at", datetime.utcnow()))
    average_transaction_amount = cast(float, user.average_transaction_amount)
    user_id = cast(int, user.id)
    user_trust_score = cast(int, user.trust_score)

    if average_transaction_amount and amount > average_transaction_amount * 5:
        rule_score += 25
        reasons.append("Amount higher than 5x user average")

    if recipient_is_new:
        rule_score += 15
        reasons.append("New beneficiary")

    if latest_login and cast(int, latest_login.risk_score) >= 60:
        rule_score += 25
        reasons.append("Transaction after suspicious login")

    if db is not None:
        recent_count = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user.id,
                Transaction.created_at >= created_at - timedelta(minutes=10),
            )
            .count()
        )
        if recent_count >= 3:
            rule_score += 20
            reasons.append("Many transactions in short time")

        if to_account:
            flagged_edges = (
                db.query(MuleEdge)
                .filter(MuleEdge.to_account == to_account, MuleEdge.risk_score >= 80)
                .count()
            )
            if flagged_edges:
                rule_score += 30
                reasons.append("Recipient already flagged")

    if latest_login and cast(bool, latest_login.is_vpn):
        rule_score += 20
        reasons.append("VPN login before transaction")

    rule_score = cap_score(rule_score)
    transaction_context = {
        "amount": amount,
        "to_account": to_account,
        "recipient_is_new": recipient_is_new,
        "currency": _value(input_data, "currency", "EUR"),
        "created_at": created_at,
    }
    if db is not None:
        ml_features = build_transaction_features(db, user, transaction_context, latest_login)
    else:
        ml_features = {
            "amount": amount,
            "recipient_is_new": int(recipient_is_new),
            "trust_score": user_trust_score,
            "average_transaction_amount": average_transaction_amount,
        }

    ml_result = get_ml_transaction_score(
        transaction_data=ml_features,
        user_context={"user_id": user_id},
    )

    ml_score = float(ml_result.get("ml_score", 0) or 0)
    ml_enabled = bool(ml_result.get("enabled", False))
    if ml_enabled:
        risk_score = cap_score(round((rule_score * 0.65) + (ml_score * 0.35)))
    else:
        risk_score = rule_score

    final_reasons = list(reasons or ["Transaction matches expected behavior"])
    if ml_enabled:
        ml_band = str(ml_result.get("ml_risk_band", "UNKNOWN"))
        final_reasons.append(f"XGBoost ML model classified transaction as {ml_band} risk")
        final_reasons.append(
            f"XGBoost fraud probability: {float(ml_result.get('ml_probability', 0) or 0) * 100:.1f}%"
        )

    return {
        "risk_score": risk_score,
        "severity": get_severity(risk_score),
        "reasons": final_reasons,
        "rule_score": rule_score,
        "ml_score": ml_score,
        "ml_probability": ml_result.get("ml_probability", 0),
        "ml_flag": ml_result.get("ml_flag", 0),
        "ml_risk_band": ml_result.get("ml_risk_band", "DISABLED"),
        "ml_model_version": ml_result.get("model_version", "unknown"),
        "ml_enabled": ml_enabled,
        "ml_missing_features": ml_result.get("missing_features", []),
        "ml_explanation": ml_result.get("explanation", ""),
    }


def calculate_security_log_risk(input_data: Any):
    payload = str(_value(input_data, "payload_sample", "") or "").lower()
    endpoint = str(_value(input_data, "endpoint", "") or "").lower()
    event_type = str(_value(input_data, "event_type", "") or "").lower()
    score = 0
    reasons = []

    sql_patterns = ["' or '1'='1", "union select", "drop table", "--", "/*", "xp_cmdshell"]
    matched_sql_patterns = [pattern for pattern in sql_patterns if pattern in payload]
    if matched_sql_patterns:
        score += 80
        reasons.append("SQL injection pattern")
        if len(matched_sql_patterns) > 1:
            score += 20
            reasons.append("Multiple SQL injection indicators")

    if "brute" in event_type or "failed" in payload:
        score += 50
        reasons.append("Brute force pattern")

    if any(path in endpoint for path in ["/admin", "/internal", "/debug"]):
        score += 35
        reasons.append("Suspicious endpoint access")

    if "token reuse" in event_type or "reused token" in payload:
        score += 70
        reasons.append("Token reuse")

    risk_score = cap_score(score)
    return {
        "risk_score": risk_score,
        "severity": get_severity(risk_score),
        "reasons": reasons or ["No suspicious log pattern"],
    }


def calculate_token_theft_risk(input_data: Any):
    score = 0
    reasons = []

    if _value(input_data, "original_ip_address") != _value(input_data, "new_ip_address"):
        score += 35
        reasons.append("Same token different IP")

    if _value(input_data, "original_country") != _value(input_data, "new_country"):
        score += 40
        reasons.append("Same token different country")

    if _value(input_data, "original_device_hash") != _value(input_data, "new_device_hash"):
        score += 35
        reasons.append("Same token different device")

    if bool(_value(input_data, "is_vpn", False)) or bool(_value(input_data, "is_proxy", False)):
        score += 50
        reasons.append("Same token with VPN/proxy")

    risk_score = cap_score(score)
    return {
        "risk_score": risk_score,
        "severity": get_severity(risk_score),
        "reasons": reasons or ["No token theft indicators"],
    }


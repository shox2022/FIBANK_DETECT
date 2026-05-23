from sqlalchemy.orm import Session

from app.models import FraudAlert, SecurityLog, User
from app.services.explanation_engine import generate_explanation
from app.services.message_service import create_bank_message
from app.services.risk_engine import calculate_security_log_risk
from app.services.trust_engine import update_trust_score


SUSPICIOUS_PATTERNS = [
    "' OR '1'='1",
    "UNION SELECT",
    "DROP TABLE",
    "--",
    "/*",
    "xp_cmdshell",
    "<script",
]


def detect_suspicious_payload(payload_sample: str) -> list[str]:
    payload_lower = payload_sample.lower()
    return [
        pattern
        for pattern in SUSPICIOUS_PATTERNS
        if pattern.lower() in payload_lower
    ]


def create_security_log(db: Session, input_data, user: User | None = None):
    risk = calculate_security_log_risk(input_data)
    log = SecurityLog(
        user_id=user.id if user else getattr(input_data, "user_id", None),
        event_type=getattr(input_data, "event_type", "SECURITY_EVENT"),
        endpoint=getattr(input_data, "endpoint", None),
        ip_address=getattr(input_data, "ip_address", None),
        payload_sample=getattr(input_data, "payload_sample", None),
        risk_score=risk["risk_score"],
        severity=risk["severity"],
    )
    db.add(log)
    db.flush()

    alert = None
    if risk["risk_score"] >= 61:
        explanation = generate_explanation(
            "SECURITY_LOG",
            risk["risk_score"],
            risk["severity"],
            risk["reasons"],
        )
        alert = FraudAlert(
            user_id=log.user_id,
            alert_type="SECURITY_LOG",
            severity=risk["severity"],
            risk_score=risk["risk_score"],
            title=f"{risk['severity']} security log detected",
            explanation=explanation["summary"],
            recommended_action=explanation["recommended_action"],
            status="OPEN",
        )
        db.add(alert)
        db.flush()
        if user:
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
            update_trust_score(db, user, risk["reasons"], "security_log")

    db.commit()
    db.refresh(log)
    return {"log": log, "risk": risk, "alert": alert}

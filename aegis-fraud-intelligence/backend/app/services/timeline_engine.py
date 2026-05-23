from sqlalchemy.orm import Session

from app.models import FraudAlert, LoginEvent, SecurityLog, Transaction, TrustScoreHistory


def get_user_timeline(db: Session, user_id: int):
    events = []

    for item in db.query(LoginEvent).filter(LoginEvent.user_id == user_id).all():
        events.append(
            {
                "event_type": "LOGIN",
                "title": f"Login from {item.city}, {item.country}",
                "description": f"Device {item.device_hash}, VPN={item.is_vpn}, proxy={item.is_proxy}",
                "severity": None,
                "risk_score": item.risk_score,
                "created_at": item.created_at,
            }
        )

    for item in db.query(Transaction).filter(Transaction.user_id == user_id).all():
        events.append(
            {
                "event_type": "TRANSACTION",
                "title": f"{item.status} transfer to {item.recipient_name}",
                "description": f"{item.amount} {item.currency} to {item.to_account}",
                "severity": None,
                "risk_score": item.risk_score,
                "created_at": item.created_at,
            }
        )

    for item in db.query(SecurityLog).filter(SecurityLog.user_id == user_id).all():
        events.append(
            {
                "event_type": "SECURITY_LOG",
                "title": item.event_type,
                "description": item.payload_sample or "",
                "severity": item.severity,
                "risk_score": item.risk_score,
                "created_at": item.created_at,
            }
        )

    for item in db.query(FraudAlert).filter(FraudAlert.user_id == user_id).all():
        events.append(
            {
                "event_type": "FRAUD_ALERT",
                "title": item.title,
                "description": item.explanation,
                "severity": item.severity,
                "risk_score": item.risk_score,
                "created_at": item.created_at,
            }
        )

    for item in db.query(TrustScoreHistory).filter(TrustScoreHistory.user_id == user_id).all():
        events.append(
            {
                "event_type": "TRUST_SCORE",
                "title": f"Trust score {item.old_score} -> {item.new_score}",
                "description": item.reason,
                "severity": None,
                "risk_score": None,
                "created_at": item.created_at,
            }
        )

    return sorted(events, key=lambda event: event["created_at"])


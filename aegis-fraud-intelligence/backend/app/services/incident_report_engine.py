from datetime import datetime
from typing import cast

from sqlalchemy.orm import Session

from app.models import FraudAlert, User
from app.services.timeline_engine import get_user_timeline


def generate_incident_report(db: Session, alert_id: int):
    alert = db.get(FraudAlert, alert_id)
    if alert is None:
        return None

    alert_user_id = cast(int | None, alert.user_id)
    alert_user = cast(User | None, alert.user)
    alert_id_value = cast(int, alert.id)
    alert_type = cast(str, alert.alert_type)
    severity = cast(str, alert.severity)
    risk_score = cast(int, alert.risk_score)
    explanation = cast(str, alert.explanation)
    recommended_action = cast(str, alert.recommended_action)
    status = cast(str, alert.status)

    timeline = get_user_timeline(db, alert_user_id) if alert_user_id else []
    customer_name = cast(str, alert_user.name) if alert_user else None
    trust_score = cast(int, alert_user.trust_score) if alert_user else None

    return {
        "incident_id": f"AEGIS-INC-{alert_id_value:05d}",
        "incident_type": alert_type,
        "severity": severity,
        "customer": customer_name,
        "risk_score": risk_score,
        "trust_score": trust_score,
        "timeline_summary": [
            f"{event['created_at'].isoformat()} - {event['event_type']}: {event['title']}"
            for event in timeline[-6:]
        ],
        "key_risk_indicators": [
            part.strip()
            for part in explanation.replace(".", "").split("detected")[-1].split(",")
            if part.strip()
        ][:6],
        "explanation": explanation,
        "recommended_action": recommended_action,
        "analyst_notes_placeholder": "Analyst notes can be added during investigation.",
        "status": status,
        "generated_at": datetime.utcnow(),
    }

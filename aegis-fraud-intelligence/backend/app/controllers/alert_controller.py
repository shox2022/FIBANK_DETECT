from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import FraudAlert, User
from app.services.analyst_note_service import create_status_change_note
from app.services.incident_report_engine import generate_incident_report


def list_alerts(db: Session):
    return db.query(FraudAlert).order_by(FraudAlert.created_at.desc()).all()


def get_alert(db: Session, alert_id: int):
    alert = db.get(FraudAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


def update_alert_status(db: Session, alert_id: int, payload, analyst_user: User):
    alert = get_alert(db, alert_id)
    old_status = alert.status
    alert.status = payload.status
    if old_status != payload.status:
        create_status_change_note(
            db,
            alert,
            analyst_user,
            old_status=old_status,
            new_status=payload.status,
            note=payload.note,
        )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def incident_report(db: Session, alert_id: int):
    report = generate_incident_report(db, alert_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return report

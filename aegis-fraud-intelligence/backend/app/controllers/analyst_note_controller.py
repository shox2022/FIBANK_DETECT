from sqlalchemy.orm import Session

from app.models import User
from app.schemas.analyst_note_schema import AnalystNoteCreate
from app.services import analyst_note_service


def list_notes(db: Session, alert_id: int):
    return analyst_note_service.get_alert_notes(db, alert_id)


def create_note(db: Session, alert_id: int, analyst_user: User, payload: AnalystNoteCreate):
    return analyst_note_service.add_analyst_note(
        db,
        alert_id,
        analyst_user,
        payload.note,
        payload.action_type,
    )


def decision_trail(db: Session, alert_id: int):
    return analyst_note_service.get_decision_trail(db, alert_id)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models import AnalystNote, FraudAlert, User


ALLOWED_ACTION_TYPES = {
    "NOTE",
    "STATUS_CHANGE",
    "ESCALATED",
    "MARKED_FRAUD",
    "MARKED_FALSE_POSITIVE",
    "CUSTOMER_CONTACTED",
    "REVIEW_COMPLETED",
}


def _note_payload(note: AnalystNote) -> dict:
    return {
        "id": note.id,
        "alert_id": note.alert_id,
        "analyst_user_id": note.analyst_user_id,
        "analyst_name": note.analyst.name if note.analyst else None,
        "note": note.note,
        "action_type": note.action_type,
        "old_status": note.old_status,
        "new_status": note.new_status,
        "created_at": note.created_at,
    }


def _get_alert_or_404(db: Session, alert_id: int) -> FraudAlert:
    alert = db.get(FraudAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


def add_analyst_note(
    db: Session,
    alert_id: int,
    analyst_user: User,
    note: str,
    action_type: str = "NOTE",
) -> dict:
    _get_alert_or_404(db, alert_id)
    normalized_action = (action_type or "NOTE").upper()
    if normalized_action not in ALLOWED_ACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported analyst note action type",
        )

    analyst_note = AnalystNote(
        alert_id=alert_id,
        analyst_user_id=analyst_user.id,
        note=note,
        action_type=normalized_action,
    )
    db.add(analyst_note)
    db.commit()
    db.refresh(analyst_note)
    return _note_payload(
        db.query(AnalystNote)
        .options(joinedload(AnalystNote.analyst))
        .filter(AnalystNote.id == analyst_note.id)
        .one()
    )


def get_alert_notes(db: Session, alert_id: int) -> list[dict]:
    _get_alert_or_404(db, alert_id)
    notes = (
        db.query(AnalystNote)
        .options(joinedload(AnalystNote.analyst))
        .filter(AnalystNote.alert_id == alert_id)
        .order_by(AnalystNote.created_at.desc())
        .all()
    )
    return [_note_payload(note) for note in notes]


def create_status_change_note(
    db: Session,
    alert: FraudAlert,
    analyst_user: User,
    old_status: str,
    new_status: str,
    note: str | None = None,
) -> AnalystNote:
    if new_status == "FALSE_POSITIVE":
        action_type = "MARKED_FALSE_POSITIVE"
    elif new_status == "RESOLVED":
        action_type = "REVIEW_COMPLETED"
    else:
        action_type = "STATUS_CHANGE"

    analyst_note = AnalystNote(
        alert_id=alert.id,
        analyst_user_id=analyst_user.id,
        note=note or f"Status changed from {old_status} to {new_status}",
        action_type=action_type,
        old_status=old_status,
        new_status=new_status,
    )
    db.add(analyst_note)
    return analyst_note


def get_decision_trail(db: Session, alert_id: int) -> list[dict]:
    _get_alert_or_404(db, alert_id)
    notes = (
        db.query(AnalystNote)
        .options(joinedload(AnalystNote.analyst))
        .filter(AnalystNote.alert_id == alert_id)
        .order_by(AnalystNote.created_at.asc())
        .all()
    )
    return [_note_payload(note) for note in notes]

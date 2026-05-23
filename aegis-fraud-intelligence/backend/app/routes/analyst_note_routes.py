from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import analyst_note_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User
from app.schemas.analyst_note_schema import AnalystNoteCreate


router = APIRouter()
ANALYST_ROLES = [ANALYST, ADMIN]


@router.get("/alerts/{alert_id}/notes")
def list_notes(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ANALYST_ROLES)),
):
    return jsonable_encoder(analyst_note_controller.list_notes(db, alert_id))


@router.post("/alerts/{alert_id}/notes")
def create_note(
    alert_id: int,
    payload: AnalystNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ANALYST_ROLES)),
):
    return jsonable_encoder(
        analyst_note_controller.create_note(db, alert_id, current_user, payload)
    )


@router.get("/alerts/{alert_id}/decision-trail")
def decision_trail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ANALYST_ROLES)),
):
    return jsonable_encoder(analyst_note_controller.decision_trail(db, alert_id))

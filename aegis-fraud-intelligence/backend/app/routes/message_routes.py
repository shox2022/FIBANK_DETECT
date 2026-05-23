from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import message_controller
from app.core.rbac import ADMIN, ANALYST, CUSTOMER, require_roles
from app.database import get_db
from app.models import User
from app.schemas.message_schema import MessageVerificationRequest


router = APIRouter()
MESSAGE_ROLES = [CUSTOMER, ANALYST, ADMIN]
SOC_ROLES = [ANALYST, ADMIN]


@router.get("/my")
def my_messages(
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(MESSAGE_ROLES)),
):
    return jsonable_encoder(message_controller.my_messages(db, current_user, user_id))


@router.post("/verify")
def verify_message(
    payload: MessageVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(MESSAGE_ROLES)),
):
    return jsonable_encoder(message_controller.verify_message(db, current_user, payload))


@router.get("/checks")
def message_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SOC_ROLES)),
):
    return jsonable_encoder(message_controller.message_checks(db))


@router.get("/all")
def all_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SOC_ROLES)),
):
    return jsonable_encoder(message_controller.all_messages(db))

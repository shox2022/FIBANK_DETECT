from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import ADMIN, ANALYST
from app.models import User
from app.services import message_service


def _target_user_id(current_user: User, requested_user_id: int | None) -> int | None:
    if current_user.role in {ANALYST, ADMIN}:
        return requested_user_id
    if requested_user_id is not None and requested_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers can only access their own messages",
        )
    return current_user.id


def my_messages(db: Session, current_user: User, user_id: int | None = None):
    return message_service.get_user_bank_messages(
        db,
        current_user,
        _target_user_id(current_user, user_id),
    )


def verify_message(db: Session, current_user: User, payload):
    return message_service.verify_message(
        db,
        current_user,
        payload.message_text,
        _target_user_id(current_user, payload.user_id),
    )


def message_checks(db: Session):
    return [message_service.serialize_check(check) for check in message_service.get_all_message_checks(db)]


def all_messages(db: Session):
    return message_service.get_all_bank_messages(db)

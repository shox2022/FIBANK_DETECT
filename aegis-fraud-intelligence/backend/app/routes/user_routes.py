from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import user_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User


router = APIRouter()


def _user_payload(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "home_country": user.home_country,
        "home_city": user.home_city,
        "trust_score": user.trust_score,
        "average_transaction_amount": user.average_transaction_amount,
        "account_number": user.account_number,
        "balance": user.balance,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder([_user_payload(user) for user in user_controller.list_users(db)])


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(_user_payload(user_controller.get_user(db, user_id)))


@router.get("/{user_id}/timeline")
def user_timeline(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(user_controller.user_timeline(db, user_id))


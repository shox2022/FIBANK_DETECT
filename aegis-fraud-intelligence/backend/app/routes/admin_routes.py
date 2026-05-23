from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import admin_controller
from app.core.rbac import ADMIN, require_roles
from app.database import get_db
from app.models import User
from app.routes.user_routes import _user_payload


router = APIRouter()


@router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ADMIN])),
):
    rules = admin_controller.list_rules(db)
    return jsonable_encoder(
        [
            {
                "id": rule.id,
                "code": rule.code,
                "description": rule.description,
                "points": rule.points,
                "enabled": rule.enabled,
            }
            for rule in rules
        ]
    )


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ADMIN])),
):
    return jsonable_encoder([_user_payload(user) for user in admin_controller.list_users(db)])


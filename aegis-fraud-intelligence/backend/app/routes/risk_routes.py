from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import risk_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User


router = APIRouter()
RISK_ROLES = [ANALYST, ADMIN]


@router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RISK_ROLES)),
):
    return jsonable_encoder(risk_controller.list_rules(db))


@router.get("/transparency")
def transparency(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RISK_ROLES)),
):
    return jsonable_encoder(risk_controller.transparency(db))

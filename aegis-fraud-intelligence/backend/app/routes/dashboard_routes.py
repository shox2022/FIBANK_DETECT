from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import dashboard_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User


router = APIRouter()


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(dashboard_controller.stats(db))


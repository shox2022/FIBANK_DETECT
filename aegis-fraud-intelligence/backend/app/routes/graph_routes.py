from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import graph_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User


router = APIRouter()


@router.get("/mule-network")
def mule_network(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(graph_controller.mule_network(db))


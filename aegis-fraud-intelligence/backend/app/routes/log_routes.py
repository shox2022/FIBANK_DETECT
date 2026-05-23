from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import log_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User


router = APIRouter()


@router.get("")
def list_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    logs = log_controller.list_logs(db)
    return jsonable_encoder(
        [
            {
                "id": log.id,
                "user_id": log.user_id,
                "event_type": log.event_type,
                "endpoint": log.endpoint,
                "ip_address": log.ip_address,
                "payload_sample": log.payload_sample,
                "risk_score": log.risk_score,
                "severity": log.severity,
                "created_at": log.created_at,
            }
            for log in logs
        ]
    )


from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import alert_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User
from app.schemas.alert_schema import AlertStatusUpdate


router = APIRouter()


def _alert_detail(alert):
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "risk_score": alert.risk_score,
        "title": alert.title,
        "explanation": alert.explanation,
        "recommended_action": alert.recommended_action,
        "status": alert.status,
        "created_at": alert.created_at,
        "customer_name": alert.user.name if alert.user else None,
        "trust_score": alert.user.trust_score if alert.user else None,
    }


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder([_alert_detail(alert) for alert in alert_controller.list_alerts(db)])


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(_alert_detail(alert_controller.get_alert(db, alert_id)))


@router.patch("/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(
        _alert_detail(alert_controller.update_alert_status(db, alert_id, payload))
    )


@router.get("/{alert_id}/incident-report")
def incident_report(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return jsonable_encoder(alert_controller.incident_report(db, alert_id))


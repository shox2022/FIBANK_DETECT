from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import simulate_controller
from app.core.rbac import ADMIN, ANALYST, CUSTOMER, require_roles
from app.database import get_db
from app.models import User
from app.schemas.simulation_schema import (
    SimulateLoginRequest,
    SimulateMuleRingRequest,
    SimulateSecurityLogRequest,
    SimulateTokenTheftRequest,
    SimulateTransactionRequest,
)


router = APIRouter()
SIMULATION_ROLES = [CUSTOMER, ANALYST, ADMIN]


def _alert_payload(alert):
    if alert is None:
        return None
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "risk_score": alert.risk_score,
        "title": alert.title,
        "status": alert.status,
        "created_at": alert.created_at,
    }


@router.post("/login")
def simulate_login(
    payload: SimulateLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SIMULATION_ROLES)),
):
    result = simulate_controller.simulate_login(payload, db, current_user)
    event = result["login_event"]
    return jsonable_encoder(
        {
            **result["risk"],
            "login_event": {
                "id": event.id,
                "user_id": event.user_id,
                "country": event.country,
                "city": event.city,
                "device_hash": event.device_hash,
                "risk_score": event.risk_score,
                "created_at": event.created_at,
            },
            "alert": _alert_payload(result.get("alert")),
        }
    )


@router.post("/transaction")
def simulate_transaction(
    payload: SimulateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SIMULATION_ROLES)),
):
    result = simulate_controller.simulate_transaction(payload, db, current_user)
    tx = result["transaction"]
    risk = result["risk"]
    return jsonable_encoder(
        {
            "risk_score": risk["risk_score"],
            "severity": risk["severity"],
            "reasons": risk["reasons"],
            "rule_score": risk["rule_score"],
            "ml_score": risk["ml_score"],
            "ml_model_version": risk["ml_model_version"],
            "ml_enabled": risk["ml_enabled"],
            "friction": result["friction"],
            "transaction": {
                "id": tx.id,
                "user_id": tx.user_id,
                "from_account": tx.from_account,
                "to_account": tx.to_account,
                "amount": tx.amount,
                "currency": tx.currency,
                "recipient_name": tx.recipient_name,
                "recipient_is_new": tx.recipient_is_new,
                "status": tx.status,
                "risk_score": tx.risk_score,
                "created_at": tx.created_at,
            },
            "alert": _alert_payload(result.get("alert")),
        }
    )


@router.post("/security-log")
def simulate_security_log(
    payload: SimulateSecurityLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SIMULATION_ROLES)),
):
    result = simulate_controller.simulate_security_log(payload, db, current_user)
    log = result["log"]
    return jsonable_encoder(
        {
            **result["risk"],
            "log": {
                "id": log.id,
                "user_id": log.user_id,
                "event_type": log.event_type,
                "endpoint": log.endpoint,
                "ip_address": log.ip_address,
                "payload_sample": log.payload_sample,
                "risk_score": log.risk_score,
                "severity": log.severity,
                "created_at": log.created_at,
            },
            "alert": _alert_payload(result.get("alert")),
        }
    )


@router.post("/token-theft")
def simulate_token_theft(
    payload: SimulateTokenTheftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SIMULATION_ROLES)),
):
    result = simulate_controller.simulate_token_theft(payload, db, current_user)
    session = result.get("session")
    return jsonable_encoder(
        {
            **result["risk"],
            "session": None
            if session is None
            else {
                "id": session.id,
                "user_id": session.user_id,
                "session_token_hash": session.session_token_hash,
                "is_active": session.is_active,
            },
            "alert": _alert_payload(result.get("alert")),
            "recommendation": result["recommendation"],
        }
    )


@router.post("/mule-ring")
def simulate_mule_ring(
    payload: SimulateMuleRingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SIMULATION_ROLES)),
):
    result = simulate_controller.simulate_mule_ring(payload, db)
    return jsonable_encoder(
        {
            "edges_created": len(result["edges"]),
            "alert": _alert_payload(result.get("alert")),
            "graph": result["graph"],
        }
    )


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.services import simulation_service


def simulate_login(payload, db: Session, current_user: User | None = None):
    try:
        return simulation_service.simulate_login(db, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def simulate_transaction(payload, db: Session, current_user: User | None = None):
    try:
        return simulation_service.simulate_transaction(db, payload, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def simulate_security_log(payload, db: Session, current_user: User | None = None):
    return simulation_service.simulate_security_log(db, payload, current_user)


def simulate_token_theft(payload, db: Session, current_user: User | None = None):
    return simulation_service.simulate_token_theft(db, payload, current_user)


def simulate_mule_ring(payload, db: Session):
    return simulation_service.simulate_mule_ring(db, payload)


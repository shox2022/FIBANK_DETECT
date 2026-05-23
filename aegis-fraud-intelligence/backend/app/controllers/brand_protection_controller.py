from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.services import brand_protection_service


def run_scan(db: Session, current_user: User, payload):
    try:
        return brand_protection_service.run_brand_scan(
            db,
            current_user,
            quick=payload.quick,
            max_candidates=payload.max_candidates,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def scan_runs(db: Session):
    return brand_protection_service.get_brand_scan_runs(db)


def scan_detail(db: Session, scan_id: int):
    try:
        return brand_protection_service.get_brand_scan_detail(db, scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def latest_scan(db: Session):
    latest = brand_protection_service.get_latest_brand_scan(db)
    if latest is None:
        return {"scan": None, "findings": []}
    return latest


def summary(db: Session):
    return brand_protection_service.get_brand_protection_summary(db)


def config():
    return brand_protection_service.get_brand_protection_config()

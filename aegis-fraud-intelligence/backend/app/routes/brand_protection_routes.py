from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.controllers import brand_protection_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.database import get_db
from app.models import User
from app.schemas.brand_protection_schema import BrandScanRequest


router = APIRouter()
BRAND_ROLES = [ANALYST, ADMIN]


@router.post("/scan")
def run_scan(
    payload: BrandScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(BRAND_ROLES)),
):
    return jsonable_encoder(brand_protection_controller.run_scan(db, current_user, payload))


@router.get("/runs")
def scan_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(BRAND_ROLES)),
):
    return jsonable_encoder(brand_protection_controller.scan_runs(db))


@router.get("/runs/{scan_id}")
def scan_detail(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(BRAND_ROLES)),
):
    return jsonable_encoder(brand_protection_controller.scan_detail(db, scan_id))


@router.get("/latest")
def latest_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(BRAND_ROLES)),
):
    return jsonable_encoder(brand_protection_controller.latest_scan(db))


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(BRAND_ROLES)),
):
    return jsonable_encoder(brand_protection_controller.summary(db))


@router.get("/config")
def config(current_user: User = Depends(require_roles(BRAND_ROLES))):
    return brand_protection_controller.config()

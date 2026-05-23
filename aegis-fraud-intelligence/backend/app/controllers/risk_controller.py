from sqlalchemy.orm import Session

from app.services import risk_transparency_service


def list_rules(db: Session):
    return risk_transparency_service.list_risk_rules(db)


def transparency(db: Session):
    return risk_transparency_service.get_risk_transparency(db)

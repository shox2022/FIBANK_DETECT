from sqlalchemy.orm import Session

from app.models import RiskRule, User


def list_rules(db: Session):
    return db.query(RiskRule).order_by(RiskRule.code.asc()).all()


def list_users(db: Session):
    return db.query(User).order_by(User.id.asc()).all()


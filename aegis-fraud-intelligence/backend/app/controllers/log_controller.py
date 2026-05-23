from sqlalchemy.orm import Session

from app.models import SecurityLog


def list_logs(db: Session):
    return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).all()


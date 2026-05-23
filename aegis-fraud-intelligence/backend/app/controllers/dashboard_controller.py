from sqlalchemy.orm import Session

from app.services.dashboard_service import get_dashboard_stats


def stats(db: Session):
    return get_dashboard_stats(db)


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.services.timeline_engine import get_user_timeline


def list_users(db: Session):
    return db.query(User).order_by(User.id.asc()).all()


def get_user(db: Session, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def user_timeline(db: Session, user_id: int):
    get_user(db, user_id)
    return get_user_timeline(db, user_id)


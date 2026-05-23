from typing import cast

from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models import User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None

    password_hash = cast(str, user.password_hash)
    if not verify_password(password, password_hash):
        return None

    return user


def create_login_response(user: User) -> dict:
    access_token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

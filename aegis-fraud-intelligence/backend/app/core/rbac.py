from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import User


CUSTOMER = "CUSTOMER"
ANALYST = "ANALYST"
ADMIN = "ADMIN"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception()

    subject = payload.get("sub")
    if subject is None:
        raise _credentials_exception()

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise _credentials_exception() from None

    user = db.get(User, user_id)
    if user is None:
        raise _credentials_exception()

    return user


def require_roles(allowed_roles: list[str]) -> Callable[[User], User]:
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user

    return role_dependency


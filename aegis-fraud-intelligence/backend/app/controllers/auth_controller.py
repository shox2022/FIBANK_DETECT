from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.auth_schema import CurrentUserResponse, LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_login_response


def login(payload: LoginRequest, db: Session) -> TokenResponse:
    return login_with_credentials(payload.email, payload.password, db)


def login_with_credentials(email: str, password: str, db: Session) -> TokenResponse:
    user = authenticate_user(db, email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**create_login_response(user))


def me(current_user: User) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


def analyst_rbac_test(current_user: User) -> dict:
    return {
        "status": "ok",
        "message": "RBAC check passed for analyst/admin access",
        "user_id": current_user.id,
        "role": current_user.role,
    }

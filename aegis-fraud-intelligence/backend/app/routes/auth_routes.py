from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.controllers import auth_controller
from app.core.rbac import ADMIN, ANALYST, get_current_user, require_roles
from app.database import get_db
from app.models import User
from app.schemas.auth_schema import CurrentUserResponse, LoginRequest, TokenResponse


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return auth_controller.login_with_credentials(
            email=str(form.get("username", "")),
            password=str(form.get("password", "")),
            db=db,
        )

    payload = LoginRequest.model_validate(await request.json())
    return auth_controller.login(payload, db)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)):
    return auth_controller.me(current_user)


@router.get("/rbac-test/analyst")
def analyst_rbac_test(
    current_user: User = Depends(require_roles([ANALYST, ADMIN])),
):
    return auth_controller.analyst_rbac_test(current_user)

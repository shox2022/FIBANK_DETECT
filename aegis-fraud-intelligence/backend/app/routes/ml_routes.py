from fastapi import APIRouter, Depends

from app.controllers import ml_controller
from app.core.rbac import ADMIN, ANALYST, require_roles
from app.models import User
from app.schemas.ml_schema import FraudScoreBatchRequest, FraudScoreRequest

router = APIRouter()
ML_ROLES = [ANALYST, ADMIN]


@router.get("/health")
def model_health(current_user: User = Depends(require_roles(ML_ROLES))):
    return ml_controller.model_health()


@router.post("/score")
def score_transaction(
    payload: FraudScoreRequest,
    current_user: User = Depends(require_roles(ML_ROLES)),
):
    return ml_controller.score_transaction(payload)


@router.post("/score-batch")
def score_batch(
    payload: FraudScoreBatchRequest,
    current_user: User = Depends(require_roles(ML_ROLES)),
):
    return ml_controller.score_batch(payload)


@router.get("/features")
def feature_catalogue(current_user: User = Depends(require_roles(ML_ROLES))):
    return ml_controller.feature_catalogue()

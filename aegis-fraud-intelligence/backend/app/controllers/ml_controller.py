from fastapi import HTTPException, status

from app.services.ml_score_engine import (
    MLModelUnavailableError,
    get_feature_names,
    get_ml_batch_scores,
    get_ml_transaction_score,
    get_model_health,
)


def model_health() -> dict:
    try:
        return get_model_health()
    except MLModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def score_transaction(payload) -> dict:
    try:
        return get_ml_transaction_score(payload.transaction)
    except MLModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def score_batch(payload) -> dict:
    try:
        return get_ml_batch_scores(payload.transactions)
    except MLModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def feature_catalogue() -> dict:
    features = get_feature_names()
    return {"feature_names": features, "feature_count": len(features)}

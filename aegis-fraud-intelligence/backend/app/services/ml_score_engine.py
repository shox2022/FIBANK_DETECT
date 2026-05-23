def get_ml_transaction_score(
    transaction_data: dict,
    user_context: dict | None = None,
) -> dict:
    """Return a deterministic placeholder for future transaction ML scoring.

    The real XGBoost integration will load the trained model artifact here,
    transform transaction_data/user_context into the model feature vector, and
    return the model suspicion score alongside explainability metadata.
    """
    return {
        "ml_score": 0,
        "model_version": "xgboost-placeholder-v0",
        "enabled": False,
        "features_used": [],
        "explanation": (
            "ML scoring placeholder. XGBoost model will be integrated in a later phase."
        ),
    }


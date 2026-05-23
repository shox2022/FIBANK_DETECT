from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_VERSION = "fibank-xgboost-v1"
UNAVAILABLE_VERSION = "xgboost-unavailable"

FEATURE_NAMES = [
    "amount", "amount_log", "amount_ratio", "amount_vs_balance",
    "is_tiny_probe", "is_large_spike",
    "tx_hour", "tx_dow", "is_night", "is_weekend", "user_age_days",
    "recipient_is_new", "beneficiary_tx_count",
    "trust_score", "average_transaction_amount", "balance",
    "user_tx_count_24h",
    "login_failed_attempts_total", "login_vpn_count", "login_proxy_count",
    "login_risk_score_mean", "login_success_rate", "login_country_nunique",
    "device_count", "trusted_device_count", "os_nunique",
    "browser_nunique", "untrusted_device_ratio",
    "session_country_mismatch",
    "seclog_count", "seclog_risk_mean",
    "seclog_critical_count", "seclog_high_count",
    "trust_delta_mean", "trust_change_count",
    "status_blocked", "status_held", "status_2fa",
    "currency_foreign",
    "home_country_enc", "session_country_enc", "role_enc",
]

_detector: Any | None = None
_detector_error: str | None = None
_detector_loaded = False


class MLModelUnavailableError(RuntimeError):
    """Raised when ML scoring is required but the model is unavailable."""


def _safe_error(exc: BaseException | str | None) -> str | None:
    if exc is None:
        return None
    text = str(exc).strip().replace("\n", " ")
    return text[:500]


def _unavailable_response(error: str | None = None) -> dict:
    response = {
        "ml_score": 0,
        "ml_probability": 0,
        "ml_flag": 0,
        "ml_risk_band": "DISABLED",
        "model_version": UNAVAILABLE_VERSION,
        "enabled": False,
        "features_used": [],
        "missing_features": [],
        "explanation": "XGBoost ML scoring is disabled or unavailable. Rule-based scoring is being used.",
    }
    if error:
        response["error"] = error
    return response


def get_feature_names() -> list[str]:
    return list(FEATURE_NAMES)


def get_detector():
    global _detector, _detector_error, _detector_loaded

    if not settings.fraud_ml_enabled:
        logger.info("ML disabled by configuration")
        return None

    if _detector is not None:
        return _detector

    if _detector_loaded and _detector_error and settings.fraud_ml_fail_open:
        logger.info("ML fallback active", extra={"error_type": "cached_model_error"})
        return None

    try:
        from app.ml.fraud_detector import FraudDetector

        model_path = settings.resolved_fraud_model_path
        _detector = FraudDetector(model_path=str(model_path))
        _detector_error = None
        _detector_loaded = True
        logger.info("Fraud model loaded", extra={"model_status": "loaded", "feature_count": len(FEATURE_NAMES)})
        return _detector
    except Exception as exc:  # noqa: BLE001 - normalize all load failures for fail-open mode.
        _detector = None
        _detector_error = _safe_error(exc)
        _detector_loaded = True
        logger.warning("Fraud model load failure", extra={"error_type": type(exc).__name__})
        if settings.fraud_ml_fail_open:
            return None
        raise MLModelUnavailableError(_detector_error or "Fraud model unavailable") from exc


def _model_input(transaction_data: dict, user_context: dict | None = None) -> dict:
    merged = dict(user_context or {})
    merged.update(transaction_data or {})
    return merged


def _explain(result: dict, features_used: list[str]) -> str:
    probability = float(result.get("fraud_probability", 0) or 0)
    band = result.get("fraud_risk_band", "UNKNOWN")
    missing = result.get("missing_features", []) or []
    highlighted = ", ".join(features_used[:6]) if features_used else "the supplied transaction signals"
    suffix = ""
    if missing:
        suffix = f" {len(missing)} model features were not supplied and defaulted to 0."
    return (
        f"The XGBoost model classified this transaction as {band} risk with a fraud "
        f"probability of {probability * 100:.1f}%. Key supplied signals include {highlighted}." + suffix
    )


def get_ml_transaction_score(transaction_data: dict, user_context: dict | None = None) -> dict:
    detector = get_detector()
    if detector is None:
        return _unavailable_response(_detector_error)

    model_input = _model_input(transaction_data, user_context)
    features_used = [key for key in FEATURE_NAMES if key in model_input]
    logger.info("Fraud score request", extra={"feature_count": len(features_used), "model_status": "loaded"})

    try:
        result = detector.score(model_input)
    except Exception as exc:  # noqa: BLE001
        error = _safe_error(exc)
        logger.exception("Fraud scoring failure", extra={"error_type": type(exc).__name__})
        if settings.fraud_ml_fail_open:
            return _unavailable_response(error)
        raise MLModelUnavailableError(error or "Fraud scoring failed") from exc

    logger.info("Fraud score complete", extra={"risk_band": result.get("fraud_risk_band")})
    return {
        "ml_score": float(result.get("fraud_percentage", 0) or 0),
        "ml_probability": float(result.get("fraud_probability", 0) or 0),
        "ml_flag": int(result.get("fraud_flag", 0) or 0),
        "ml_risk_band": result.get("fraud_risk_band", "UNKNOWN"),
        "model_version": MODEL_VERSION,
        "enabled": True,
        "features_used": features_used,
        "missing_features": result.get("missing_features", []) or [],
        "explanation": _explain(result, features_used),
    }


def get_ml_batch_scores(transactions: list[dict]) -> dict:
    detector = get_detector()
    if detector is None:
        return {"enabled": False, "model_version": UNAVAILABLE_VERSION, "results": [_unavailable_response(_detector_error) for _ in transactions]}

    logger.info("Fraud score batch request", extra={"batch_size": len(transactions)})
    try:
        raw_results = detector.score_batch(transactions)
    except Exception as exc:  # noqa: BLE001
        error = _safe_error(exc)
        logger.exception("Fraud batch scoring failure", extra={"error_type": type(exc).__name__})
        if settings.fraud_ml_fail_open:
            return {"enabled": False, "model_version": UNAVAILABLE_VERSION, "results": [_unavailable_response(error) for _ in transactions]}
        raise MLModelUnavailableError(error or "Fraud batch scoring failed") from exc

    normalized = []
    for tx, result in zip(transactions, raw_results, strict=False):
        features_used = [key for key in FEATURE_NAMES if key in tx]
        normalized.append(
            {
                "ml_score": float(result.get("fraud_percentage", 0) or 0),
                "ml_probability": float(result.get("fraud_probability", 0) or 0),
                "ml_flag": int(result.get("fraud_flag", 0) or 0),
                "ml_risk_band": result.get("fraud_risk_band", "UNKNOWN"),
                "model_version": MODEL_VERSION,
                "enabled": True,
                "features_used": features_used,
                "missing_features": result.get("missing_features", []) or [],
                "explanation": _explain(result, features_used),
            }
        )
    return {"enabled": True, "model_version": MODEL_VERSION, "results": normalized}


def get_model_health() -> dict:
    detector = None
    error = None
    try:
        detector = get_detector()
    except MLModelUnavailableError as exc:
        error = _safe_error(exc)
        if not settings.fraud_ml_fail_open:
            raise

    if error is None:
        error = _detector_error

    return {
        "enabled": bool(settings.fraud_ml_enabled and detector is not None),
        "model_loaded": detector is not None,
        "model_path": str(settings.resolved_fraud_model_path),
        "model_version": MODEL_VERSION if detector is not None else UNAVAILABLE_VERSION,
        "feature_count": len(FEATURE_NAMES),
        "threshold": getattr(detector, "threshold", 0.35) if detector is not None else 0.35,
        "error": error,
    }


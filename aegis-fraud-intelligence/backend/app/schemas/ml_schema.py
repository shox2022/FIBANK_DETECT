from typing import Any

from pydantic import BaseModel, Field, field_validator

AllowedValue = int | float | bool | str | None


def _validate_transaction_dict(value: dict[str, Any]) -> dict[str, AllowedValue]:
    if not isinstance(value, dict) or not value:
        raise ValueError("transaction must be a non-empty object")
    cleaned: dict[str, AllowedValue] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("transaction feature names must be non-empty strings")
        if not isinstance(item, (int, float, bool, str)) and item is not None:
            raise ValueError("transaction values must be int, float, bool, string, or null")
        cleaned[key] = item
    return cleaned


class FraudScoreRequest(BaseModel):
    transaction: dict[str, Any]
    include_explanation: bool = True

    @field_validator("transaction")
    @classmethod
    def validate_transaction(cls, value: dict[str, Any]) -> dict[str, AllowedValue]:
        return _validate_transaction_dict(value)


class FraudScoreBatchRequest(BaseModel):
    transactions: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    include_explanation: bool = True

    @field_validator("transactions")
    @classmethod
    def validate_transactions(cls, value: list[dict[str, Any]]) -> list[dict[str, AllowedValue]]:
        return [_validate_transaction_dict(item) for item in value]


class FraudScoreResponse(BaseModel):
    ml_score: float
    ml_probability: float
    ml_flag: int
    ml_risk_band: str
    model_version: str
    enabled: bool
    features_used: list[str]
    missing_features: list[str]
    explanation: str
    error: str | None = None


class FraudScoreBatchResponse(BaseModel):
    enabled: bool
    model_version: str
    results: list[dict[str, Any]]


class FraudHealthResponse(BaseModel):
    enabled: bool
    model_loaded: bool
    model_path: str
    model_version: str
    feature_count: int
    threshold: float
    error: str | None = None


class FraudFeaturesResponse(BaseModel):
    feature_names: list[str]
    feature_count: int

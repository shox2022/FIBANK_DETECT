"""
fraud_detector.py
-----------------
Import this file anywhere in the application to score transactions.
The model file (fibank_fraud_model.ubj) must exist in the outputs/ subfolder
next to this file unless an explicit model_path is passed.
"""

import os

import pandas as pd
import xgboost as xgb

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODEL_DIR = os.path.join(_HERE, "outputs")
_MODEL_FILE = os.path.join(_MODEL_DIR, "fibank_fraud_model.ubj")

FRAUD_THRESHOLD = 0.35

FEATURE_COLS = [
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


class FraudDetector:
    """Loads the trained XGBoost model and scores transactions."""

    def __init__(self, model_path: str = _MODEL_FILE):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"\n\n  Model file not found at: {model_path}"
                f"\n  Train the model first by running:"
                f"\n      python fibank_fraud_model.py --retrain"
                f"\n  The model will be saved to: outputs/fibank_fraud_model.ubj"
            )
        self._model = xgb.XGBClassifier()
        self._model.load_model(model_path)

    def score(self, transaction: dict) -> dict:
        """Score a single transaction and return its fraud probability."""
        row, missing = self._build_row(transaction)
        X = pd.DataFrame([row])[FEATURE_COLS]
        prob = float(self._model.predict_proba(X)[0, 1])

        return {
            "fraud_probability": round(prob, 4),
            "fraud_percentage": round(prob * 100, 2),
            "fraud_flag": int(prob >= FRAUD_THRESHOLD),
            "fraud_risk_band": self._band(prob),
            "missing_features": missing,
        }

    def score_batch(self, transactions: list) -> list:
        """Score multiple transactions at once."""
        rows = []
        missing = []
        for tx in transactions:
            row, m = self._build_row(tx)
            rows.append(row)
            missing.append(m)

        X = pd.DataFrame(rows)[FEATURE_COLS]
        probs = self._model.predict_proba(X)[:, 1]

        return [
            {
                "fraud_probability": round(float(p), 4),
                "fraud_percentage": round(float(p) * 100, 2),
                "fraud_flag": int(p >= FRAUD_THRESHOLD),
                "fraud_risk_band": self._band(float(p)),
                "missing_features": missing[i],
            }
            for i, p in enumerate(probs)
        ]

    def _build_row(self, transaction: dict):
        """Fill in missing features with 0 and track which were absent."""
        row = {col: 0 for col in FEATURE_COLS}
        missing = []
        for col in FEATURE_COLS:
            if col in transaction:
                row[col] = transaction[col]
            else:
                missing.append(col)
        return row, missing

    @staticmethod
    def _band(prob: float) -> str:
        if prob < 0.15:
            return "LOW"
        if prob < 0.35:
            return "MEDIUM"
        if prob < 0.65:
            return "HIGH"
        return "CRITICAL"

    @property
    def threshold(self) -> float:
        """The probability cut-off used by fraud_flag."""
        return FRAUD_THRESHOLD

    @property
    def feature_names(self) -> list:
        """Ordered list of feature column names expected by the model."""
        return FEATURE_COLS

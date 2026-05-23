"""
fraud_detector.py
-----------------
Import this file anywhere in the application to score transactions.
The model file (fibank_fraud_model.ubj) must exist in the outputs/ subfolder
next to fibank_fraud_model.py. Run the training script once to produce it:

    python fibank_fraud_model.py --retrain

USAGE IN ANOTHER FILE
---------------------
    from fraud_detector import FraudDetector

    detector = FraudDetector()

    result = detector.score({
        "amount"          : 5000.0,
        "recipient_is_new": 1,
        "login_vpn_count" : 2,
        "trust_score"     : 30.0,
    })

    print(result["fraud_probability"])   # 0.0 – 1.0  (e.g. 0.87)
    print(result["fraud_percentage"])    # 0 – 100    (e.g. 87.3)
    print(result["fraud_flag"])          # 1 = fraud, 0 = legitimate
    print(result["fraud_risk_band"])     # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
"""

import os
import xgboost as xgb
import pandas as pd

# ── Resolve the model path regardless of where this file is imported from ────
_HERE = os.path.dirname(os.path.abspath(__file__))
_MODEL_DIR = os.path.join(_HERE, "outputs")
_MODEL_FILE = os.path.join(_MODEL_DIR, "fibank_fraud_model.ubj")

# ── Fraud threshold ───────────────────────────────────────────────────────────
FRAUD_THRESHOLD = 0.35  # probability above which fraud_flag = 1

# ── Feature columns (must match training order exactly) ───────────────────────
FEATURE_COLS = [
    # Amount
    "amount", "amount_log", "amount_ratio", "amount_vs_balance",
    "is_tiny_probe", "is_large_spike",
    # Time
    "tx_hour", "tx_dow", "is_night", "is_weekend", "user_age_days",
    # Recipient
    "recipient_is_new", "beneficiary_tx_count",
    # User financial
    "trust_score", "average_transaction_amount", "balance",
    # Velocity
    "user_tx_count_24h",
    # Login signals
    "login_failed_attempts_total", "login_vpn_count", "login_proxy_count",
    "login_risk_score_mean", "login_success_rate", "login_country_nunique",
    # Device
    "device_count", "trusted_device_count", "os_nunique",
    "browser_nunique", "untrusted_device_ratio",
    # Location
    "session_country_mismatch",
    # Security logs
    "seclog_count", "seclog_risk_mean",
    "seclog_critical_count", "seclog_high_count",
    # Trust dynamics
    "trust_delta_mean", "trust_change_count",
    # Transaction status / currency
    "status_blocked", "status_held", "status_2fa",
    "currency_foreign",
    # Encoded categoricals
    "home_country_enc", "session_country_enc", "role_enc",
]


class FraudDetector:
    """
    Loads the trained XGBoost model and scores transactions.

    Parameters
    ----------
    model_path : str, optional
        Absolute or relative path to fibank_fraud_model.ubj.
        Defaults to outputs/fibank_fraud_model.ubj next to this file.
        Pass a custom path if your project layout differs:

            FraudDetector(r"C:\\myapp\\models\\fibank_fraud_model.ubj")
    """

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

    # ── Core scoring ──────────────────────────────────────────────────────────

    def score(self, transaction: dict) -> dict:
        """
        Score a single transaction and return its fraud probability.

        Parameters
        ----------
        transaction : dict
            Supply any of the keys listed in FEATURE_COLS.
            Any key you omit defaults to 0 — the more you supply, the more
            accurate the prediction. See FEATURE_COLS for the full list.

        Returns
        -------
        dict
            fraud_probability  float (0.0 – 1.0)
                Raw model output. 0 = certainly legitimate, 1 = certainly fraud.

            fraud_percentage   float (0.0 – 100.0)
                Same value as a percentage. Easier to display in a UI.
                e.g. 0.87 -> 87.3

            fraud_flag         int (0 or 1)
                1 if fraud_probability >= FRAUD_THRESHOLD (default 0.35), else 0.

            fraud_risk_band    str
                Human-readable risk tier:
                  "LOW"      probability < 0.15
                  "MEDIUM"   0.15 <= probability < 0.35
                  "HIGH"     0.35 <= probability < 0.65
                  "CRITICAL" probability >= 0.65

            missing_features   list[str]
                Feature keys that were not supplied and defaulted to 0.
                Fewer missing features = more reliable prediction.
        """
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
        """
        Score multiple transactions at once.

        Parameters
        ----------
        transactions : list of dict
            Each dict is the same format as score().

        Returns
        -------
        list of dict — same structure as score(), one entry per input transaction.
        """
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

    # ── Helpers ───────────────────────────────────────────────────────────────

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
        elif prob < 0.35:
            return "MEDIUM"
        elif prob < 0.65:
            return "HIGH"
        else:
            return "CRITICAL"

    @property
    def threshold(self) -> float:
        """The probability cut-off used by fraud_flag (default 0.35)."""
        return FRAUD_THRESHOLD

    @property
    def feature_names(self) -> list:
        """Ordered list of feature column names expected by the model."""
        return FEATURE_COLS

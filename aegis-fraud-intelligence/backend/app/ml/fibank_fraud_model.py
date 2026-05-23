"""
fibank Fraud Detection runtime compatibility module.

The original training script should remain the source of truth for retraining.
For AEGIS runtime integration, this module preserves the importable inference
API by re-exporting FraudDetector, FEATURE_COLS, and FRAUD_THRESHOLD.
"""

try:
    from .fraud_detector import FEATURE_COLS, FRAUD_THRESHOLD, FraudDetector
except ImportError:  # Allows `python fibank_fraud_model.py` from this folder.
    from fraud_detector import FEATURE_COLS, FRAUD_THRESHOLD, FraudDetector


__all__ = ["FEATURE_COLS", "FRAUD_THRESHOLD", "FraudDetector"]

from app.database import SessionLocal
from app.models import LoginEvent, User
from app.seed import run_seed
from app.services.ml_score_engine import get_ml_batch_scores, get_ml_transaction_score, get_model_health
from app.services.risk_engine import calculate_transaction_risk


def check(label: str, condition: bool, details: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        raise AssertionError(label)


def has_fields(data: dict, fields: set[str]) -> bool:
    return fields.issubset(set(data.keys()))


def main():
    run_seed()
    db = SessionLocal()
    try:
        health = get_model_health()
        print("Model health:", health)
        if not health.get("model_loaded"):
            print("ML model unavailable, rule-based fallback active.")

        required = {
            "ml_score",
            "ml_probability",
            "ml_flag",
            "ml_risk_band",
            "model_version",
            "enabled",
            "missing_features",
        }

        suspicious = {
            "amount": 15000.0,
            "recipient_is_new": 1,
            "login_vpn_count": 3,
            "trust_score": 25.0,
            "amount_ratio": 12.0,
            "is_large_spike": 1,
        }
        normal = {
            "amount": 120.0,
            "recipient_is_new": 0,
            "login_vpn_count": 0,
            "trust_score": 88.0,
            "amount_ratio": 0.9,
        }

        suspicious_result = get_ml_transaction_score(suspicious)
        normal_result = get_ml_transaction_score(normal)
        batch_result = get_ml_batch_scores([suspicious, normal, {"amount": 5000.0}])

        check("suspicious score returns normalized ML fields", has_fields(suspicious_result, required), str(suspicious_result))
        check("normal score returns normalized ML fields", has_fields(normal_result, required), str(normal_result))
        check("batch score returns results", "results" in batch_result and len(batch_result["results"]) == 3, str(batch_result))

        user = db.query(User).filter(User.email == "customer@aegis.test").first()
        check("seeded customer exists", user is not None)
        latest_login = (
            db.query(LoginEvent)
            .filter(LoginEvent.user_id == user.id)
            .order_by(LoginEvent.created_at.desc())
            .first()
        )
        risk = calculate_transaction_risk(
            {
                "to_account": "AL472091000000009999",
                "amount": 2500.0,
                "currency": "EUR",
                "recipient_is_new": True,
            },
            user,
            latest_login,
            db=db,
        )
        risk_fields = {
            "risk_score",
            "rule_score",
            "ml_score",
            "ml_probability",
            "ml_flag",
            "ml_risk_band",
            "ml_model_version",
            "ml_enabled",
            "ml_missing_features",
            "ml_explanation",
        }
        check("transaction risk output includes ML fields", risk_fields.issubset(set(risk.keys())), str(risk))
        print("\nML smoke complete: all checks passed")
    finally:
        db.close()


if __name__ == "__main__":
    main()

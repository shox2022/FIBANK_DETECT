from app.database import SessionLocal
from app.models import MessageVerificationCheck, User
from app.seed import run_seed
from app.services.message_service import get_user_bank_messages, verify_message


def check(label: str, condition: bool, details: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        raise AssertionError(label)


def main():
    run_seed()
    db = SessionLocal()
    try:
        customer = db.query(User).filter(User.email == "customer@aegis.test").first()
        check("main customer exists", customer is not None)

        messages = get_user_bank_messages(db, customer)
        check("seeded official bank messages exist", len(messages) >= 4, str(len(messages)))

        official_text = messages[0].body
        official_result = verify_message(db, customer, official_text)
        check(
            "official message verifies",
            official_result["result"] == "VERIFIED_OFFICIAL",
            str(official_result),
        )

        phishing_text = (
            "URGENT: Your Fibank account has been blocked. Click "
            "http://fake-fibank-login.example to verify your password and OTP immediately."
        )
        phishing_result = verify_message(db, customer, phishing_text)
        check(
            "phishing sample is detected",
            phishing_result["result"] == "POSSIBLE_PHISHING",
            str(phishing_result),
        )

        suspicious_text = (
            "Final warning. Your account will be suspended unless you confirm your card number today."
        )
        suspicious_result = verify_message(db, customer, suspicious_text)
        check(
            "suspicious sample is suspicious or phishing",
            suspicious_result["result"] in {"SUSPICIOUS", "POSSIBLE_PHISHING"},
            str(suspicious_result),
        )

        check_count = db.query(MessageVerificationCheck).filter(
            MessageVerificationCheck.user_id == customer.id
        ).count()
        check("verification checks were stored", check_count >= 3, str(check_count))

        print("\nMessage verification smoke complete: all checks passed")
    finally:
        db.close()


if __name__ == "__main__":
    main()

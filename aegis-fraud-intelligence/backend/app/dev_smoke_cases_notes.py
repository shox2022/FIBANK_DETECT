from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import FraudAlert
from app.seed import run_seed


client = TestClient(app)


def check(label: str, condition: bool, details: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        raise AssertionError(label)


def login(email: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    check(f"login {email}", response.status_code == 200, response.text)
    return response.json()["access_token"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def find_case_alert_id() -> int:
    db = SessionLocal()
    try:
        alert = (
            db.query(FraudAlert)
            .filter(FraudAlert.severity.in_(["HIGH", "CRITICAL"]))
            .order_by(FraudAlert.created_at.desc())
            .first()
        )
        check("seeded HIGH/CRITICAL alert exists", alert is not None)
        return int(alert.id)
    finally:
        db.close()


def main():
    run_seed()
    alert_id = find_case_alert_id()
    customer = login("customer@aegis.test")
    analyst = login("analyst@aegis.test")
    admin = login("admin@aegis.test")

    alert_response = client.get(f"/api/alerts/{alert_id}", headers=headers(analyst))
    check("alert detail available to analyst", alert_response.status_code == 200, alert_response.text)
    alert = alert_response.json()
    check("HIGH/CRITICAL alert treated as case", alert["is_case"] is True, str(alert))
    check("case priority returned", alert["case_priority"] in {"P1", "P2"}, str(alert))

    forbidden = client.get(f"/api/alerts/{alert_id}/notes", headers=headers(customer))
    check("CUSTOMER receives 403 for notes", forbidden.status_code == 403, forbidden.text)

    note_response = client.post(
        f"/api/alerts/{alert_id}/notes",
        headers=headers(analyst),
        json={
            "note": "Customer transaction reviewed. New beneficiary and VPN login confirmed.",
            "action_type": "NOTE",
        },
    )
    check("ANALYST can add analyst note", note_response.status_code == 200, note_response.text)

    status_response = client.patch(
        f"/api/alerts/{alert_id}/status",
        headers=headers(analyst),
        json={
            "status": "INVESTIGATING",
            "note": "Reviewing customer login and transaction timeline.",
        },
    )
    check("ANALYST can change alert status with note", status_response.status_code == 200, status_response.text)

    notes_response = client.get(f"/api/alerts/{alert_id}/notes", headers=headers(admin))
    check("ADMIN can read notes", notes_response.status_code == 200, notes_response.text)
    notes = notes_response.json()
    check("notes include explicit NOTE", any(note["action_type"] == "NOTE" for note in notes), str(notes))

    trail_response = client.get(f"/api/alerts/{alert_id}/decision-trail", headers=headers(analyst))
    check("ANALYST can read decision trail", trail_response.status_code == 200, trail_response.text)
    trail = trail_response.json()
    check(
        "decision trail contains status decision",
        any(item["action_type"] in {"STATUS_CHANGE", "REVIEW_COMPLETED", "MARKED_FALSE_POSITIVE"} for item in trail),
        str(trail),
    )

    rules_response = client.get("/api/risk/rules", headers=headers(analyst))
    check("ANALYST can access risk rules", rules_response.status_code == 200, rules_response.text)
    check("risk rules include categories", "category" in rules_response.json()[0], rules_response.text)

    transparency_response = client.get("/api/risk/transparency", headers=headers(analyst))
    check("ANALYST can access risk transparency", transparency_response.status_code == 200, transparency_response.text)
    transparency = transparency_response.json()
    check(
        "transparency returns core sections",
        {"risk_levels", "adaptive_friction", "trust_score_impacts", "ml_integration", "rules"}.issubset(transparency.keys()),
        str(transparency),
    )

    customer_transparency = client.get("/api/risk/transparency", headers=headers(customer))
    check("CUSTOMER receives 403 for risk transparency", customer_transparency.status_code == 403, customer_transparency.text)

    print("\nCases, notes, and risk transparency smoke complete: all checks passed")


if __name__ == "__main__":
    main()

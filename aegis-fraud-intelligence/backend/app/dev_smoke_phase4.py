from fastapi.testclient import TestClient

from app.main import app
from app.seed import run_seed


client = TestClient(app)


def check(label: str, condition: bool, details: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        raise AssertionError(label)


def login(email: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    check(f"login {email}", response.status_code == 200, response.text)
    data = response.json()
    check(
        f"login {email} returns token",
        "access_token" in data and data["token_type"] == "bearer",
    )
    return data


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_with_role(path: str, token: str):
    return client.get(path, headers=auth_headers(token))


def post_with_role(path: str, token: str, payload: dict):
    return client.post(path, json=payload, headers=auth_headers(token))


def main():
    run_seed()

    customer = login("customer@aegis.test")
    analyst = login("analyst@aegis.test")
    admin = login("admin@aegis.test")

    tokens = {
        "CUSTOMER": customer["access_token"],
        "ANALYST": analyst["access_token"],
        "ADMIN": admin["access_token"],
    }

    for role, token in tokens.items():
        response = get_with_role("/api/auth/me", token)
        body = response.json()
        check(
            f"/api/auth/me works for {role}",
            response.status_code == 200 and body["role"] == role,
            response.text,
        )

    login_payload = {
        "device_hash": "phase4_customer_device",
        "device_label": "Phase 4 test device",
        "browser": "Chrome",
        "os": "Windows",
        "ip_address": "185.53.12.99",
        "country": "Albania",
        "city": "Tirana",
        "is_vpn": False,
        "is_proxy": False,
        "success": True,
        "failed_attempts": 0,
    }
    response = post_with_role("/api/simulate/login", tokens["CUSTOMER"], login_payload)
    check(
        "CUSTOMER can call /api/simulate/login",
        response.status_code == 200 and "risk_score" in response.json(),
        response.text,
    )

    tx_payload = {
        "to_account": "AL472091000000009999",
        "amount": 2500,
        "currency": "EUR",
        "recipient_name": "Phase 4 Beneficiary",
        "recipient_is_new": True,
    }
    response = post_with_role(
        "/api/simulate/transaction",
        tokens["CUSTOMER"],
        tx_payload,
    )
    tx_body = response.json()
    required_tx_fields = {
        "risk_score",
        "severity",
        "reasons",
        "friction",
        "rule_score",
        "ml_score",
        "ml_model_version",
        "ml_enabled",
    }
    check(
        "CUSTOMER can call /api/simulate/transaction",
        response.status_code == 200,
        response.text,
    )
    check(
        "/api/simulate/transaction returns risk, friction, status, and ML fields",
        required_tx_fields.issubset(set(tx_body.keys()))
        and "transaction" in tx_body
        and "status" in tx_body["transaction"],
        str(tx_body),
    )

    customer_forbidden = [
        "/api/dashboard/stats",
        "/api/alerts",
        "/api/graph/mule-network",
        "/api/logs",
        "/api/admin/users",
    ]
    for path in customer_forbidden:
        response = get_with_role(path, tokens["CUSTOMER"])
        check(f"CUSTOMER receives 403 for {path}", response.status_code == 403, response.text)

    response = get_with_role("/api/messages/my", tokens["CUSTOMER"])
    check(
        "CUSTOMER can call /api/messages/my",
        response.status_code == 200 and isinstance(response.json(), list),
        response.text,
    )
    verify_response = post_with_role(
        "/api/messages/verify",
        tokens["CUSTOMER"],
        {"message_text": "URGENT: Your Fibank account has been blocked. Click http://fake-fibank-login.example to verify your password and OTP immediately."},
    )
    check(
        "CUSTOMER can call /api/messages/verify",
        verify_response.status_code == 200 and verify_response.json()["result"] == "POSSIBLE_PHISHING",
        verify_response.text,
    )
    response = get_with_role("/api/messages/checks", tokens["CUSTOMER"])
    check("CUSTOMER receives 403 for /api/messages/checks", response.status_code == 403, response.text)

    analyst_allowed = [
        "/api/dashboard/stats",
        "/api/alerts",
        "/api/graph/mule-network",
        "/api/logs",
        "/api/users",
        "/api/messages/checks",
    ]
    for path in analyst_allowed:
        response = get_with_role(path, tokens["ANALYST"])
        check(f"ANALYST can access {path}", response.status_code == 200, response.text)

    analyst_forbidden = ["/api/admin/users", "/api/admin/rules"]
    for path in analyst_forbidden:
        response = get_with_role(path, tokens["ANALYST"])
        check(f"ANALYST receives 403 for {path}", response.status_code == 403, response.text)

    admin_allowed = ["/api/admin/users", "/api/admin/rules", "/api/messages/all"]
    for path in admin_allowed:
        response = get_with_role(path, tokens["ADMIN"])
        check(f"ADMIN can access {path}", response.status_code == 200, response.text)

    alerts_response = get_with_role("/api/alerts", tokens["ANALYST"])
    alerts = alerts_response.json()
    check("existing alert available for incident report", bool(alerts), alerts_response.text)
    alert_id = alerts[0]["id"]
    report_response = get_with_role(
        f"/api/alerts/{alert_id}/incident-report",
        tokens["ANALYST"],
    )
    report = report_response.json()
    check(
        "/api/alerts/{alert_id}/incident-report works",
        report_response.status_code == 200
        and {"incident_id", "incident_type", "severity", "recommended_action"}.issubset(
            set(report.keys())
        ),
        report_response.text,
    )


    fraud_customer_response = get_with_role("/api/fraud/health", tokens["CUSTOMER"])
    check("CUSTOMER receives 403 for /api/fraud/health", fraud_customer_response.status_code == 403, fraud_customer_response.text)

    for role in ["ANALYST", "ADMIN"]:
        health_response = get_with_role("/api/fraud/health", tokens[role])
        check(f"{role} can access /api/fraud/health", health_response.status_code == 200, health_response.text)
        health_body = health_response.json()
        check("/api/fraud/health returns model status", {"enabled", "model_loaded", "model_version", "feature_count"}.issubset(set(health_body.keys())), str(health_body))

        score_response = post_with_role(
            "/api/fraud/score",
            tokens[role],
            {"transaction": {"amount": 5000.0, "recipient_is_new": 1, "login_vpn_count": 2, "trust_score": 30.0}},
        )
        score_body = score_response.json()
        check(f"{role} can call /api/fraud/score", score_response.status_code == 200, score_response.text)
        check("/api/fraud/score returns ML or controlled fallback", {"ml_score", "ml_probability", "ml_flag", "ml_risk_band", "enabled"}.issubset(set(score_body.keys())), str(score_body))

    print("\nPhase 4 API smoke complete: all checks passed")


if __name__ == "__main__":
    main()



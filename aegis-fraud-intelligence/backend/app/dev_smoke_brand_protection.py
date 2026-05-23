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


def login(email: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    check(f"login {email}", response.status_code == 200, response.text)
    return response.json()["access_token"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    run_seed()
    customer = login("customer@aegis.test")
    analyst = login("analyst@aegis.test")
    admin = login("admin@aegis.test")

    response = client.get("/api/brand-protection/summary", headers=headers(customer))
    check("CUSTOMER receives 403 for brand summary", response.status_code == 403, response.text)

    for role, token in {"ANALYST": analyst, "ADMIN": admin}.items():
        response = client.get("/api/brand-protection/summary", headers=headers(token))
        check(f"{role} can access brand summary", response.status_code == 200, response.text)
        body = response.json()
        check(
            "summary returns expected fields",
            {"high_count", "medium_count", "low_count", "total_findings", "top_risky_domains"}.issubset(body.keys()),
            str(body),
        )

    scan_response = client.post(
        "/api/brand-protection/scan",
        headers=headers(analyst),
        json={"quick": True, "max_candidates": 20},
    )
    check("ANALYST can run tiny quick scan", scan_response.status_code == 200, scan_response.text)
    scan = scan_response.json()
    check(
        "scan response contains run fields",
        {"id", "status", "total_candidates", "live_domains_count", "findings"}.issubset(scan.keys()),
        str(scan),
    )

    detail_response = client.get(
        f"/api/brand-protection/runs/{scan['id']}",
        headers=headers(admin),
    )
    check("ADMIN can fetch scan detail", detail_response.status_code == 200, detail_response.text)

    print("\nBrand protection smoke complete: all checks passed")


if __name__ == "__main__":
    main()

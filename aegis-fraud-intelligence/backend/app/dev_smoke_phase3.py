from typing import cast

from pydantic import BaseModel

from app.database import SessionLocal
from app.models import FraudAlert, Session as UserSession, User
from app.schemas.simulation_schema import (
    SimulateMuleRingRequest,
    SimulateSecurityLogRequest,
    SimulateTokenTheftRequest,
    SimulateTransactionRequest,
)
from app.services.dashboard_service import get_dashboard_stats
from app.services.incident_report_engine import generate_incident_report
from app.services.log_engine import create_security_log
from app.services.mule_engine import get_mule_graph
from app.services.risk_engine import calculate_login_risk, calculate_transaction_risk
from app.services.simulation_service import simulate_mule_ring, simulate_transaction
from app.services.token_engine import detect_token_theft


class LoginRiskInput(BaseModel):
    device_hash: str
    ip_address: str
    country: str
    city: str
    is_vpn: bool = False
    is_proxy: bool = False
    failed_attempts: int = 0


def check(label: str, condition: bool, details: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    return condition


def required_report_fields_present(report: dict):
    required = {
        "incident_id",
        "incident_type",
        "severity",
        "customer",
        "risk_score",
        "trust_score",
        "timeline_summary",
        "key_risk_indicators",
        "explanation",
        "recommended_action",
        "analyst_notes_placeholder",
        "status",
        "generated_at",
    }
    return required.issubset(set(report.keys()))


def main():
    db = SessionLocal()
    passed = 0
    failed = 0

    try:
        customer = db.query(User).filter(User.email == "customer@aegis.test").first()
        if customer is None:
            raise RuntimeError("Seeded customer not found. Run: python -m app.seed")

        customer_id = cast(int, customer.id)
        previous_login = customer.login_events[-1] if customer.login_events else None

        normal_login = LoginRiskInput(
            device_hash="dev_hash_ardit_trusted_laptop",
            ip_address="185.53.12.12",
            country="Albania",
            city="Tirana",
        )
        normal_risk = calculate_login_risk(normal_login, customer, previous_login)
        passed += check(
            "normal login risk should be LOW",
            normal_risk["severity"] == "LOW",
            str(normal_risk),
        )

        germany_vpn = LoginRiskInput(
            device_hash="dev_hash_phase3_unknown_germany",
            ip_address="93.184.216.34",
            country="Germany",
            city="Berlin",
            is_vpn=True,
            failed_attempts=3,
        )
        germany_risk = calculate_login_risk(germany_vpn, customer, previous_login)
        passed += check(
            "VPN Germany login after Albania history should be HIGH or CRITICAL",
            germany_risk["severity"] in {"HIGH", "CRITICAL"},
            str(germany_risk),
        )

        tx_input = SimulateTransactionRequest(
            user_id=customer_id,
            to_account="AL472091000000009999",
            amount=2500,
            currency="EUR",
            recipient_name="New Beneficiary",
            recipient_is_new=True,
        )
        tx_risk = calculate_transaction_risk(tx_input, customer, previous_login, db=db)
        ml_fields = {"rule_score", "ml_score", "ml_model_version", "ml_enabled"}
        passed += check(
            "high-value new-beneficiary transaction should be HIGH or CRITICAL",
            tx_risk["severity"] in {"HIGH", "CRITICAL"},
            str(tx_risk),
        )
        passed += check(
            "transaction risk output includes ML placeholder fields",
            ml_fields.issubset(set(tx_risk.keys())),
            str({key: tx_risk.get(key) for key in ml_fields}),
        )

        simulated_tx = simulate_transaction(db, tx_input, customer)
        transaction_id = cast(int | None, simulated_tx["transaction"].id)
        passed += check(
            "transaction service creates transaction record",
            transaction_id is not None,
            f"id={transaction_id}",
        )

        sql_input = SimulateSecurityLogRequest(
            user_id=customer_id,
            event_type="SQL_INJECTION_ATTEMPT",
            endpoint="/api/auth/login",
            ip_address="91.220.33.44",
            payload_sample="' OR '1'='1 --",
        )
        sql_result = create_security_log(db, sql_input, customer)
        passed += check(
            "SQL injection payload should be CRITICAL",
            sql_result["risk"]["severity"] == "CRITICAL",
            str(sql_result["risk"]),
        )

        session_token_hash = "phase3_smoke_token_hash"
        existing_session = (
            db.query(UserSession)
            .filter(UserSession.session_token_hash == session_token_hash)
            .first()
        )
        if existing_session is None:
            existing_session = UserSession(
                user_id=customer_id,
                session_token_hash=session_token_hash,
                device_hash="dev_hash_ardit_trusted_laptop",
                ip_address="185.53.12.12",
                country="Albania",
                city="Tirana",
                is_active=True,
            )
            db.add(existing_session)
            db.commit()
            db.refresh(existing_session)
        else:
            existing_session.is_active = True
            db.commit()

        token_input = SimulateTokenTheftRequest(
            user_id=customer_id,
            session_token_hash=session_token_hash,
            original_ip_address="185.53.12.12",
            new_ip_address="203.0.113.77",
            original_country="Albania",
            new_country="Germany",
            original_device_hash="dev_hash_ardit_trusted_laptop",
            new_device_hash="dev_hash_unknown_attacker",
            is_vpn=True,
        )
        token_result = detect_token_theft(db, token_input, customer)
        token_alert = token_result["alert"]
        token_session = token_result["session"]
        token_alert_severity = cast(str | None, token_alert.severity) if token_alert else None
        token_session_active = (
            cast(bool | None, token_session.is_active) if token_session else None
        )
        passed += check(
            "token theft should create a CRITICAL alert and invalidate the session",
            token_alert is not None
            and token_alert_severity == "CRITICAL"
            and token_session is not None
            and token_session_active is False,
            f"alert={getattr(token_alert, 'id', None)}, active={token_session_active}",
        )

        simulate_mule_ring(
            db,
            SimulateMuleRingRequest(
                mule_account="AL472091000000009998",
                amount=450,
            ),
        )
        graph = get_mule_graph(db)
        passed += check(
            "mule graph should return nodes and edges",
            bool(graph["nodes"]) and bool(graph["edges"]),
            f"nodes={len(graph['nodes'])}, edges={len(graph['edges'])}",
        )

        dashboard = get_dashboard_stats(db)
        dashboard_fields = {
            "total_alerts",
            "critical_alerts",
            "blocked_transactions",
            "average_trust_score",
            "suspicious_log_count",
            "mule_accounts_count",
            "recent_alerts",
            "recent_transactions",
        }
        passed += check(
            "dashboard service should return aggregate stats",
            dashboard_fields.issubset(set(dashboard.keys())),
            str({key: dashboard[key] for key in sorted(dashboard_fields)}),
        )

        latest_alert = db.query(FraudAlert).order_by(FraudAlert.id.desc()).first()
        if latest_alert is None:
            raise RuntimeError("No alert found for incident report smoke check")
        latest_alert_id = cast(int, latest_alert.id)
        report = generate_incident_report(db, latest_alert_id)
        passed += check(
            "incident report should return required report fields",
            report is not None and required_report_fields_present(report),
            str(report),
        )

        failed = 10 - passed
        print(f"\nPhase 3 smoke complete: {passed} passed, {failed} failed")
        if failed:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

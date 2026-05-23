from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy.orm import Session as OrmSession

from app.models import Device, LoginEvent, SecurityLog, Session as AegisSession, Transaction, TrustScoreHistory, User

COUNTRY_ENCODING = {
    "UNKNOWN": 0,
    "AL": 1,
    "Albania": 1,
    "DE": 2,
    "Germany": 2,
    "IT": 3,
    "Italy": 3,
    "FR": 4,
    "France": 4,
    "GB": 5,
    "United Kingdom": 5,
    "US": 6,
    "United States": 6,
    "TR": 7,
    "Turkey": 7,
    "MK": 8,
    "North Macedonia": 8,
    "GR": 9,
    "Greece": 9,
    "RS": 10,
    "Serbia": 10,
}

ROLE_ENCODING = {"CUSTOMER": 0, "ANALYST": 1, "ADMIN": 2}


def _value(input_data: Any, field: str, default=None):
    if isinstance(input_data, dict):
        return input_data.get(field, default)
    return getattr(input_data, field, default)


def _country_enc(country: str | None) -> int:
    return COUNTRY_ENCODING.get(country or "UNKNOWN", 0)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_transaction_features(
    db: OrmSession,
    user: User,
    transaction_data: dict | Any,
    latest_login: LoginEvent | None = None,
) -> dict:
    """Build the XGBoost feature dict from AEGIS transaction context.

    The production version should reuse the original training encoders or saved
    metadata for categorical encoding consistency. For this prototype we use
    stable placeholder mappings for country and role fields.
    """
    now = datetime.utcnow()
    tx_time = cast(datetime | None, _value(transaction_data, "created_at", None)) or now
    amount = float(_value(transaction_data, "amount", 0) or 0)
    to_account = str(_value(transaction_data, "to_account", "") or "")
    currency = str(_value(transaction_data, "currency", "EUR") or "EUR")
    status = str(_value(transaction_data, "status", "") or "")
    avg_amount = float(cast(float, user.average_transaction_amount) or 0)
    balance = float(cast(float, user.balance) or 0)
    trust_score = float(cast(int, user.trust_score) or 0)
    user_id = cast(int, user.id)

    login_events = db.query(LoginEvent).filter(LoginEvent.user_id == user_id).all()
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    security_logs = db.query(SecurityLog).filter(SecurityLog.user_id == user_id).all()
    trust_history = (
        db.query(TrustScoreHistory)
        .filter(TrustScoreHistory.user_id == user_id)
        .order_by(TrustScoreHistory.created_at.asc())
        .all()
    )
    latest_session = (
        db.query(AegisSession)
        .filter(AegisSession.user_id == user_id)
        .order_by(AegisSession.created_at.desc())
        .first()
    )

    prior_beneficiary_count = 0
    if to_account:
        prior_beneficiary_count = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.to_account == to_account)
            .count()
        )

    user_tx_count_24h = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= tx_time - timedelta(hours=24),
        )
        .count()
    )

    login_risks = [float(cast(int, event.risk_score) or 0) / 100 for event in login_events]
    security_risks = [float(cast(int, log.risk_score) or 0) / 100 for log in security_logs]
    trust_deltas = [
        float(cast(int, item.new_score) - cast(int, item.old_score))
        for item in trust_history
    ]

    device_count = len(devices)
    trusted_device_count = sum(1 for device in devices if bool(cast(bool, device.is_trusted)))
    latest_country = (
        cast(str | None, latest_session.country)
        if latest_session is not None
        else cast(str | None, latest_login.country) if latest_login is not None else None
    )

    amount_ratio = amount / avg_amount if avg_amount > 0 else 0.0
    amount_vs_balance = amount / balance if balance > 0 else 0.0
    user_created_at = cast(datetime | None, user.created_at) or tx_time
    user_age_days = max(0, (tx_time - user_created_at).days)

    return {
        "amount": amount,
        "amount_log": math.log1p(max(amount, 0)),
        "amount_ratio": amount_ratio,
        "amount_vs_balance": amount_vs_balance,
        "is_tiny_probe": int(amount < 2.0),
        "is_large_spike": int(amount_ratio > 5),
        "tx_hour": tx_time.hour,
        "tx_dow": tx_time.weekday(),
        "is_night": int(tx_time.hour >= 23 or tx_time.hour <= 5),
        "is_weekend": int(tx_time.weekday() >= 5),
        "user_age_days": user_age_days,
        "recipient_is_new": int(bool(_value(transaction_data, "recipient_is_new", False))),
        "beneficiary_tx_count": prior_beneficiary_count,
        "trust_score": trust_score,
        "average_transaction_amount": avg_amount,
        "balance": balance,
        "user_tx_count_24h": user_tx_count_24h,
        "login_failed_attempts_total": sum(int(cast(int, event.failed_attempts) or 0) for event in login_events),
        "login_vpn_count": sum(1 for event in login_events if bool(cast(bool, event.is_vpn))),
        "login_proxy_count": sum(1 for event in login_events if bool(cast(bool, event.is_proxy))),
        "login_risk_score_mean": _mean(login_risks),
        "login_success_rate": _mean([1.0 if bool(cast(bool, event.success)) else 0.0 for event in login_events]),
        "login_country_nunique": len({cast(str | None, event.country) for event in login_events if cast(str | None, event.country)}),
        "device_count": device_count,
        "trusted_device_count": trusted_device_count,
        "os_nunique": len({cast(str | None, device.os) for device in devices if cast(str | None, device.os)}),
        "browser_nunique": len({cast(str | None, device.browser) for device in devices if cast(str | None, device.browser)}),
        "untrusted_device_ratio": 1 - (trusted_device_count / device_count) if device_count else 0.0,
        "session_country_mismatch": int(bool(latest_country and cast(str | None, user.home_country) and latest_country != cast(str | None, user.home_country))),
        "seclog_count": len(security_logs),
        "seclog_risk_mean": _mean(security_risks),
        "seclog_critical_count": sum(1 for log in security_logs if cast(str | None, log.severity) == "CRITICAL"),
        "seclog_high_count": sum(1 for log in security_logs if cast(str | None, log.severity) == "HIGH"),
        "trust_delta_mean": _mean(trust_deltas),
        "trust_change_count": len(trust_history),
        "status_blocked": int(status == "BLOCKED"),
        "status_held": int(status == "HELD"),
        "status_2fa": int(status == "REQUIRE_2FA"),
        "currency_foreign": int(currency != "ALL"),
        "home_country_enc": _country_enc(cast(str | None, user.home_country)),
        "session_country_enc": _country_enc(latest_country),
        "role_enc": ROLE_ENCODING.get(cast(str, user.role), 0),
    }

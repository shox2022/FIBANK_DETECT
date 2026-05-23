from typing import cast

from sqlalchemy.orm import Session

from app.models import TrustScoreHistory, User


DECREASES = {
    "New device": -8,
    "VPN": -10,
    "Proxy": -8,
    "Impossible travel": -25,
    "Token theft": -30,
    "SQL injection": -20,
    "High-risk transaction": -20,
    "Mule connection": -25,
}

INCREASES = {
    "Trusted device normal login": 3,
    "Normal transaction": 2,
    "Successful verification simulation": 5,
}


def _delta_for_reason(reason: str) -> int:
    delta = 0
    lower_reason = reason.lower()
    for key, value in DECREASES.items():
        if key.lower() in lower_reason:
            delta += value
    for key, value in INCREASES.items():
        if key.lower() in lower_reason:
            delta += value
    return delta


def update_trust_score(db: Session, user: User, reasons: list[str], event_type: str):
    old_score = cast(int, user.trust_score)
    user_id = cast(int, user.id)
    delta = sum(_delta_for_reason(reason) for reason in reasons)

    if delta == 0:
        if event_type == "normal_login":
            delta = 3
        elif event_type == "normal_transaction":
            delta = 2
        elif event_type in {"high_risk_transaction", "security_log"}:
            delta = -10

    new_score = max(0, min(100, old_score + delta))
    if new_score == old_score:
        return user

    user.trust_score = new_score
    db.add(
        TrustScoreHistory(
            user_id=user_id,
            old_score=old_score,
            new_score=new_score,
            reason=f"{event_type}: {', '.join(reasons)}",
        )
    )
    db.add(user)
    return user

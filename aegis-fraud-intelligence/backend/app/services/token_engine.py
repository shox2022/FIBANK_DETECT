from typing import cast

from sqlalchemy.orm import Session

from app.models import FraudAlert, Session as UserSession, User
from app.services.explanation_engine import generate_explanation
from app.services.risk_engine import calculate_token_theft_risk
from app.services.trust_engine import update_trust_score


def detect_token_theft(db: Session, input_data, user: User | None = None):
    risk = calculate_token_theft_risk(input_data)
    token_hash = cast(str | None, getattr(input_data, "session_token_hash", None))
    user_id = cast(int, user.id) if user else None
    input_user_id = cast(int | None, getattr(input_data, "user_id", None))
    session = None

    if token_hash:
        query = db.query(UserSession).filter(UserSession.session_token_hash == token_hash)
        if user_id is not None:
            query = query.filter(UserSession.user_id == user_id)
        session = query.first()
        if session and risk["risk_score"] >= 61:
            session.is_active = False
            db.add(session)

    alert = None
    if risk["risk_score"] >= 61:
        explanation = generate_explanation(
            "TOKEN_THEFT",
            risk["risk_score"],
            risk["severity"],
            risk["reasons"],
        )
        alert = FraudAlert(
            user_id=user_id if user_id is not None else input_user_id,
            alert_type="TOKEN_THEFT",
            severity="CRITICAL" if risk["risk_score"] >= 81 else risk["severity"],
            risk_score=risk["risk_score"],
            title="Possible token theft detected",
            explanation=explanation["summary"],
            recommended_action="Invalidate session and require secure re-authentication.",
            status="OPEN",
        )
        db.add(alert)
        if user:
            update_trust_score(db, user, ["Token theft", *risk["reasons"]], "token_theft")

    db.commit()
    if session:
        db.refresh(session)
    if alert:
        db.refresh(alert)

    return {
        "risk": risk,
        "session": session,
        "alert": alert,
        "recommendation": "Require re-authentication" if alert else "Continue monitoring",
    }

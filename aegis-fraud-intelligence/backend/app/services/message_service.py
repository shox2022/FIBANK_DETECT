from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from typing import cast

from sqlalchemy.orm import Session

from app.models import BankMessage, MessageVerificationCheck, User

logger = logging.getLogger(__name__)

OFFICIAL_DOMAIN_HINTS = ["aegis.bank", "fibank.al", "bank.local"]
SENSITIVE_TERMS = [
    "password",
    "pin",
    "card number",
    "cvv",
    "otp",
    "one-time password",
    "seed phrase",
    "security code",
]
URGENCY_TERMS = [
    "urgent",
    "immediately",
    "verify now",
    "click here",
    "final warning",
    "limited time",
]
BLOCKED_TERMS = ["account blocked", "account suspended", "account will be suspended"]
AUTH_OUTSIDE_APP_TERMS = [
    "click http",
    "login link",
    "confirm your card",
    "confirm your account",
    "verify your password",
]
SUSPICIOUS_WORDING_TERMS = [
    "dear customer your account",
    "kindly verify",
    "failure to comply",
    "avoid permanent closure",
]


def normalize_message_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _safe_reasons(reasons: list[str]) -> str:
    return json.dumps(reasons, ensure_ascii=True)


def _message_response(message: BankMessage | None):
    if message is None:
        return None
    return {
        "id": message.id,
        "user_id": message.user_id,
        "channel": message.channel,
        "title": message.title,
        "body": message.body,
        "message_type": message.message_type,
        "official": message.official,
        "risk_level": message.risk_level,
        "related_alert_id": message.related_alert_id,
        "created_at": message.created_at,
    }


def _check_response(check: MessageVerificationCheck):
    try:
        reasons = json.loads(cast(str, check.reasons))
    except json.JSONDecodeError:
        reasons = [cast(str, check.reasons)]
    return {
        "id": check.id,
        "user_id": check.user_id,
        "submitted_text": check.submitted_text,
        "matched_message_id": check.matched_message_id,
        "result": check.result,
        "risk_score": check.risk_score,
        "reasons": reasons,
        "recommendation": check.recommendation,
        "created_at": check.created_at,
    }


def create_bank_message(
    db: Session,
    user_id: int | None,
    channel: str,
    title: str,
    body: str,
    message_type: str,
    risk_level: str = "LOW",
    related_alert_id: int | None = None,
):
    try:
        message = BankMessage(
            user_id=user_id,
            channel=channel,
            title=title,
            body=body,
            message_type=message_type,
            official=True,
            risk_level=risk_level,
            related_alert_id=related_alert_id,
        )
        db.add(message)
        db.flush()
        return message
    except Exception:  # noqa: BLE001 - bank message generation must never break fraud flow.
        logger.exception("Bank message creation failed")
        return None


def get_user_bank_messages(db: Session, user: User, user_id: int | None = None):
    target_user_id = user_id if user_id is not None else cast(int, user.id)
    return (
        db.query(BankMessage)
        .filter(BankMessage.official.is_(True), BankMessage.user_id == target_user_id)
        .order_by(BankMessage.created_at.desc())
        .all()
    )


def get_all_bank_messages(db: Session):
    return db.query(BankMessage).order_by(BankMessage.created_at.desc()).limit(200).all()


def get_all_message_checks(db: Session):
    return (
        db.query(MessageVerificationCheck)
        .order_by(MessageVerificationCheck.created_at.desc())
        .limit(100)
        .all()
    )


def find_official_match(db: Session, user_id: int, submitted_text: str):
    normalized = normalize_message_text(submitted_text)
    messages = (
        db.query(BankMessage)
        .filter(BankMessage.official.is_(True), BankMessage.user_id == user_id)
        .all()
    )
    best_match = None
    best_score = 0.0
    for message in messages:
        official_text = normalize_message_text(f"{message.title} {message.body}")
        body_text = normalize_message_text(cast(str, message.body))
        title_text = normalize_message_text(cast(str, message.title))
        if normalized in {official_text, body_text, title_text}:
            return message, 1.0
        ratio = max(
            SequenceMatcher(None, normalized, official_text).ratio(),
            SequenceMatcher(None, normalized, body_text).ratio(),
        )
        if ratio > best_score:
            best_score = ratio
            best_match = message
    if best_score >= 0.86:
        return best_match, best_score
    return None, best_score


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)>\"]+|(?:bit\.ly|tinyurl\.com)/[^\s)>\"]+", text, flags=re.IGNORECASE)


def _has_non_bank_domain(urls: list[str]) -> bool:
    for url in urls:
        lowered = url.lower()
        if not any(domain in lowered for domain in OFFICIAL_DOMAIN_HINTS):
            return True
    return False


def evaluate_phishing_indicators(normalized_text: str) -> tuple[int, list[str]]:
    score = 25
    reasons = ["Message was not found in your official bank messages."]

    urls = _extract_urls(normalized_text)
    if urls:
        score += 30
        reasons.append("Contains an external link.")

    if urls and _has_non_bank_domain(urls):
        score += 25
        reasons.append("Contains a non-bank or unrecognized domain.")

    if any(term in normalized_text for term in SENSITIVE_TERMS):
        score += 40
        reasons.append("Asks for sensitive information such as password, PIN, card, CVV, OTP, or security code.")

    if any(term in normalized_text for term in URGENCY_TERMS):
        score += 20
        reasons.append("Uses urgent language to pressure immediate action.")

    if any(term in normalized_text for term in BLOCKED_TERMS):
        score += 20
        reasons.append("Mentions account blocked or suspended wording.")

    if any(term in normalized_text for term in AUTH_OUTSIDE_APP_TERMS):
        score += 20
        reasons.append("Asks you to authenticate or confirm details outside the banking app.")

    if any(term in normalized_text for term in SUSPICIOUS_WORDING_TERMS):
        score += 10
        reasons.append("Uses wording that is unusual for official bank communication.")

    return min(100, score), reasons


def _result_for_score(score: int) -> str:
    if score <= 20:
        return "UNKNOWN"
    if score <= 50:
        return "SUSPICIOUS"
    return "POSSIBLE_PHISHING"


def _recommendation(result: str) -> str:
    if result == "VERIFIED_OFFICIAL":
        return "This message matches an official message in your banking app. For safety, perform any action only inside the app."
    if result == "POSSIBLE_PHISHING":
        return "This message does not match official bank communication and contains phishing indicators. Do not click links, do not share credentials, and contact the bank through official channels."
    if result == "SUSPICIOUS":
        return "This message has suspicious signs. Do not click links. Verify inside the banking app or contact support."
    return "This message was not found in your official message inbox, but strong phishing indicators were not detected. Treat it cautiously."


def verify_message(db: Session, user: User, message_text: str, user_id: int | None = None):
    target_user_id = user_id if user_id is not None else cast(int, user.id)
    matched_message, _score = find_official_match(db, target_user_id, message_text)
    checked_at = None

    if matched_message is not None:
        result = "VERIFIED_OFFICIAL"
        risk_score = 0
        reasons = ["Message matches an official bank message in the AEGIS inbox."]
        recommendation = _recommendation(result)
    else:
        normalized = normalize_message_text(message_text)
        risk_score, reasons = evaluate_phishing_indicators(normalized)
        result = _result_for_score(risk_score)
        recommendation = _recommendation(result)

    check = MessageVerificationCheck(
        user_id=target_user_id,
        submitted_text=message_text,
        matched_message_id=matched_message.id if matched_message is not None else None,
        result=result,
        risk_score=risk_score,
        reasons=_safe_reasons(reasons),
        recommendation=recommendation,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    checked_at = check.created_at

    return {
        "result": result,
        "risk_score": risk_score,
        "matched_message": _message_response(matched_message),
        "reasons": reasons,
        "recommendation": recommendation,
        "checked_at": checked_at,
    }


def serialize_check(check: MessageVerificationCheck):
    return _check_response(check)

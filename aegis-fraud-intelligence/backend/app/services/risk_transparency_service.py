from sqlalchemy.orm import Session

from app.models import RiskRule


def derive_rule_category(rule: RiskRule) -> str:
    code = rule.code.upper()
    text = f"{rule.code} {rule.description}".upper()
    if code.startswith("ML") or "XGBOOST" in text:
        return "ML"
    if code.startswith("TX") or code.startswith("MULE"):
        return "TRANSACTION"
    if code.startswith("LOGIN"):
        return "LOGIN"
    if code.startswith("LOG_"):
        return "SECURITY_LOG"
    if code.startswith("TOKEN"):
        return "TOKEN"
    if code.startswith("TRUST"):
        return "TRUST"
    if "LOGIN" in text:
        return "LOGIN"
    if "TRANSACTION" in text or "TRANSFER" in text:
        return "TRANSACTION"
    if "TOKEN" in text:
        return "TOKEN"
    if "SQL" in text or "ENDPOINT" in text:
        return "SECURITY_LOG"
    if "TRUST" in text:
        return "TRUST"
    if "FRICTION" in text or "2FA" in text:
        return "FRICTION"
    return "OTHER"


def rule_payload(rule: RiskRule) -> dict:
    return {
        "id": rule.id,
        "code": rule.code,
        "description": rule.description,
        "points": rule.points,
        "enabled": rule.enabled,
        "category": derive_rule_category(rule),
    }


def list_risk_rules(db: Session) -> list[dict]:
    rules = db.query(RiskRule).order_by(RiskRule.code.asc()).all()
    return [rule_payload(rule) for rule in rules]


def get_risk_transparency(db: Session) -> dict:
    return {
        "risk_levels": [
            {"range": "0-30", "severity": "LOW", "action": "Allow"},
            {"range": "31-60", "severity": "MEDIUM", "action": "Require 2FA"},
            {"range": "61-80", "severity": "HIGH", "action": "Hold for review"},
            {"range": "81-100", "severity": "CRITICAL", "action": "Block and alert"},
        ],
        "adaptive_friction": [
            {
                "risk": "LOW",
                "action": "ALLOW",
                "description": "Low-risk activity proceeds without extra friction.",
            },
            {
                "risk": "MEDIUM",
                "action": "REQUIRE_2FA",
                "description": "Medium-risk events trigger step-up authentication.",
            },
            {
                "risk": "HIGH",
                "action": "HOLD_FOR_REVIEW",
                "description": "High-risk activity is held for analyst review.",
            },
            {
                "risk": "CRITICAL",
                "action": "BLOCK_AND_ALERT",
                "description": "Critical events are blocked and escalated immediately.",
            },
        ],
        "trust_score_impacts": [
            "New device decreases trust.",
            "VPN or proxy usage decreases trust.",
            "Impossible travel causes a major trust decrease.",
            "Token theft and SQL injection indicators cause severe trust decreases.",
            "Normal trusted behavior can gradually increase trust.",
            "Low trust can escalate adaptive friction even for medium-risk events.",
        ],
        "ml_integration": {
            "description": "Rule-based score is combined with XGBoost ML score when enabled.",
            "combination": "final_score = rule_score * 0.65 + ml_score * 0.35",
            "fallback": "If ML is unavailable, rule-based scoring remains active.",
        },
        "rules": list_risk_rules(db),
    }

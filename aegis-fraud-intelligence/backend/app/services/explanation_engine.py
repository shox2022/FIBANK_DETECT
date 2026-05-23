def generate_explanation(
    alert_type: str,
    risk_score: int,
    severity: str,
    reasons: list[str],
) -> dict:
    reason_text = ", ".join(reason.lower() for reason in reasons) if reasons else "risk signals"
    summary = (
        f"This {alert_type.replace('_', ' ').lower()} was classified as {severity} "
        f"with a risk score of {risk_score} because AEGIS detected {reason_text}."
    )

    if severity == "CRITICAL":
        recommended_action = "Block the activity, protect the account, and begin immediate investigation."
    elif severity == "HIGH":
        recommended_action = "Hold the activity for analyst review and require customer verification."
    elif severity == "MEDIUM":
        recommended_action = "Require step-up authentication and monitor follow-up activity."
    else:
        recommended_action = "Allow the activity and continue passive monitoring."

    return {
        "summary": summary,
        "recommended_action": recommended_action,
        "reasons": reasons,
    }


def determine_friction_action(risk_score: int, trust_score: int) -> dict:
    trusted_customer = False

    if risk_score <= 30:
        action = "ALLOW"
        label = "Allow"
        customer_message = "Your transaction was allowed."
        analyst_message = "Low-risk event. No additional friction required."
    elif risk_score <= 60:
        action = "REQUIRE_2FA"
        label = "Require 2FA"
        customer_message = "Additional verification is required."
        analyst_message = "Medium-risk event. Step-up authentication recommended."
        if trust_score >= 80:
            trusted_customer = True
        elif trust_score < 50:
            action = "HOLD_FOR_REVIEW"
            label = "Hold for Review"
            customer_message = "Your transaction is temporarily held for security review."
            analyst_message = "Medium-risk event escalated because customer trust is low."
    elif risk_score <= 80:
        action = "HOLD_FOR_REVIEW"
        label = "Hold for Review"
        customer_message = "Your transaction is temporarily held for security review."
        analyst_message = "High-risk event. Analyst review required."
    else:
        action = "BLOCK_AND_ALERT"
        label = "Block and Alert"
        customer_message = "This transaction was blocked for your protection."
        analyst_message = "Critical-risk event. Block transaction and investigate immediately."

    if trust_score < 30 and risk_score > 60:
        action = "BLOCK_AND_ALERT"
        label = "Block and Alert"
        customer_message = "This transaction was blocked for your protection."
        analyst_message = "High-risk event escalated to block because customer trust is critical."

    message = customer_message
    if trusted_customer:
        analyst_message = f"{analyst_message} Customer is trusted; retain 2FA instead of escalation."

    return {
        "action": action,
        "label": label,
        "message": message,
        "customer_message": customer_message,
        "analyst_message": analyst_message,
    }


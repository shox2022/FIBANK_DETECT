from fraud_detector import FraudDetector

detector = FraudDetector()  # loads outputs/fibank_fraud_model.ubj automatically

# Single transaction — returns fraud % directly
result = detector.score({
    "amount": 5000.0,
    "recipient_is_new": 1,
    "login_vpn_count": 2,
    "trust_score": 30.0,
})

print(result["fraud_percentage"])  # e.g. 46.36  (out of 100)
print(result["fraud_risk_band"])  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
print(result["fraud_flag"])  # 1 = fraud, 0 = legitimate

tx1 = {
    "amount": 5000.0,
    "recipient_is_new": 1,
    "login_vpn_count": 2,
    "trust_score": 30.0,
}

tx2 = {
    "amount": 7000.0,
    "recipient_is_new": 1,
    "login_vpn_count": 25,
    "trust_score": 30.0,
}

tx3 = {
    "amount": 200000.0,
    "recipient_is_new": 0,
    "login_vpn_count": 20,
    "trust_score": 50.0,
}

# Multiple transactions at once
# results = detector.score_batch([tx1, tx2, tx3])
# print(results)

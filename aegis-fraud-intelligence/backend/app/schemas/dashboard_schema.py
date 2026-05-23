from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_alerts: int
    critical_alerts: int
    blocked_transactions: int
    average_trust_score: float
    suspicious_log_count: int
    mule_accounts_count: int
    recent_alerts: list[dict]
    recent_transactions: list[dict]


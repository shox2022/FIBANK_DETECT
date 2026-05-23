from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    alert_type: str
    severity: str
    risk_score: int
    title: str
    status: str
    created_at: datetime


class AlertDetailResponse(AlertResponse):
    explanation: str
    recommended_action: str
    customer_name: str | None = None
    trust_score: int | None = None


class AlertStatusUpdate(BaseModel):
    status: str


class IncidentReportResponse(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    customer: str | None = None
    risk_score: int
    trust_score: int | None = None
    timeline_summary: list[str]
    key_risk_indicators: list[str]
    explanation: str
    recommended_action: str
    analyst_notes_placeholder: str
    status: str
    generated_at: datetime


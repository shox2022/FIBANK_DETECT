from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BankMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    channel: str
    title: str
    body: str
    message_type: str
    official: bool
    risk_level: str
    related_alert_id: int | None = None
    created_at: datetime


class MessageVerificationRequest(BaseModel):
    message_text: str = Field(min_length=5, max_length=5000)
    user_id: int | None = None


class MessageVerificationResponse(BaseModel):
    result: str
    risk_score: int
    matched_message: BankMessageResponse | None = None
    reasons: list[str]
    recommendation: str
    checked_at: datetime


class MessageVerificationCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    submitted_text: str
    matched_message_id: int | None = None
    result: str
    risk_score: int
    reasons: Any
    recommendation: str
    created_at: datetime

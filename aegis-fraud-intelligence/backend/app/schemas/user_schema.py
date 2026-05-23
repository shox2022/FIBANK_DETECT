from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    home_country: str | None = None
    home_city: str | None = None
    trust_score: int
    average_transaction_amount: float
    account_number: str | None = None
    balance: float
    created_at: datetime
    updated_at: datetime


class TimelineEventResponse(BaseModel):
    event_type: str
    title: str
    description: str
    severity: str | None = None
    risk_score: int | None = None
    created_at: datetime


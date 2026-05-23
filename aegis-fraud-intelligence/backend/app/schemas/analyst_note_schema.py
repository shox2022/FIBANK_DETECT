from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalystNoteCreate(BaseModel):
    note: str = Field(..., min_length=2, max_length=2000)
    action_type: str = "NOTE"


class AnalystNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    analyst_user_id: int
    analyst_name: str | None = None
    note: str
    action_type: str
    old_status: str | None = None
    new_status: str | None = None
    created_at: datetime

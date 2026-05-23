from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("fraud_alerts.id"), nullable=False, index=True)
    analyst_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    note = Column(Text, nullable=False)
    action_type = Column(String(40), nullable=False, default="NOTE", index=True)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    alert = relationship("FraudAlert", back_populates="analyst_notes")
    analyst = relationship("User", back_populates="analyst_notes")

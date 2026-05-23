from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    alert_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(30), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    title = Column(String(180), nullable=False)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="OPEN", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="fraud_alerts")
    analyst_notes = relationship(
        "AnalystNote",
        back_populates="alert",
        cascade="all, delete-orphan",
    )

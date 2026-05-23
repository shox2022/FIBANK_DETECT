from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class BankMessage(Base):
    __tablename__ = "bank_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel = Column(String(30), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    message_type = Column(String(60), nullable=False, index=True)
    official = Column(Boolean, nullable=False, default=True)
    risk_level = Column(String(30), nullable=False, default="LOW", index=True)
    related_alert_id = Column(Integer, ForeignKey("fraud_alerts.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="bank_messages")
    related_alert = relationship("FraudAlert")

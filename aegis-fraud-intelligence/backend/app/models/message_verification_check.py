from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MessageVerificationCheck(Base):
    __tablename__ = "message_verification_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    submitted_text = Column(Text, nullable=False)
    matched_message_id = Column(Integer, ForeignKey("bank_messages.id"), nullable=True)
    result = Column(String(40), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    reasons = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="message_verification_checks")
    matched_message = relationship("BankMessage")

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    endpoint = Column(String(160), nullable=True)
    ip_address = Column(String(64), nullable=True)
    payload_sample = Column(Text, nullable=True)
    risk_score = Column(Integer, nullable=False, default=0)
    severity = Column(String(30), nullable=False, default="LOW", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="security_logs")


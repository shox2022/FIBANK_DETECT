from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class LoginEvent(Base):
    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_hash = Column(String(128), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    country = Column(String(80), nullable=True)
    city = Column(String(80), nullable=True)
    is_vpn = Column(Boolean, nullable=False, default=False)
    is_proxy = Column(Boolean, nullable=False, default=False)
    success = Column(Boolean, nullable=False, default=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    risk_score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="login_events")


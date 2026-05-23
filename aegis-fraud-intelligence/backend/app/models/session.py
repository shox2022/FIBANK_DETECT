from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token_hash = Column(String(255), nullable=False, index=True)
    device_hash = Column(String(128), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    country = Column(String(80), nullable=True)
    city = Column(String(80), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")


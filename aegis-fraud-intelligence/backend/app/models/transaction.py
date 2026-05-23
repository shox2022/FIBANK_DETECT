from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    from_account = Column(String(64), nullable=False, index=True)
    to_account = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="EUR")
    recipient_name = Column(String(120), nullable=True)
    recipient_is_new = Column(Boolean, nullable=False, default=False)
    status = Column(String(30), nullable=False, default="ALLOWED", index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="transactions")


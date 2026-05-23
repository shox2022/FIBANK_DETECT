from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class MuleEdge(Base):
    __tablename__ = "mule_edges"

    id = Column(Integer, primary_key=True, index=True)
    from_account = Column(String(64), nullable=False, index=True)
    to_account = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    risk_score = Column(Integer, nullable=False, default=0)


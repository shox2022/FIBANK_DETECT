from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(80), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    points = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)


from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class BrandScanRun(Base):
    __tablename__ = "brand_scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    target_domain = Column(String(255), nullable=False)
    target_brand = Column(String(120), nullable=False)
    mode = Column(String(20), nullable=False, default="QUICK", index=True)
    status = Column(String(20), nullable=False, default="RUNNING", index=True)
    total_candidates = Column(Integer, nullable=False, default=0)
    live_domains_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    low_count = Column(Integer, nullable=False, default=0)
    none_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    findings = relationship(
        "BrandThreatFinding",
        back_populates="scan_run",
        cascade="all, delete-orphan",
    )

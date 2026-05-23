from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class BrandThreatFinding(Base):
    __tablename__ = "brand_threat_findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, ForeignKey("brand_scan_runs.id"), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    title = Column(String(250), nullable=True)
    redirected_to = Column(String(500), nullable=True)
    risk_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(20), nullable=False, default="NONE", index=True)
    matched_brand_keywords = Column(Text, nullable=False, default="[]")
    matched_phishing_signals = Column(Text, nullable=False, default="[]")
    has_favicon = Column(Boolean, nullable=False, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    scan_run = relationship("BrandScanRun", back_populates="findings")

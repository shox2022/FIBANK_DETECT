from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BrandScanRequest(BaseModel):
    quick: bool = True
    max_candidates: int | None = Field(default=None, ge=10, le=1000)


class BrandScanRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_domain: str
    target_brand: str
    mode: str
    status: str
    total_candidates: int
    live_domains_count: int
    high_count: int
    medium_count: int
    low_count: int
    none_count: int
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class BrandThreatFindingResponse(BaseModel):
    id: int
    domain: str
    url: str | None = None
    status_code: int | None = None
    title: str | None = None
    redirected_to: str | None = None
    risk_score: int
    risk_level: str
    matched_brand_keywords: list[str]
    matched_phishing_signals: list[str]
    has_favicon: bool
    error: str | None = None
    created_at: datetime


class BrandScanDetailResponse(BrandScanRunResponse):
    findings: list[BrandThreatFindingResponse]


class BrandProtectionSummaryResponse(BaseModel):
    latest_scan_id: int | None = None
    latest_scan_time: datetime | None = None
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_findings: int = 0
    top_risky_domains: list[dict[str, Any]] = Field(default_factory=list)

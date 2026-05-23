from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import cast

from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models import BrandScanRun, BrandThreatFinding, User
from app.threat_intel import web_detector

logger = logging.getLogger(__name__)


def _safe_error(exc: BaseException | str) -> str:
    return str(exc).replace("\n", " ")[:500]


def _json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=True)


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return [value]


def _finding_payload(finding: BrandThreatFinding) -> dict:
    return {
        "id": finding.id,
        "domain": finding.domain,
        "url": finding.url,
        "status_code": finding.status_code,
        "title": finding.title,
        "redirected_to": finding.redirected_to,
        "risk_score": finding.risk_score,
        "risk_level": finding.risk_level,
        "matched_brand_keywords": _parse_json_list(cast(str | None, finding.matched_brand_keywords)),
        "matched_phishing_signals": _parse_json_list(cast(str | None, finding.matched_phishing_signals)),
        "has_favicon": finding.has_favicon,
        "error": finding.error,
        "created_at": finding.created_at,
    }


def _run_payload(scan: BrandScanRun) -> dict:
    return {
        "id": scan.id,
        "target_domain": scan.target_domain,
        "target_brand": scan.target_brand,
        "mode": scan.mode,
        "status": scan.status,
        "total_candidates": scan.total_candidates,
        "live_domains_count": scan.live_domains_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "none_count": scan.none_count,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at,
        "error": scan.error,
    }


def _detail_payload(scan: BrandScanRun) -> dict:
    payload = _run_payload(scan)
    payload["findings"] = [_finding_payload(finding) for finding in scan.findings]
    payload["findings"].sort(key=lambda item: item["risk_score"], reverse=True)
    return payload


def _limit_candidates(candidates: list[str], quick: bool, max_candidates: int) -> list[str]:
    if quick:
        brand = settings.brand_target_name.lower()
        candidates = [domain for domain in candidates if brand in domain.lower()]
    return candidates[:max_candidates]


def run_brand_scan(
    db: Session,
    current_user: User,
    quick: bool = True,
    max_candidates: int | None = None,
) -> dict:
    if not settings.brand_protection_enabled:
        raise RuntimeError("Brand protection is disabled")

    candidate_limit = min(
        max_candidates or settings.brand_scan_max_candidates,
        settings.brand_scan_max_candidates,
    )
    mode = "QUICK" if quick else "FULL"
    scan = BrandScanRun(
        target_domain=settings.brand_target_domain,
        target_brand=settings.brand_target_name,
        mode=mode,
        status="RUNNING",
        created_by_user_id=current_user.id,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        candidates = web_detector.generate_candidates(
            target_domain=settings.brand_target_domain,
            target_brand=settings.brand_target_name,
        )
        candidates = _limit_candidates(candidates, quick=quick, max_candidates=candidate_limit)
        scan.total_candidates = len(candidates)
        db.add(scan)
        db.commit()

        live_domains = web_detector.filter_live_domains(
            candidates,
            timeout=min(settings.brand_scan_request_timeout, 5),
            delay=min(settings.brand_scan_request_delay, 1.0),
        )
        scan.live_domains_count = len(live_domains)
        db.add(scan)
        db.commit()

        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "NONE": 0}
        for domain in live_domains:
            page = web_detector.fetch_page(
                domain,
                timeout=settings.brand_scan_request_timeout,
            )
            scored = web_detector.score_impersonation(
                page,
                target_brand=settings.brand_target_name,
                target_domain=settings.brand_target_domain,
            )
            risk_level = scored["risk_level"]
            counts[risk_level] = counts.get(risk_level, 0) + 1
            finding = BrandThreatFinding(
                scan_run_id=scan.id,
                domain=domain,
                url=page.url,
                status_code=page.status_code,
                title=page.title,
                redirected_to=page.redirected_to,
                risk_score=scored["risk_score"],
                risk_level=risk_level,
                matched_brand_keywords=_json_list(scored["matched_brand_keywords"]),
                matched_phishing_signals=_json_list(scored["matched_phishing_signals"]),
                has_favicon=page.has_favicon,
                error=page.error,
            )
            db.add(finding)
            db.flush()
            if settings.brand_scan_request_delay > 0:
                time.sleep(min(settings.brand_scan_request_delay, 1.0))

        scan.high_count = counts["HIGH"]
        scan.medium_count = counts["MEDIUM"]
        scan.low_count = counts["LOW"]
        scan.none_count = counts["NONE"]
        scan.status = "COMPLETED"
        scan.completed_at = datetime.utcnow()
        db.add(scan)
        db.commit()
        return get_brand_scan_detail(db, scan.id)
    except Exception as exc:
        logger.exception("Brand protection scan failed")
        scan.status = "FAILED"
        scan.error = _safe_error(exc)
        scan.completed_at = datetime.utcnow()
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return _detail_payload(scan)


def get_brand_scan_runs(db: Session) -> list[dict]:
    runs = (
        db.query(BrandScanRun)
        .order_by(BrandScanRun.started_at.desc())
        .limit(25)
        .all()
    )
    return [_run_payload(run) for run in runs]


def get_brand_scan_detail(db: Session, scan_id: int) -> dict:
    scan = (
        db.query(BrandScanRun)
        .options(selectinload(BrandScanRun.findings))
        .filter(BrandScanRun.id == scan_id)
        .first()
    )
    if scan is None:
        raise ValueError("Brand scan not found")
    return _detail_payload(scan)


def get_latest_brand_scan(db: Session) -> dict | None:
    scan = (
        db.query(BrandScanRun)
        .options(selectinload(BrandScanRun.findings))
        .filter(BrandScanRun.status == "COMPLETED")
        .order_by(BrandScanRun.completed_at.desc())
        .first()
    )
    if scan is None:
        return None
    return _detail_payload(scan)


def get_brand_protection_summary(db: Session) -> dict:
    latest = get_latest_brand_scan(db)
    if latest is None:
        return {
            "latest_scan_id": None,
            "latest_scan_time": None,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "total_findings": 0,
            "top_risky_domains": [],
        }

    findings = latest.get("findings", [])
    top = sorted(findings, key=lambda item: item["risk_score"], reverse=True)[:5]
    return {
        "latest_scan_id": latest["id"],
        "latest_scan_time": latest["completed_at"],
        "high_count": latest["high_count"],
        "medium_count": latest["medium_count"],
        "low_count": latest["low_count"],
        "total_findings": len(findings),
        "top_risky_domains": [
            {
                "domain": item["domain"],
                "risk_score": item["risk_score"],
                "risk_level": item["risk_level"],
                "title": item["title"],
            }
            for item in top
        ],
    }


def get_brand_protection_config() -> dict:
    return {
        "enabled": settings.brand_protection_enabled,
        "target_domain": settings.brand_target_domain,
        "target_brand": settings.brand_target_name,
        "target_url": settings.brand_target_url,
        "quick_default": settings.brand_scan_quick_default,
        "max_candidates": settings.brand_scan_max_candidates,
        "request_timeout": settings.brand_scan_request_timeout,
        "request_delay": settings.brand_scan_request_delay,
    }

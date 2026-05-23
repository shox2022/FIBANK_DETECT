from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse


COMMON_TLDS = ["al", "com", "net", "org", "info", "online", "site", "co", "eu"]
BRAND_KEYWORDS = ["fibank", "first investment bank", "bank", "banking", "e-banking", "online banking"]
PHISHING_SIGNALS = [
    "password",
    "pin",
    "otp",
    "one-time password",
    "card number",
    "cvv",
    "verify",
    "blocked",
    "suspended",
    "urgent",
    "login",
    "sign in",
]


@dataclass
class PageFetchResult:
    domain: str
    url: str | None
    status_code: int | None
    title: str | None
    text_sample: str
    links: list[str]
    has_favicon: bool
    redirected_to: str | None
    error: str | None = None


def generate_candidates(target_domain: str = "fibank.al", target_brand: str = "fibank") -> list[str]:
    """Generate likely lookalike and typosquatting candidates for passive checks."""
    brand = target_brand.lower().replace(" ", "")
    root = target_domain.split(".")[0].lower()
    variants = {
        brand,
        root,
        f"{brand}-online",
        f"{brand}-login",
        f"{brand}-secure",
        f"{brand}-verify",
        f"{brand}bank",
        f"my{brand}",
        f"{brand}app",
        f"{brand}support",
        f"{brand}security",
        f"{brand}al",
        f"{brand}-al",
        f"online-{brand}",
        f"secure-{brand}",
        f"login-{brand}",
        f"{brand}online",
        f"{brand}login",
        f"{brand}secure",
        f"{brand}verify",
    }

    substitutions = {
        "i": ["1", "l"],
        "a": ["4"],
        "b": ["8"],
        "o": ["0"],
    }
    for index, char in enumerate(brand):
        for replacement in substitutions.get(char, []):
            variants.add(f"{brand[:index]}{replacement}{brand[index + 1:]}")
    for index in range(len(brand)):
        variants.add(f"{brand[:index]}{brand[index + 1:]}")
    for index in range(1, len(brand)):
        variants.add(f"{brand[:index]}-{brand[index:]}")

    candidates = {target_domain.lower()}
    for variant in variants:
        cleaned = variant.strip("-")
        if not cleaned or len(cleaned) < 3:
            continue
        for tld in COMMON_TLDS:
            candidates.add(f"{cleaned}.{tld}")
    return sorted(candidates)


def resolves(domain: str, timeout: float = 3.0) -> bool:
    """Resolve A/CNAME passively. Falls back to socket if dnspython is unavailable."""
    try:
        import dns.resolver

        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        resolver.timeout = min(timeout, 2.0)
        for record_type in ["A", "CNAME"]:
            try:
                answers = resolver.resolve(domain, record_type)
                if answers:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        try:
            socket.gethostbyname(domain)
            return True
        except OSError:
            return False


def filter_live_domains(domains: Iterable[str], timeout: float = 3.0, delay: float = 0.0) -> list[str]:
    live = []
    for domain in domains:
        if resolves(domain, timeout=timeout):
            live.append(domain)
        if delay > 0:
            time.sleep(delay)
    return live


def _favicon_present(soup, base_url: str) -> bool:
    for link in soup.find_all("link"):
        rel = " ".join(link.get("rel", [])).lower() if isinstance(link.get("rel"), list) else str(link.get("rel", "")).lower()
        href = link.get("href")
        if href and ("icon" in rel or "shortcut" in rel):
            return bool(urljoin(base_url, href))
    return False


def fetch_page(domain: str, timeout: float = 8.0) -> PageFetchResult:
    """Fetch only top-level HTTP/HTTPS metadata. No forms, auth, or crawling."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as exc:
        return PageFetchResult(domain, None, None, None, "", [], False, None, f"Dependency unavailable: {type(exc).__name__}")

    headers = {
        "User-Agent": "AEGIS-BrandProtection/0.1 defensive-metadata-check"
    }
    last_error = None
    for scheme in ["https", "http"]:
        url = f"{scheme}://{domain}"
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            content_type = response.headers.get("content-type", "")
            html = response.text[:200_000] if "text/html" in content_type or response.text else ""
            soup = BeautifulSoup(html, "html.parser") if html else None
            title = soup.title.string.strip()[:250] if soup and soup.title and soup.title.string else None
            text_sample = soup.get_text(" ", strip=True)[:5000] if soup else ""
            links = []
            if soup:
                for link in soup.find_all("a", href=True)[:30]:
                    links.append(urljoin(response.url, link["href"])[:500])
            return PageFetchResult(
                domain=domain,
                url=response.url,
                status_code=response.status_code,
                title=title,
                text_sample=text_sample,
                links=links,
                has_favicon=_favicon_present(soup, response.url) if soup else False,
                redirected_to=response.url if response.url != url else None,
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:220]}"
    return PageFetchResult(domain, None, None, None, "", [], False, None, last_error)


def score_impersonation(
    page: PageFetchResult,
    target_brand: str = "fibank",
    target_domain: str = "fibank.al",
) -> dict:
    domain_text = page.domain.lower()
    title_text = (page.title or "").lower()
    body_text = page.text_sample.lower()
    link_text = " ".join(page.links).lower()
    combined = f"{domain_text} {title_text} {body_text} {link_text}"
    target_brand = target_brand.lower()
    target_domain = target_domain.lower()

    score = 0
    matched_brand_keywords = []
    matched_phishing_signals = []

    if target_brand in domain_text and page.domain.lower() != target_domain:
        score += 30
        matched_brand_keywords.append(target_brand)

    for keyword in BRAND_KEYWORDS:
        if keyword.lower() in combined and keyword not in matched_brand_keywords:
            matched_brand_keywords.append(keyword)
            score += 8

    for signal in PHISHING_SIGNALS:
        if signal in combined:
            matched_phishing_signals.append(signal)
            score += 10

    parsed_host = urlparse(page.url or "").netloc.lower()
    if parsed_host and target_domain not in parsed_host and matched_brand_keywords:
        score += 20
        matched_phishing_signals.append("brand keywords on non-official domain")

    if page.redirected_to and target_domain not in page.redirected_to.lower() and matched_brand_keywords:
        score += 10
        matched_phishing_signals.append("redirects away from official domain")

    if page.error:
        score = min(score, 20)

    risk_score = max(0, min(100, score))
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    elif risk_score >= 15:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "matched_brand_keywords": sorted(set(matched_brand_keywords)),
        "matched_phishing_signals": sorted(set(matched_phishing_signals)),
    }

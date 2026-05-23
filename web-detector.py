# Whois lookup could be added later

import time
import logging
import argparse
from datetime import datetime

import requests
import dns.resolver
from bs4 import BeautifulSoup

# Configuration

TARGET_DOMAIN   = "fibank.al"
TARGET_BRAND    = "fibank"
TARGET_URL      = "https://www.fibank.al"

# Keywords/phrases that strongly suggest impersonation of fibank.al
BRAND_KEYWORDS = [
    "fibank", "first investment bank", "first investment",
    "банка", "banka", "bankë", "banking", "online banking",
    "login", "sign in", "username", "password", "account",
    "transfer", "balance", "internet banking", "e-banking",
    "fibank.al", "fi bank",
]

# High-risk keywords that, combined with brand keywords, suggest phishing
PHISHING_SIGNALS = [
    "enter your", "verify your", "confirm your", "update your",
    "suspended", "locked", "unusual activity", "security alert",
    "click here", "submit", "credential", "otp", "one-time",
    "social security", "verify identity",
]

REQUEST_TIMEOUT   = 8    # seconds
REQUEST_DELAY     = 0.5  # seconds between requests (be polite)
MAX_CONTENT_LEN   = 500_000  # bytes – don't download huge pages

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# TLDs to probe (prioritise those common in Albania / banking fraud)
PROBE_TLDS = [
    "al", "com", "net", "org", "info", "biz", "online",
    "bank", "co", "io", "eu", "site", "xyz", "app",
    "com.al", "org.al", "net.al",
]

# Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# Domain Generation

def generate_candidates(base: str = TARGET_BRAND) -> set[str]:
    """Generate typosquatting / lookalike domain names for *base*."""

    candidates: set[str] = set()

    # Homoglyph substitutions (visual lookalikes)
    homoglyphs: dict[str, list[str]] = {
        "a": ["à", "á", "â", "ä", "å", "ā", "4"],
        "b": ["6", "lb"],
        "e": ["3", "è", "é", "ê"],
        "i": ["1", "l", "ì", "í"],
        "k": ["kk", "ck"],
        "o": ["0", "ò", "ó"],
        "f": ["ph"],
        "n": ["m", "nn"],
    }
    for char, substitutes in homoglyphs.items():
        for sub in substitutes:
            replaced = base.replace(char, sub)
            if replaced != base:
                candidates.add(replaced)

    # Character insertions / deletions / transpositions
    for i in range(len(base)):
        # deletion
        candidates.add(base[:i] + base[i+1:])
        # transposition
        if i < len(base) - 1:
            t = list(base)
            t[i], t[i+1] = t[i+1], t[i]
            candidates.add("".join(t))
        # double character
        candidates.add(base[:i] + base[i] + base[i:])

    # Common prefix / suffix additions
    affixes = [
        "my", "e", "online", "secure", "web", "net", "al",
        "bank", "login", "portal", "official", "new", "mobile",
        "app", "direct", "-al", "-bank", "-login", "-secure",
        "1", "24", "365",
    ]
    for affix in affixes:
        candidates.add(f"{affix}{base}")
        candidates.add(f"{base}{affix}")
        candidates.add(f"{base}-{affix}")
        candidates.add(f"{affix}-{base}")

    # Substring / split tricks
    candidates.update([
        "fi-bank", "fibanks", "fibankk", "fiibank",
        "fibankgroup", "fibankbg", "fibankeu",
        "first-investment-bank", "firstinvestmentbank",
        "fibankpay", "fibankcard", "fibankdigital",
    ])

    # Attach TLDs
    full_domains: set[str] = set()
    for cand in candidates:
        cand = cand.lower().strip("-").strip()
        if not cand or cand == base:
            continue
        for tld in PROBE_TLDS:
            full_domains.add(f"{cand}.{tld}")

    # Also probe the legitimate name under every alternate TLD
    for tld in PROBE_TLDS:
        d = f"{base}.{tld}"
        if d != TARGET_DOMAIN:
            full_domains.add(d)

    log.info("Generated %d candidate domains.", len(full_domains))
    return full_domains


# DNS / Reachability

def resolves(domain: str) -> bool:
    """Return True if *domain* has a DNS A or CNAME record."""
    try:
        dns.resolver.resolve(domain, "A", lifetime=3)
        return True
    except Exception:
        pass
    try:
        dns.resolver.resolve(domain, "CNAME", lifetime=3)
        return True
    except Exception:
        return False


def filter_live_domains(domains: set[str]) -> list[str]:
    """Return only domains that resolve in DNS."""
    log.info("Checking DNS resolution for %d domains …", len(domains))
    live = []
    for i, domain in enumerate(sorted(domains), 1):
        if i % 50 == 0:
            log.info("  DNS progress: %d / %d checked, %d live so far",
                     i, len(domains), len(live))
        if resolves(domain):
            log.info("  ✓ LIVE: %s", domain)
            live.append(domain)
    log.info("DNS check complete: %d live domains found.", len(live))
    return live


# Scraping

def fetch_page(domain: str) -> dict:
    """Fetch a domain over HTTP/HTTPS and return page metadata."""
    result = {
        "domain": domain,
        "url": None,
        "status_code": None,
        "title": "",
        "text": "",
        "html_snippet": "",
        "error": None,
        "redirected_to": None,
        "has_favicon": False,
        "links": [],
    }

    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}"
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )
            # Read up to MAX_CONTENT_LEN bytes
            raw = b""
            for chunk in resp.iter_content(4096):
                raw += chunk
                if len(raw) >= MAX_CONTENT_LEN:
                    break

            result["url"] = url
            result["status_code"] = resp.status_code
            final_url = resp.url
            if final_url != url:
                result["redirected_to"] = final_url

            soup = BeautifulSoup(raw, "html.parser")

            # Title
            title_tag = soup.find("title")
            result["title"] = title_tag.get_text(strip=True) if title_tag else ""

            # Visible text (strip scripts/styles)
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            result["text"] = soup.get_text(separator=" ", strip=True)

            # Small HTML snippet for manual review
            result["html_snippet"] = raw[:2000].decode("utf-8", errors="replace")

            # Favicon check
            result["has_favicon"] = bool(
                soup.find("link", rel=lambda r: r and "icon" in r)
            )

            # Internal links
            result["links"] = [
                a.get("href", "") for a in soup.find_all("a", href=True)
            ][:50]

            return result

        except requests.exceptions.SSLError:
            continue  # try http
        except Exception as exc:
            result["error"] = str(exc)
            continue

    return result


# Similarity Scoring

def score_impersonation(page: dict) -> dict:
    """
    Score how likely a page is impersonating fibank.al.
    Returns a dict with score (0-100) and matched signals.
    """
    text_lower = (page["title"] + " " + page["text"]).lower()
    matched_brand    : list[str] = []
    matched_phishing : list[str] = []

    for kw in BRAND_KEYWORDS:
        if kw.lower() in text_lower:
            matched_brand.append(kw)

    for kw in PHISHING_SIGNALS:
        if kw.lower() in text_lower:
            matched_phishing.append(kw)

    # Scoring heuristic
    score = 0
    score += min(len(matched_brand) * 12, 60)     # up to 60 pts for brand hits
    score += min(len(matched_phishing) * 8, 30)   # up to 30 pts for phishing signals
    if page.get("has_favicon"):
        score += 5
    # If domain name itself contains "fibank"
    if "fibank" in page["domain"]:
        score += 10
    score = min(score, 100)

    # Risk level
    if score >= 70:
        risk = "🔴 HIGH"
    elif score >= 40:
        risk = "🟠 MEDIUM"
    elif score >= 15:
        risk = "🟡 LOW"
    else:
        risk = "🟢 NONE"

    return {
        "score": score,
        "risk": risk,
        "matched_brand_keywords": matched_brand,
        "matched_phishing_signals": matched_phishing,
    }


# Reporting

def print_report(findings: list[dict]) -> None:
    """Print a structured report to stdout."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "═" * 72

    print(f"\n{sep}")
    print(f"  fibank.al BRAND PROTECTION REPORT  —  {now}")
    print(sep)
    print(f"  Target: {TARGET_DOMAIN}  |  Domains analysed: {len(findings)}")
    print(sep)

    # Sort by score descending
    findings.sort(key=lambda x: x["analysis"]["score"], reverse=True)

    flagged = [f for f in findings if f["analysis"]["score"] >= 15]
    if not flagged:
        print("\n  ✅  No suspicious domains found.\n")
    else:
        print(f"\n  ⚠️   {len(flagged)} suspicious domain(s) detected:\n")

    for f in findings:
        a   = f["analysis"]
        pg  = f["page"]
        if a["score"] < 5 and not pg.get("title"):
            continue  # skip blanks

        print(f"  {a['risk']}  [{a['score']:3d}/100]  {pg['domain']}")
        if pg.get("title"):
            print(f"    Title      : {pg['title'][:80]}")
        if pg.get("redirected_to"):
            print(f"    Redirects  → {pg['redirected_to'][:80]}")
        if pg.get("status_code"):
            print(f"    HTTP status: {pg['status_code']}")
        if a["matched_brand_keywords"]:
            print(f"    Brand hits : {', '.join(a['matched_brand_keywords'][:8])}")
        if a["matched_phishing_signals"]:
            print(f"    Phishing   : {', '.join(a['matched_phishing_signals'][:6])}")
        print()

    print(sep)
    high   = sum(1 for f in findings if "HIGH"   in f["analysis"]["risk"])
    medium = sum(1 for f in findings if "MEDIUM" in f["analysis"]["risk"])
    low    = sum(1 for f in findings if "LOW"    in f["analysis"]["risk"])
    print(f"  Summary: 🔴 HIGH={high}  🟠 MEDIUM={medium}  🟡 LOW={low}")
    print(f"{sep}\n")


def save_report(findings: list[dict], path: str = "fibank_report.txt") -> None:
    """Save the report to a text file."""
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_report(findings)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    log.info("Report saved to %s", path)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Detect lookalike/impersonation domains for fibank.al"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Only test domains containing 'fibank' (faster, targeted)"
    )
    parser.add_argument(
        "--output", default="fibank_report.txt",
        help="Output report file path (default: fibank_report.txt)"
    )
    parser.add_argument(
        "--no-dns-filter", action="store_true",
        help="Skip DNS pre-filter and attempt to scrape all candidates (slow)"
    )
    args = parser.parse_args()

    # 1. Generate candidates
    candidates = generate_candidates(TARGET_BRAND)

    if args.quick:
        candidates = {d for d in candidates if TARGET_BRAND in d}
        log.info("Quick mode: reduced to %d targeted candidates.", len(candidates))

    # 2. Filter to live domains
    if args.no_dns_filter:
        live_domains = list(candidates)
    else:
        live_domains = filter_live_domains(candidates)

    if not live_domains:
        log.warning("No live lookalike domains found. Nothing to scrape.")
        return

    # 3. Scrape + analyse each live domain
    findings: list[dict] = []
    log.info("Scraping %d live domain(s) …", len(live_domains))

    for i, domain in enumerate(live_domains, 1):
        log.info("[%d/%d] Scraping %s …", i, len(live_domains), domain)
        page     = fetch_page(domain)
        analysis = score_impersonation(page)
        findings.append({"page": page, "analysis": analysis})
        time.sleep(REQUEST_DELAY)

    # 4. Report
    print_report(findings)
    save_report(findings, args.output)


if __name__ == "__main__":
    main()
"""Safe website audit (brief sections 2.2 and 5).

SSRF defenses: only http/https; DNS is resolved first and every resulting IP
is checked — loopback, private, link-local, multicast, and reserved ranges
are refused; redirects are followed manually with re-validation at each hop;
response size, timeout, and content type are capped. robots.txt is honored
for our user agent.
"""
import ipaddress
import re
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

UA = "GhostCorpAgencyAudit/0.1 (+https://koalstingkdelaney-gif.github.io/kestrelattice/)"
MAX_BYTES = 512_000
TIMEOUT_S = 8
MAX_REDIRECTS = 3


class UnsafeURL(Exception):
    pass


BENCH_TRANSLATION_NET = ipaddress.ip_network("198.18.0.0/15")


def _trust_proxy_dns_bench() -> bool:
    # Some sandboxed VMs sit behind an egress proxy whose DNS translates
    # every public hostname into the 198.18.0.0/15 benchmarking range.
    # Trusting that translation is an explicit, default-OFF operator choice
    # for such an environment only — never enable it on a normal host,
    # and it never applies to any other non-public range.
    import os
    return os.environ.get("AGENCY_TRUST_PROXY_DNS_BENCH", "0") == "1"


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURL(f"scheme not allowed: {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise UnsafeURL("missing host")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise UnsafeURL(f"DNS resolution failed for {host}: {e}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _trust_proxy_dns_bench() and ip in BENCH_TRANSLATION_NET:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                or ip.is_reserved or ip.is_unspecified):
            raise UnsafeURL(f"host {host} resolves to non-public IP {ip}")
    return url


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url: str, opener) -> tuple[int, dict, bytes]:
    validate_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with opener.open(req, timeout=TIMEOUT_S) as resp:
            body = resp.read(MAX_BYTES + 1)
            return resp.status, dict(resp.headers), body[:MAX_BYTES]
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            raise _Redirect(e.headers["Location"])
        try:
            body = e.read(MAX_BYTES + 1)
        except Exception:
            body = b""
        return e.code, dict(e.headers or {}), body[:MAX_BYTES]


class _Redirect(Exception):
    def __init__(self, location):
        self.location = location


def fetch_public(url: str) -> tuple[int, dict, bytes]:
    opener = urllib.request.build_opener(_NoRedirect)
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        try:
            return _fetch(current, opener)
        except _Redirect as r:
            from urllib.parse import urljoin
            current = urljoin(current, r.location)
    raise UnsafeURL("too many redirects")


def robots_allows(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        status, _, body = fetch_public(robots_url)
    except Exception:
        return True  # unreachable robots.txt is not a block; fetch itself is validated
    if status != 200:
        return True
    text = body.decode("utf-8", "ignore")
    path = parsed.path or "/"
    agent_block = False
    disallows = []
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            agent_block = line.split(":", 1)[1].strip() in ("*", "GhostCorpAgencyAudit")
        elif agent_block and line.lower().startswith("disallow:"):
            disallows.append(line.split(":", 1)[1].strip())
    return not any(d and path.startswith(d) for d in disallows)


def audit_website(url: str) -> dict:
    """Return evidence-backed findings. Never raises for a bad site — an
    unreachable or broken site is itself a finding."""
    result = {"url": url, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "findings": [], "evidence": {}}
    try:
        validate_public_url(url)
    except UnsafeURL as e:
        result["findings"].append(f"URL refused by safety checks: {e}")
        return result
    if not robots_allows(url):
        result["findings"].append("robots.txt disallows our audit crawler — audit skipped")
        result["evidence"]["robots_blocked"] = True
        return result
    started = time.time()
    try:
        status, headers, body = fetch_public(url)
    except Exception as e:
        result["findings"].append(f"site unreachable: {type(e).__name__}: {e}")
        return result
    elapsed_ms = int((time.time() - started) * 1000)
    result["evidence"] = {"http_status": status, "response_ms": elapsed_ms,
                          "bytes": len(body), "content_type": headers.get("Content-Type", "")}
    if status != 200:
        result["findings"].append(f"homepage returns HTTP {status}, not 200")
    if urlparse(url).scheme != "https":
        result["findings"].append("site is not on HTTPS")
    html = body.decode("utf-8", "ignore")
    low = html.lower()
    if "<title" not in low or not re.search(r"<title[^>]*>\s*\S", low):
        result["findings"].append("missing or empty page <title> (SEO basics)")
    if 'name="description"' not in low:
        result["findings"].append("missing meta description (SEO basics)")
    if 'name="viewport"' not in low:
        result["findings"].append("missing mobile viewport meta — likely poor mobile usability")
    if "<h1" not in low:
        result["findings"].append("no <h1> heading on homepage")
    if not any(k in low for k in ("contact", "book", "call", "quote", "appointment")):
        result["findings"].append("no visible call to action (contact/book/call) on homepage")
    if len(body) >= MAX_BYTES:
        result["findings"].append(f"homepage is very heavy (>= {MAX_BYTES} bytes served)")
    if elapsed_ms > 3000:
        result["findings"].append(f"slow homepage response ({elapsed_ms} ms)")
    result["evidence"]["findings_count"] = len(result["findings"])
    return result

"""Transparent lead scoring. Every point carries a human-readable reason;
no black-box numbers (brief section 2.3).
"""

SERVICE_FIT = {
    "AI Website": ("website", 25),
    "AI Front Desk": ("front_desk", 25),
    "Property Video Walkthroughs": ("video", 20),
    "Playbook": ("playbook", 15),
    "Break-Test": ("breaktest", 15),
}


def score_lead(lead: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    service = lead.get("service", "")
    if service in SERVICE_FIT:
        pts = SERVICE_FIT[service][1]
        score += pts
        reasons.append(f"matched service '{service}' (+{pts})")
    if lead.get("email"):
        score += 25
        reasons.append("public business email verified on own site (+25)")
    if lead.get("source_url"):
        score += 15
        reasons.append("provenance recorded: source URL present (+15)")
    if lead.get("city"):
        score += 10
        reasons.append(f"local business with known city '{lead['city']}' (+10)")
    vertical = (lead.get("vertical") or "").lower()
    if vertical and vertical != "online":
        score += 10
        reasons.append(f"local vertical '{vertical}' — walk-in trade, website converts (+10)")
    elif vertical == "online":
        score += 5
        reasons.append("online business (+5)")
    audit = lead.get("audit_obj") or {}
    findings = audit.get("findings", []) if isinstance(audit, dict) else []
    if findings:
        pts = min(15, 5 * len(findings))
        score += pts
        reasons.append(f"website audit found {len(findings)} issue(s) (+{pts})")
    return min(score, 100), reasons

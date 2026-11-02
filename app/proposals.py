"""Proposals built ONLY from the existing ghostcorpnet agency rate card.

Prices are the ones already live on the company's services page
(koalstingkdelaney-gif.github.io/kestrelattice/services/ai-agency.html).
Nothing here invents a price, a discount, a testimonial, or a guarantee.
Proposals are drafts: outbound sending stays with the existing gated
pipelines and owner rules.
"""

PACKAGES = {
    "AI Website": {
        "upfront_usd": 499,
        "monthly_usd": 0,
        "optional_care_monthly_usd": 99,
        "blurb": "A fast, mobile-first website built for your business, with contact "
                 "and booking calls to action, SEO basics, and analytics.",
    },
    "AI Front Desk": {
        "upfront_usd": 299,
        "monthly_usd": 149,
        "optional_care_monthly_usd": 0,
        "blurb": "Web chat on your site plus email lead follow-up, so enquiries get "
                 "answered when you're on a job. (Web chat and email only — not phone calls.)",
    },
    "Property Video Walkthroughs": {
        "upfront_usd": 199,
        "monthly_usd": 0,
        "optional_care_monthly_usd": 0,
        "blurb": "One property video walkthrough. A 4-pack is $599.",
    },
}


def build_proposal(lead: dict, audit: dict | None = None) -> dict:
    service = lead.get("service") or "AI Website"
    pkg = PACKAGES.get(service, PACKAGES["AI Website"])
    name = lead.get("name", "your business")
    lines = [
        f"Proposal for {name} — {service}",
        "",
        pkg["blurb"],
        "",
        f"Price: ${pkg['upfront_usd']} one-time"
        + (f" + ${pkg['monthly_usd']}/month" if pkg["monthly_usd"] else "")
        + (f" (optional care plan ${pkg['optional_care_monthly_usd']}/month)"
           if pkg["optional_care_monthly_usd"] else "")
        + ". No other charges.",
    ]
    if audit and audit.get("findings"):
        lines += ["", "What we found on your current site:"]
        for f in audit["findings"][:5]:
            lines.append(f"- {f}")
    lines += [
        "",
        "Next step: reply to this proposal and we'll confirm scope before any work "
        "or payment. Payment, when agreed, is taken through a secure checkout — "
        "never by card details in email.",
        "",
        "— Ghost Corp (ghostcorpnet)",
    ]
    return {
        "package": service,
        "total_upfront_usd": pkg["upfront_usd"],
        "monthly_usd": pkg["monthly_usd"],
        "body": "\n".join(lines),
    }

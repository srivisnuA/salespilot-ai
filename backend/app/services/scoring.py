"""Explainable lead scoring engine.

Transparent weighted scoring (0-100) over meaningful sales features:
job seniority, company size, industry fit, budget, buying timeline,
website activity, pricing-page visits, email opens, clicks, replies,
demo requests.

Architecture note: `score_lead()` is the single entry point. The current
MODEL_BACKEND is "rules" — a transparent weighted engine. The function
signature (features -> ScoreResult) is the contract for a future ML
backend (e.g. scikit-learn/XGBoost trained on won/lost outcomes);
swap implementations inside score_lead() without touching callers.
No model accuracy metrics are claimed anywhere — this is a rules engine.
"""
from dataclasses import dataclass, field

import datetime as dt

SENIORITY_POINTS = {
    "chief executive officer": 18, "ceo": 18, "chief": 16, "c-level": 16,
    "president": 15, "owner": 15, "founder": 15, "vp": 13,
    "vice president": 13, "head": 11, "director": 11, "senior": 8,
    "manager": 7, "lead": 6, "": 2,
}

COMPANY_SIZE_POINTS = {
    "1000+": 14, "201-1000": 11, "51-200": 8, "11-50": 5, "1-10": 2, "": 1,
}

# Industries where our product has strongest fit (SaaS-style sales teams).
INDUSTRY_FIT = {
    "SaaS": 10, "Technology": 9, "FinTech": 8, "E-commerce": 7,
    "Healthcare": 6, "Manufacturing": 5,
}

TIMELINE_POINTS = {
    "immediate": 12, "this quarter": 10, "quarter": 10, "6 months": 6,
    "half_year": 6, "1 year": 3, "year": 3, "unknown": 0, "": 0,
}

WEIGHTS = {
    "seniority": 20, "company_size": 14, "industry_fit": 12,
    "budget": 16, "timeline": 12, "website_activity": 6,
    "pricing_visits": 6, "email_opens": 6, "email_clicks": 6,
    "replies": 6, "demo_requests": 6,
}


@dataclass
class ScoreResult:
    score: int
    classification: str
    conversion_probability: float
    factors: list[dict] = field(default_factory=list)


def _seniority_points(title: str) -> tuple[float, str]:
    t = (title or "").lower()
    for key, pts in sorted(SENIORITY_POINTS.items(), key=lambda kv: -kv[1]):
        if key and key in t:
            return pts, f'Job title "{title}" maps to seniority level (+{pts:.0f})'
    return 2, "No seniority signal detected (+2)"


def _budget_points(budget: float) -> tuple[float, str]:
    if budget <= 0:
        return 0, "No budget information provided (0)"
    if budget >= 100000:
        pts = 14.0
    elif budget >= 50000:
        pts = 11.0
    elif budget >= 20000:
        pts = 8.0
    elif budget >= 10000:
        pts = 5.0
    else:
        pts = 3.0
    return pts, f"Declared budget ${budget:,.0f} (+{pts:.0f})"


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def score_lead(lead, engagement_events=None) -> ScoreResult:
    """Compute score 0-100 + factor breakdown for a lead ORM object."""
    events = engagement_events or []
    counts: dict[str, int] = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1

    factors: list[dict] = []

    def add(name: str, points: float, explanation: str):
        factors.append({
            "factor": name.replace("_", " ").title(),
            "points": round(points, 1),
            "max_points": WEIGHTS[name],
            "explanation": explanation,
            "kind": "positive" if points >= 0 else "negative",
        })

    pts, expl = _seniority_points(lead.job_title)
    add("seniority", pts, expl)

    size_pts = COMPANY_SIZE_POINTS.get(lead.company_size, 1)
    add("company_size", size_pts,
        f"Company size {lead.company_size or 'unknown'} (+{size_pts})")

    ind_pts = INDUSTRY_FIT.get(lead.industry, 3)
    add("industry_fit", ind_pts,
        f"{lead.industry or 'Unknown'} industry fit (+{ind_pts})")

    pts, expl = _budget_points(float(lead.budget or 0))
    add("budget", pts, expl)

    tl = (lead.buying_timeline or "").lower()
    tl_pts = TIMELINE_POINTS.get(tl, 0)
    add("timeline", tl_pts,
        f"Buying timeline: {lead.buying_timeline or 'unknown'} (+{tl_pts})")

    # Intent bonus: automation-driven intent (multiple opens, pricing interest)
    # Behavioral features from engagement events
    opens = counts.get("opened", 0)
    o_pts = min(opens, 4.0) * WEIGHTS["email_opens"] / 4.0 * 2.0
    o_pts = min(o_pts, WEIGHTS["email_opens"] * 2.0)
    add("email_opens", o_pts, f"{opens} email open(s) (+{o_pts:.1f})")

    clicks = counts.get("link_clicked", 0)
    c_pts = _clamp(clicks / 3.0, 0, 1) * WEIGHTS["email_clicks"]
    add("email_clicks", c_pts, f"{clicks} link click(s) (+{c_pts:.1f})")

    replies = counts.get("reply", 0)
    r_pts = min(replies, 2.0) * WEIGHTS["replies"]
    add("replies", r_pts, f"{replies} reply/replies (+{r_pts:.1f})")

    demos = counts.get("demo_requested", 0) + counts.get("meeting_booked", 0)
    d_pts = min(float(demos), 2.0) * WEIGHTS["demo_requests"] / 2.0 * 2.0
    d_pts = min(d_pts, WEIGHTS["demo_requests"] * 2.0)
    add("demo_requests", d_pts, f"{demos} demo/meeting request(s) (+{d_pts:.1f})")

    sent = counts.get("sent", 0) + counts.get("delivered", 0)
    website = counts.get("website_visit", 0)
    # website activity proxy: tracked visits + lead source quality
    wa_pts = min(WEIGHTS["website_activity"],
                 website * 2 + (2 if lead.source in ("inbound", "website", "referral") else 0)
                 + (lead.intent_score or 0) * 0.2)
    add("website_activity", wa_pts,
        f"{website} tracked visit(s), source {lead.source or 'unknown'}, intent score {lead.intent_score} (+{wa_pts:.1f})")

    pv_pts = min(WEIGHTS["pricing_visits"],
                 (lead.intent_score or 0) * 0.5 + counts.get("pricing_page_visit", 0) * 2)
    add("pricing_visits", pv_pts,
        f"Pricing page interest / intent score {lead.intent_score} (+{pv_pts:.1f})")

    total = sum(f["points"] for f in factors)
    score = int(round(_clamp(total, 0, 100)))
    if score >= 75:
        cls = "hot"
    elif score >= 50:
        cls = "warm"
    else:
        cls = "cold"
    probability = round(_clamp(score / 100.0 * 0.55 + (0.10 if cls == "hot" else 0.05 if cls == "warm" else 0.0)), 2)

    return ScoreResult(score=score, classification=cls,
                       conversion_probability=probability, factors=factors)

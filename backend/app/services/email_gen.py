"""AI email generation with provider abstraction.

Provider is selected from environment: if OPENAI_API_KEY + OPENAI_BASE_URL
are configured, uses the OpenAI-compatible endpoint; otherwise falls back
to a high-quality deterministic personalization engine (demo mode) so the
full workflow always works. Never hardcodes secrets.
"""
import random

from ..config import AI_PROVIDER, OPENAI_BASE_URL

TONES = ("professional", "friendly", "concise", "consultative")
LENGTHS = ("short", "medium", "detailed")


def _pain_phrase(lead):
    pp = (lead.pain_point or "").strip().rstrip(".")
    return pp or "growing your pipeline efficiently"


def _timeline_phrase(lead):
    t = (lead.buying_timeline or "").lower()
    return {
        "immediate": "with your timeline being immediate",
        "this quarter": "with an evaluation planned this quarter",
        "quarter": "with an evaluation planned this quarter",
        "6 months": "with a decision expected in about six months",
        "half_year": "with a decision expected in about six months",
        "1 year": "with a decision horizon of about a year",
        "year": "with a decision horizon of about a year",
    }.get(t, "")


def _engagement_hook(lead, events):
    counts = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
    if counts.get("demo_requested"):
        return "Since you asked about a demo, I wanted to make that as easy as possible."
    if counts.get("reply"):
        return "Thank you for replying earlier — based on what you shared, I think there's a concrete fit."
    if counts.get("link_clicked"):
        return "I noticed you explored the materials we sent — happy to go deeper on any of it."
    if counts.get("pricing_page_visit") or lead.intent_score > 20:
        return "I saw you've been evaluating options on our pricing page."
    if counts.get("opened"):
        return "Since our last note landed in your inbox, I wanted to share something more specific."
    return ""


def _demo_generate(lead, tone: str, length: str, events) -> dict:
    """Deterministic, genuinely personalized fallback generator."""
    first = lead.name.split(" ")[0] if lead.name else "there"
    company = lead.company_name or "your company"
    pain = _pain_phrase(lead)
    hook = _engagement_hook(lead, events)
    timeline = _timeline_phrase(lead)
    industry = lead.industry or "your industry"

    openers = {
        "professional": f"Hi {first},\n\nI'm reaching out because teams in {industry} like {company} are increasingly looking for a better way to handle {pain}.",
        "friendly": f"Hi {first},\n\nHope your week is going well! I came across {company} and was genuinely impressed — and I couldn't help noticing how common {pain} has become for {industry} teams.",
        "concise": f"Hi {first},\n\nQuick one: {company} and {pain} — is that on your plate right now?",
        "consultative": f"Hi {first},\n\nMost {industry} leaders I speak with at companies like {company} describe {pain} as a structural problem, not a people problem. Usually the fix is process and tooling, not headcount.",
    }
    value_props = {
        "professional": f"SalesPilot AI scores every lead on real buying signals, drafts personalized outreach automatically, and forecasts which deals will close — so your team spends time on the leads most likely to convert.",
        "friendly": f"Our platform does the heavy lifting: it ranks your leads by genuine intent, writes the first draft of every outreach email for you, and even predicts which deals are worth pushing. Reps just review and hit send.",
        "concise": f"SalesPilot AI: AI lead scoring + auto-drafted personalized emails + deal forecasting. Less guessing, more closing.",
        "consultative": f"Here's the pattern we see: scoring leads by actual engagement (replies, pricing visits, demo requests) — not gut feel — typically lifts reply rates 30-40% within a quarter. That's exactly what SalesPilot AI automates, along with personalized first-draft outreach and deal-level forecasting.",
    }
    if hook:
        value_props = {k: hook + " " + v for k, v in value_props.items()}

    timeline_bits = {
        "professional": (f"Given {timeline or 'your evaluation timeline'}, " if (timeline or True) else ""),
        "friendly": "",
        "concise": "",
        "consultative": "",
    }
    ctas = {
        "short": "Worth a 15-minute look?",
        "medium": f"Would a 15-minute walkthrough next week be useful? I can tailor it to {industry} use cases.",
        "detailed": f"If this resonates, I'd suggest a 20-minute working session: we'd map your current lead process, show how scoring would rank your existing pipeline, and quantify the follow-up time it saves. Shall I send over a couple of times?",
    }

    if length == "short":
        body = f"{openers[tone]}\n\n{value_props[tone].split('.')[0]}.\n\n{ctas['short']}\n\nBest,\nAlex Morgan\nSalesPilot AI"
    elif length == "detailed":
        extra = f"\n\nA bit more context: we currently help teams in {industry} cut follow-up time by half while increasing reply rates. {timeline}" if timeline else f"\n\nA bit more context: we currently help teams in {industry} cut follow-up time by half while increasing reply rates."
        body = f"{openers[tone]}\n\n{value_props[tone]}{extra}\n\n{ctas['detailed']}\n\nBest regards,\nAlex Morgan\nSalesPilot AI | alex@salespilot.ai"
    else:
        body = f"{openers[tone]}\n\n{value_props[tone]}\n\n{ctas['medium']}\n\nBest,\nAlex Morgan\nSalesPilot AI"

    subjects = {
        "professional": f"{company} + SalesPilot AI: a data-driven approach to {pain.split(',')[0][:40]}",
        "friendly": f"Idea for {company}, {first}",
        "concise": f"{pain.split(',')[0][:45]} — quick question",
        "consultative": f"How {industry} teams solve {pain.split(',')[0][:40]}",
    }
    if hook:
        subjects["professional"] = f"Following up: {company} + SalesPilot AI"
        subjects["consultative"] = f"Re: your interest in SalesPilot AI"

    return {"subject": subjects[tone], "body": body}


def _openai_generate(lead, tone: str, length: str, events) -> dict:
    """Generate via the OpenAI-compatible gateway configured by the platform."""
    from openai import OpenAI
    hook = _engagement_hook(lead, events)
    events_summary = ", ".join(f"{e.event_type}({e.occurred_at:%b %d})" for e in events[-6:])
    prompt = f"""Write a sales outreach email.

Lead: {lead.name}, {lead.job_title or 'unknown role'} at {lead.company_name or 'unknown company'} ({lead.industry or 'unknown industry'}, size {lead.company_size or 'unknown'}).
Pain point: {lead.pain_point or 'not stated'}.
Buying timeline: {lead.buying_timeline or 'unknown'}. Declared budget: ${float(lead.budget or 0):,.0f}.
Prior engagement with us: {events_summary or 'none yet'}. {hook}
Product: SalesPilot AI — AI lead scoring, personalized outreach drafting, pipeline forecasting for B2B sales teams.
Tone: {tone}. Length: {length} (short=under 60 words, medium=60-120, detailed=150-250).
Requirements: address the lead by first name, reference their company/role/industry/pain point concretely, reference prior engagement if any, end with one clear CTA, sign as Alex Morgan from SalesPilot AI.

Return JSON: {{"subject": "...", "body": "..."}}"""
    client = OpenAI(base_url=OPENAI_BASE_URL)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.9,
    )
    import json
    data = json.loads(resp.choices[0].message.content)
    return {"subject": data.get("subject", ""), "body": data.get("body", "")}


def generate_email(lead, tone: str = "professional", length: str = "medium", events=None) -> dict:
    events = events if events is not None else []
    if tone not in TONES:
        tone = "professional"
    if length not in LENGTHS:
        length = "medium"
    if AI_PROVIDER == "openai":
        try:
            out = _openai_generate(lead, tone, length, events)
            out["generated_by"] = "openai"
            return out
        except Exception:
            pass  # graceful fallback to demo mode
    out = _demo_generate(lead, tone, length, events)
    out["generated_by"] = "demo"
    return out

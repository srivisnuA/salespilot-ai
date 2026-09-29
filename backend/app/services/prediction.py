"""Deal win-probability prediction with explainable factors.

Heuristic, explainable model: stage baseline + lead score + engagement
intensity/recency + deal age. No fabricated accuracy claims — this is a
transparent rules model, architected for an ML backend swap.
"""
import datetime as dt

STAGE_BASE = {
    "NEW": 5, "QUALIFIED": 15, "CONTACTED": 25, "ENGAGED": 40,
    "DEMO": 55, "NEGOTIATION": 70, "WON": 100, "LOST": 0,
}

RISK_THRESHOLDS = (35, 60)  # < low bound = high risk? inverted below


def predict_deal(deal, lead=None, now=None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    lead = lead or deal.lead
    factors_pos, factors_neg = [], []

    base = STAGE_BASE.get(deal.stage, 10)
    prob = float(base)
    factors_pos.append({
        "factor": f"Stage: {deal.stage}", "impact": round(base, 1),
        "explanation": f"Deals at {deal.stage} historically convert at a {base}% baseline.",
    })

    score = lead.score if lead else 50
    score_adj = (score - 50) * 0.3  # -15..+15
    prob += score_adj
    (factors_pos if score_adj >= 0 else factors_neg).append({
        "factor": f"Lead score: {score}", "impact": round(score_adj, 1),
        "explanation": f"A lead score of {score}/100 {'adds' if score_adj >= 0 else 'subtracts'} {abs(round(score_adj,1))} points.",
    })

    events = lead.engagement_events if lead else []
    counts = {}
    latest = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
        latest[e.event_type] = e.occurred_at

    reply_adj = min(counts.get("reply", 0), 2) * 5
    if reply_adj:
        prob += reply_adj
        factors_pos.append({"factor": f"Replies: {counts.get('reply',0)}", "impact": reply_adj,
                            "explanation": "Direct replies are one of the strongest buying signals."})
    demo_adj = 8 if (counts.get("demo_requested") or counts.get("meeting_booked")) else 0
    if demo_adj:
        prob += demo_adj
        factors_pos.append({"factor": "Demo / meeting requested", "impact": demo_adj,
                            "explanation": "Explicit interest signals materially raise close likelihood."})
    click_adj = min(counts.get("link_clicked", 0), 2) * 2.5
    if click_adj:
        prob += click_adj
        factors_pos.append({"factor": f"Link clicks: {counts.get('link_clicked',0)}", "impact": click_adj,
                            "explanation": "Active content engagement indicates evaluation."})

    # Staleness: no engagement in 10+ days
    last_any = max(latest.values()) if latest else None
    if last_any and last_any.tzinfo is None:
        last_any = last_any.replace(tzinfo=dt.timezone.utc)
    if last_any:
        days_idle = (now - last_any).days
        if days_idle >= 10:
            idle_adj = -min(15.0, (days_idle - 9) * 2.0)
            prob += idle_adj
            factors_neg.append({"factor": f"Stale: {days_idle} days since last engagement", "impact": idle_adj,
                                "explanation": "Deals with no activity for 10+ days slip at a much higher rate."})

    # Deal age beyond 90 days
    created = deal.created_at.replace(tzinfo=dt.timezone.utc) if deal.created_at and deal.created_at.tzinfo is None else deal.created_at
    age_days = (now - created).days if created else 0
    if age_days > 90:
        age_adj = -min(10.0, (age_days - 90) / 10.0)
        prob += age_adj
        factors_neg.append({"factor": f"Deal age: {age_days} days", "impact": round(age_adj,1),
                            "explanation": "Long-running deals lose momentum."})

    if deal.value and float(deal.value) > 80000:
        prob -= 5
        factors_neg.append({"factor": f"Large deal value: ${float(deal.value):,.0f}", "impact": -5,
                            "explanation": "Larger deals involve more stakeholders and longer approval cycles."})

    if (deal.expected_close_date or dt.date.max) < now.date() and deal.stage not in ("WON", "LOST"):
        prob -= 4
        factors_neg.append({"factor": "Expected close date passed", "impact": -4,
                            "explanation": "Overdue deals are at elevated risk of stalling."})

    prob = max(2.0, min(97.0, prob))
    if deal.stage == "WON":
        prob = 100.0
    elif deal.stage == "LOST":
        prob = 0.0

    if prob >= 60:
        risk = "low"
    elif prob >= 35:
        risk = "medium"
    else:
        risk = "high"

    expected = round(float(deal.value or 0) * prob / 100.0, 2)
    return {
        "win_probability": round(prob, 1),
        "expected_revenue": expected,
        "risk_level": risk,
        "positive_factors": factors_pos,
        "negative_factors": factors_neg,
    }

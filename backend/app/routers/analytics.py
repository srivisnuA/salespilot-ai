import datetime as dt
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (Lead, EmailMessage, EngagementEvent, Deal, Activity,
                      Campaign, AutomationRun, Task)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _rates(db: Session):
    sent = db.query(EngagementEvent).filter(EngagementEvent.event_type == "sent").count()
    delivered = db.query(EngagementEvent).filter(EngagementEvent.event_type == "delivered").count()
    opened = db.query(EngagementEvent).filter(EngagementEvent.event_type == "opened").count()
    clicked = db.query(EngagementEvent).filter(EngagementEvent.event_type == "link_clicked").count()
    replied = db.query(EngagementEvent).filter(EngagementEvent.event_type == "reply").count()
    demoed = db.query(EngagementEvent).filter(EngagementEvent.event_type.in_(["demo_requested", "meeting_booked"])).count()
    pct = lambda n: round(100 * n / sent, 1) if sent else 0
    return {"emails_sent": sent, "open_rate": pct(opened), "click_rate": pct(clicked),
            "reply_rate": pct(replied), "demo_rate": pct(demoed),
            "opens": opened, "clicks": clicked, "replies": replied}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    hot = db.query(Lead).filter(Lead.classification == "hot").count()
    warm = db.query(Lead).filter(Lead.classification == "warm").count()
    cold = db.query(Lead).filter(Lead.classification == "cold").count()
    avg_score = db.query(func.avg(Lead.score)).scalar() or 0
    conv = db.query(Lead).filter(Lead.status == "converted").count()  # via deals WON
    won_leads = db.query(Deal).filter(Deal.stage == "WON").count()
    conversion_rate = round(100 * won_leads / total, 1) if total else 0

    rates = _rates(db)

    open_deals = db.query(Deal).filter(~Deal.stage.in_(["WON", "LOST"])).all()
    pipeline_value = sum(float(d.value) for d in open_deals)
    predicted = sum(float(d.expected_revenue or 0) for d in open_deals)
    won = db.query(Deal).filter(Deal.stage == "WON").all()
    won_value = sum(float(d.value) for d in won)

    # Funnel counts (leads having deals per stage ever, from stage history + current)
    funnel_order = ["NEW", "QUALIFIED", "CONTACTED", "ENGAGED", "DEMO", "NEGOTIATION", "WON"]
    funnel = []
    from ..models import StageHistory
    for i, stage in enumerate(funnel_order):
        if i == 0:
            count = total
        else:
            count = db.query(StageHistory).filter(StageHistory.to_stage == stage).count()
        funnel.append({"stage": stage.title(), "count": count})

    # Revenue forecast: next 6 months from expected close dates
    forecast = defaultdict(float)
    today = dt.date.today()
    for d in open_deals:
        close = d.expected_close_date or (today + dt.timedelta(days=30))
        key = close.strftime("%Y-%m")
        forecast[key] += float(d.expected_revenue or 0)
    months = []
    cur = today.replace(day=1)
    for _ in range(6):
        key = cur.strftime("%Y-%m")
        months.append({"month": key, "predicted": round(forecast.get(key, 0), 2)})
        cur = (cur + dt.timedelta(days=32)).replace(day=1)

    recent = db.query(Activity).order_by(Activity.created_at.desc()).limit(15).all()
    activities = [{"id": a.id, "type": a.type, "message": a.message,
                   "created_at": a.created_at.isoformat(),
                   "lead_id": a.lead_id} for a in recent]

    high_intent = db.query(Lead).filter(~Lead.deals.any(Deal.stage.in_(["WON", "LOST"]))) \
        .order_by(Lead.score.desc()).limit(6).all()
    high_intent_out = [{"id": l.id, "name": l.name, "company": l.company_name,
                        "score": l.score, "classification": l.classification} for l in high_intent]

    return {
        "total_leads": total, "hot": hot, "warm": warm, "cold": cold,
        "avg_score": round(float(avg_score), 1),
        **rates,
        "conversion_rate": conversion_rate,
        "pipeline_value": round(pipeline_value, 2),
        "predicted_revenue": round(predicted, 2),
        "won_revenue": round(won_value, 2),
        "open_deals": len(open_deals),
        "funnel": funnel,
        "forecast": months,
        "recent_activity": activities,
        "high_intent_leads": high_intent_out,
    }


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    # Sources
    sources = db.query(Lead.source, func.count(Lead.id)).group_by(Lead.source).all()
    sources_out = [{"source": s or "unknown", "count": c} for s, c in sources]

    # Score distribution
    buckets = [(0, 20, "0-20"), (20, 40, "20-40"), (40, 50, "40-50"), (50, 75, "50-75"),
               (75, 90, "75-90"), (90, 101, "90-100")]
    dist = []
    for lo, hi, label in buckets:
        c = db.query(Lead).filter(Lead.score >= lo, Lead.score < hi).count()
        dist.append({"bucket": label, "count": c})

    # Industry performance
    inds = db.query(Lead.industry, func.count(Lead.id), func.avg(Lead.score)).group_by(Lead.industry).all()
    industry_out = []
    for name, cnt, avg in inds:
        won = db.query(Deal).join(Lead).filter(Lead.industry == name, Deal.stage == "WON").count()
        industry_out.append({"industry": name or "unknown", "leads": cnt,
                             "avg_score": round(float(avg or 0), 1), "won": won})

    email_rates = _rates(db)

    # Funnel conversion
    from ..models import StageHistory
    funnel_order = ["NEW", "QUALIFIED", "CONTACTED", "ENGAGED", "DEMO", "NEGOTIATION", "WON"]
    total = db.query(Lead).count()
    funnel = []
    for i, stage in enumerate(funnel_order):
        count = total if i == 0 else db.query(StageHistory).filter(StageHistory.to_stage == stage).count()
        funnel.append({"stage": stage.title(), "count": count})
    conv = []
    for i in range(1, len(funnel)):
        prev, curr = funnel[i - 1]["count"], funnel[i]["count"]
        conv.append({"from": funnel[i - 1]["stage"], "to": funnel[i]["stage"],
                     "rate": round(100 * curr / prev, 1) if prev else 0})

    # Win/loss
    won = db.query(Deal).filter(Deal.stage == "WON").count()
    lost = db.query(Deal).filter(Deal.stage == "LOST").count()
    closed = won + lost
    win_rate = round(100 * won / closed, 1) if closed else 0
    loss_rate = round(100 * lost / closed, 1) if closed else 0

    # Deal values
    won_deals = db.query(Deal).filter(Deal.stage == "WON").all()
    all_deals = db.query(Deal).all()
    avg_deal = round(sum(float(d.value) for d in won_deals) / won, 2) if won else 0

    # Sales cycle: avg days created->closed for WON deals
    cycles = [(d.closed_at - d.created_at).days for d in won_deals
              if d.closed_at and d.created_at]
    sales_cycle = round(sum(cycles) / len(cycles), 1) if cycles else 0

    # Pipeline velocity = (open deals * avg deal value * win rate) / cycle length
    open_deals = [d for d in all_deals if d.stage not in ("WON", "LOST")]
    open_value = sum(float(d.value) for d in open_deals)
    weighted = sum(float(d.expected_revenue or 0) for d in open_deals)
    velocity = round((len(open_deals) * avg_deal * win_rate / 100.0) / max(sales_cycle, 1), 2) if sales_cycle else 0

    # ROI per campaign: revenue from WON deals whose lead's emails belong to campaign
    campaigns = db.query(Campaign).all()
    roi_out = []
    total_cost = 0.0
    total_rev = 0.0
    for c in campaigns:
        revenue = 0.0
        for d in won_deals:
            ems = db.query(EmailMessage).filter(EmailMessage.lead_id == d.lead_id,
                                                EmailMessage.campaign_id == c.id).count()
            if ems:
                revenue += float(d.value)
        cost = float(c.cost)
        total_cost += cost
        total_rev += revenue
        roi = round(((revenue - cost) / cost) * 100, 1) if cost else None
        roi_out.append({"id": c.id, "name": c.name, "channel": c.channel, "cost": cost,
                        "revenue": round(revenue, 2), "roi": roi})

    overall_roi = round(((total_rev - total_cost) / total_cost) * 100, 1) if total_cost else None

    return {
        "sources": sources_out,
        "score_distribution": dist,
        "industry_performance": industry_out,
        "email": email_rates,
        "funnel": funnel,
        "funnel_conversion": conv,
        "win_rate": win_rate, "loss_rate": loss_rate,
        "avg_deal_value": avg_deal,
        "sales_cycle_days": sales_cycle,
        "pipeline_velocity": velocity,
        "won_revenue": round(sum(float(d.value) for d in won_deals), 2),
        "open_pipeline": round(open_value, 2),
        "weighted_pipeline": round(weighted, 2),
        "predicted_revenue": round(weighted, 2),
        "campaigns_roi": roi_out,
        "total_campaign_cost": round(total_cost, 2),
        "total_campaign_revenue": round(total_rev, 2),
        "overall_roi": overall_roi,
    }

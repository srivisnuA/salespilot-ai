"""Idempotent demo seed: 60+ leads across 6 industries, campaigns, emails,
engagement events, deals, automations, tasks, activities, predictions."""
import datetime as dt
import random

from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models
from .services.scoring import score_lead
from .services.email_gen import generate_email
from .services.score_service import recompute_lead_score
from .services.prediction import predict_deal

random.seed(42)

INDUSTRIES = ["SaaS", "FinTech", "Healthcare", "E-commerce", "Manufacturing", "Technology"]
SIZES = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
SOURCES = ["website", "referral", "linkedin", "webinar", "cold_outreach", "inbound", "event", "partner"]
TIMELINES = ["immediate", "this quarter", "6 months", "1 year", "unknown"]
FIRST = ["Sarah", "James", "Priya", "Michael", "Elena", "David", "Aisha", "Tom", "Lucia", "Marcus",
         "Nina", "Robert", "Grace", "Daniel", "Olivia", "Kevin", "Hannah", "Victor", "Sofia", "Brian",
         "Amara", "Chris", "Mei", "Juan", "Laura", "Omar", "Emily", "Raj", "Kate", "Andrei"]
LAST = ["Chen", "Patel", "Johnson", "Garcia", "Kim", "Okafor", "Mueller", "Rossi", "Silva", "Novak",
        "Ahmed", "Thompson", "Lee", "Martinez", "Singh", "Brown", "Kowalski", "Dubois", "Yamada", "Ivanov"]
TITLES = ["CEO", "VP Sales", "Head of Revenue", "Sales Director", "CRO", "Marketing Manager",
          "Founder", "VP Marketing", "Head of Growth", "Sales Manager", "COO", "Director of Operations"]
PAINS = {
    "SaaS": "reps spend hours manually qualifying leads and follow-ups slip through the cracks",
    "FinTech": "compliance-heavy sales cycles make manual follow-up unmanageable",
    "Healthcare": "long procurement cycles and no visibility into which accounts are actually engaged",
    "E-commerce": "high lead volume from multiple channels with no consistent prioritization",
    "Manufacturing": "deal data lives in spreadsheets so forecasts are always wrong",
    "Technology": "marketing generates leads but sales can't tell hot from cold",
}
COMPANY_NAMES = {
    "SaaS": ["Cloudstack", "Flowdesk", "IterateLabs", "Signalbox", "Quantly", "Dispatchly", "Railyard"],
    "FinTech": ["LedgerPay", "Vaultline", "Clearance", "MintRoute", "PayBasis", "Auditly"],
    "Healthcare": ["MediCore", "CareBridge", "ClinIQ", "HealthOrbit", "VitalPath", "Remedy Labs"],
    "E-commerce": ["Shoplytics", "Cartwheel", "MerchantOne", "BrightCart", "Orderly", "RetailSense"],
    "Manufacturing": ["ForgeLine", "NordicParts", "Assembly IQ", "MetalWorks Co", "PrecisionCast"],
    "Technology": ["Datacove", "Nexatek", "Bitforge", "Corelink", "Syntara", "Hexawave"],
}


def days_ago(n, hour=None):
    d = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=n)
    if hour is not None:
        d = d.replace(hour=hour, minute=random.randint(0, 59))
    return d


def seed(db: Session):
    if db.query(models.Lead).count() > 0:
        return False  # already seeded

    campaigns = [
        models.Campaign(name="Q3 Outbound — SaaS", channel="email", cost=5200, status="active"),
        models.Campaign(name="FinTech Webinar Series", channel="webinar", cost=8400, status="active"),
        models.Campaign(name="Healthcare Conference 2026", channel="event", cost=15000, status="active"),
        models.Campaign(name="E-commerce Inbound Content", channel="content", cost=3800, status="active"),
        models.Campaign(name="Manufacturing Cold Outreach", channel="email", cost=2600, status="active"),
        models.Campaign(name="Tech Partner Referrals", channel="partner", cost=4100, status="active"),
    ]
    db.add_all(campaigns)
    db.flush()

    automations = [
        models.Automation(
            name="Hot lead outreach",
            description="IF lead score > 75 THEN generate personalized outreach and create a follow-up task.",
            trigger_type="score_above_threshold", conditions={"threshold": 75},
            actions=[{"type": "generate_outreach_email"}, {"type": "create_followup_task", "days": 1}]),
        models.Automation(
            name="Multiple email opens → intent boost",
            description="IF an email is opened multiple times THEN increase intent score and notify the sales rep.",
            trigger_type="email_opened_multiple", conditions={"opens": 2},
            actions=[{"type": "increase_intent_score", "amount": 10}, {"type": "notify_rep"}]),
        models.Automation(
            name="No response follow-up",
            description="IF no response for 5 days after an email THEN create a follow-up.",
            trigger_type="no_response_days", conditions={"days": 5},
            actions=[{"type": "create_followup_task", "days": 0}]),
        models.Automation(
            name="Demo request routing",
            description="IF demo requested THEN move lead to DEMO stage and create a task.",
            trigger_type="demo_requested", conditions={},
            actions=[{"type": "move_to_stage", "stage": "DEMO"}, {"type": "create_followup_task", "days": 1}]),
    ]
    db.add_all(automations)

    leads = []
    for i in range(64):
        industry = INDUSTRIES[i % len(INDUSTRIES)]
        company = random.choice(COMPANY_NAMES[industry])
        first, last = random.choice(FIRST), random.choice(LAST)
        title = random.choice(TITLES + ["VP Sales", "CEO", "CRO", "Head of Growth"])
        source = random.choice(SOURCES)
        timeline = random.choice(TIMELINES + ["immediate", "this quarter"])
        budget = random.choice([0, 8000, 15000, 25000, 40000, 60000, 85000, 120000, 100000, 60000, 85000])
        company_size = random.choice(SIZES)
        revenue = random.choice([500000, 1200000, 4000000, 12000000, 45000000, 120000000])
        lead = models.Lead(
            name=f"{first} {last}",
            email=f"{first.lower()}.{last.lower()}@{company.lower().replace(' ', '').replace('.', '')}.com",
            company_name=company, job_title=title, industry=industry,
            company_size=company_size, annual_revenue=revenue, source=source,
            budget=budget, buying_timeline=timeline,
            pain_point=PAINS[industry],
            notes=random.choice(["", "Met at conference, interested.", "Referred by existing customer.",
                                 "Downloaded our benchmark report.", "Asked about enterprise pricing."]),
            created_at=days_ago(random.randint(1, 90)),
        )
        db.add(lead)
        leads.append(lead)
    db.flush()

    event_types_pool = ["sent", "delivered", "opened", "opened", "link_clicked", "reply",
                        "website_visit", "pricing_page_visit", "demo_requested", "meeting_booked",
                        "follow_up_completed"]

    for idx, lead in enumerate(leads):
        # engagement richness varies by lead
        richness = random.random()
        n_events = 2 if richness < 0.3 else (6 if richness < 0.75 else 11)
        if richness >= 0.75:
            chosen = list(dict.fromkeys(["reply", "demo_requested"] + random.sample(event_types_pool, 8)))
        chosen = random.sample(event_types_pool, min(n_events, len(event_types_pool)))
        # a sent+delivered pair usually comes first
        if "sent" not in chosen and richness > 0.2:
            chosen = ["sent", "delivered"] + chosen[: max(0, n_events - 2)]
        emails_for_lead = 0
        for j, et in enumerate(chosen):
            email_id = None
            if et in ("sent", "delivered", "opened", "link_clicked", "reply"):
                if emails_for_lead == 0:
                    tone, length = random.choice(["professional", "friendly", "concise", "consultative"]), "medium"
                    gen = generate_email(lead, tone, length, [])
                    em = models.EmailMessage(
                        lead_id=lead.id, campaign_id=random.choice(campaigns).id,
                        subject=gen["subject"], body=gen["body"], tone=tone, length=length,
                        status="sent", generated_by="demo", created_at=days_ago(40 - j * 2),
                        sent_at=days_ago(40 - j * 2))
                    db.add(em)
                    db.flush()
                    email_id = em.id
                    emails_for_lead += 1
                else:
                    email_id = db.query(models.EmailMessage.id).filter_by(lead_id=lead.id).first()[0]
            db.add(models.EngagementEvent(
                lead_id=lead.id, email_id=email_id, event_type=et,
                occurred_at=days_ago(random.randint(0, 35), hour=random.randint(8, 20))))
        db.flush()
        recompute_lead_score(db, lead, reason="seed")

        # deals for a subset
        if idx % 2 == 0:
            stage = random.choice(["NEW", "QUALIFIED", "CONTACTED", "ENGAGED", "DEMO", "NEGOTIATION",
                                   "WON", "WON", "LOST"])
            value = float(random.choice([8000, 15000, 24000, 40000, 65000, 90000, 140000]))
            deal = models.Deal(
                lead_id=lead.id, name=f"{lead.company_name} — SalesPilot AI",
                stage=stage, value=value,
                expected_close_date=dt.date.today() + dt.timedelta(days=random.randint(-20, 90)),
                created_at=days_ago(random.randint(10, 120)),
            )
            db.add(deal)
            db.flush()
            pred = predict_deal(deal, lead)
            deal.win_probability = pred["win_probability"]
            deal.expected_revenue = pred["expected_revenue"]
            deal.risk_level = pred["risk_level"]
            db.add(models.Prediction(
                deal_id=deal.id, win_probability=pred["win_probability"],
                expected_revenue=pred["expected_revenue"], risk_level=pred["risk_level"],
                positive_factors=pred["positive_factors"], negative_factors=pred["negative_factors"]))
            history = []
            order = ["NEW", "QUALIFIED", "CONTACTED", "ENGAGED", "DEMO", "NEGOTIATION", "WON"]
            if stage in order:
                path = order[: order.index(stage) + 1]
            else:
                path = order[: 3] + [stage]
            for k in range(1, len(path)):
                db.add(models.StageHistory(
                    deal_id=deal.id, from_stage=path[k - 1], to_stage=path[k],
                    changed_at=days_ago(random.randint(1, 60))))
        db.add(models.Activity(lead_id=lead.id, type="system",
                               message="Lead imported and scored by SalesPilot AI",
                               created_at=lead.created_at))

    db.commit()
    return True


def run_seed():
    db = SessionLocal()
    try:
        return seed(db)
    finally:
        db.close()

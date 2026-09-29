import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import EmailMessage, EngagementEvent, Activity, Lead, Campaign
from ..schemas import EmailOut
from ..services.email_gen import generate_email, TONES, LENGTHS
from ..services.score_service import recompute_lead_score

router = APIRouter(prefix="/api/emails", tags=["emails"])

EVENT_TYPES = ("sent", "delivered", "opened", "link_clicked", "reply",
               "demo_requested", "meeting_booked", "follow_up_completed")


class GenerateRequest(BaseModel):
    lead_id: int
    tone: str = "professional"
    length: str = "medium"
    campaign_id: int | None = None


class UpdateEmailRequest(BaseModel):
    subject: str | None = None
    body: str | None = None
    tone: str | None = None
    length: str | None = None
    status: str | None = None


class EngagementRequest(BaseModel):
    event_type: str
    email_id: int | None = None


@router.get("")
def list_emails(db: Session = Depends(get_db), status: str = "", lead_id: int | None = None):
    query = db.query(EmailMessage).options(joinedload(EmailMessage.lead))
    if status:
        query = query.filter(EmailMessage.status == status)
    if lead_id:
        query = query.filter(EmailMessage.lead_id == lead_id)
    rows = query.order_by(EmailMessage.created_at.desc()).limit(300).all()
    out = []
    for e in rows:
        d = EmailOut.model_validate(e).model_dump()
        d["lead_name"] = e.lead.name if e.lead else ""
        d["lead_company"] = e.lead.company_name if e.lead else ""
        counts = {}
        for ev in e.lead.engagement_events if e.lead else []:
            counts[ev.event_type] = counts.get(ev.event_type, 0) + 1
        d["opens"] = counts.get("opened", 0)
        d["clicks"] = counts.get("link_clicked", 0)
        d["replied"] = counts.get("reply", 0) > 0
        out.append(d)
    return {"items": out}


@router.post("/generate")
def generate(payload: GenerateRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    events = db.query(EngagementEvent).filter(EngagementEvent.lead_id == lead.id).all()
    gen = generate_email(lead, payload.tone, payload.length, events)
    em = EmailMessage(
        lead_id=lead.id, campaign_id=payload.campaign_id,
        subject=gen["subject"], body=gen["body"], tone=payload.tone, length=payload.length,
        status="draft", generated_by=gen.get("generated_by", "demo"))
    db.add(em)
    db.add(Activity(lead_id=lead.id, type="email",
                    message=f"AI generated a {payload.tone}/{payload.length} outreach email draft"))
    db.commit()
    db.refresh(em)
    return EmailOut.model_validate(em).model_dump()


@router.patch("/{email_id}")
def update_email(email_id: int, payload: UpdateEmailRequest, db: Session = Depends(get_db)):
    em = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if not em:
        raise HTTPException(404, "Email not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") and data["status"] not in ("draft", "approved", "sent"):
        raise HTTPException(422, "Invalid status")
    for k, v in data.items():
        setattr(em, k, v)
    db.commit()
    db.refresh(em)
    return EmailOut.model_validate(em).model_dump()


@router.post("/{email_id}/send")
def send_email(email_id: int, db: Session = Depends(get_db)):
    """Simulate send: marks sent, records sent+delivered engagement, re-scores."""
    em = db.query(EmailMessage).options(joinedload(EmailMessage.lead)).filter(EmailMessage.id == email_id).first()
    if not em:
        raise HTTPException(404, "Email not found")
    if em.status == "sent":
        raise HTTPException(409, "Email already sent")
    em.status = "sent"
    em.sent_at = dt.datetime.now(dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    db.add(EngagementEvent(lead_id=em.lead_id, email_id=em.id, event_type="sent", occurred_at=now))
    db.add(EngagementEvent(lead_id=em.lead_id, email_id=em.id, event_type="delivered", occurred_at=now))
    db.add(Activity(lead_id=em.lead_id, type="email",
                    message=f"Outreach email sent: \"{em.subject}\""))
    if em.lead:
        recompute_lead_score(db, em.lead, reason="engagement")
    db.commit()
    from .automations import evaluate_for_lead
    evaluate_for_lead(db, em.lead, event_type="sent")
    return EmailOut.model_validate(em).model_dump()


@router.post("/{email_id}/engagement")
def record_engagement(email_id: int, payload: EngagementRequest, db: Session = Depends(get_db)):
    if payload.event_type not in EVENT_TYPES:
        raise HTTPException(422, f"event_type must be one of {EVENT_TYPES}")
    em = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if not em:
        raise HTTPException(404, "Email not found")
    return _record(db, em.lead_id, payload.event_type, em.id)


def _record(db: Session, lead_id: int, event_type: str, email_id: int | None):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    old = lead.score
    ev = EngagementEvent(lead_id=lead_id, email_id=email_id, event_type=event_type)
    db.add(ev)
    db.add(Activity(lead_id=lead_id, type="engagement",
                    message=f"Engagement recorded: {event_type.replace('_', ' ')}"))
    recompute_lead_score(db, lead, reason="engagement")
    db.commit()
    db.refresh(lead)
    # Run automation engine for this lead after engagement/score change
    from .automations import evaluate_for_lead
    evaluate_for_lead(db, lead, event_type=event_type)
    return {"ok": True, "lead_id": lead_id, "event_type": event_type,
            "old_score": old, "new_score": lead.score,
            "classification": lead.classification}


@router.post("/leads/{lead_id}/engagement")
def record_lead_engagement(lead_id: int, payload: EngagementRequest, db: Session = Depends(get_db)):
    if payload.event_type not in EVENT_TYPES:
        raise HTTPException(422, f"event_type must be one of {EVENT_TYPES}")
    return _record(db, lead_id, payload.event_type, payload.email_id)


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    out = []
    for c in campaigns:
        emails = db.query(EmailMessage).filter(EmailMessage.campaign_id == c.id, EmailMessage.status == "sent").count()
        leads = db.query(Lead).filter(Lead.source.in_(["website", "inbound", "referral", "event", "webinar", "partner", "linkedin", "cold_outreach"])).count()
        out.append({
            "id": c.id, "name": c.name, "channel": c.channel, "cost": float(c.cost),
            "status": c.status, "emails_sent": emails,
        })
    return {"items": out}

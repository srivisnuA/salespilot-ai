import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Lead, ScoreFactor, Activity, Company, EngagementEvent
from ..schemas import LeadCreate, LeadUpdate, LeadOut, LeadDetailOut
from ..services.score_service import recompute_lead_score

router = APIRouter(prefix="/api/leads", tags=["leads"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate(payload: LeadCreate | LeadUpdate):
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and not (data["name"] or "").strip():
        raise HTTPException(422, "Name is required")
    if "email" in data:
        if not (data["email"] or "").strip():
            raise HTTPException(422, "Email is required")
        if not EMAIL_RE.match(data["email"]):
            raise HTTPException(422, "Invalid email address")
    for numf in ("budget", "annual_revenue"):
        if numf in data and data[numf] is not None and data[numf] < 0:
            raise HTTPException(422, f"{numf} must be a non-negative number")
    return data


@router.get("")
def list_leads(
    db: Session = Depends(get_db),
    q: str = "",
    classification: str = "",
    industry: str = "",
    source: str = "",
    min_score: int | None = None,
    max_score: int | None = None,
    sort: str = "score",
    direction: str = "desc",
    page: int = 1,
    page_size: int = Query(25, le=100),
):
    query = db.query(Lead)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Lead.name.ilike(like), Lead.company_name.ilike(like), Lead.email.ilike(like)))
    if classification:
        query = query.filter(Lead.classification == classification)
    if industry:
        query = query.filter(Lead.industry == industry)
    if source:
        query = query.filter(Lead.source == source)
    if min_score is not None:
        query = query.filter(Lead.score >= min_score)
    if max_score is not None:
        query = query.filter(Lead.score <= max_score)

    sort_col = {
        "score": Lead.score, "name": Lead.name, "company": Lead.company_name,
        "created": Lead.created_at, "classification": Lead.classification,
    }.get(sort, Lead.score)
    query = query.order_by(desc(sort_col) if direction == "desc" else asc(sort_col))

    total = query.count()
    rows = query.options(joinedload(Lead.company)).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [LeadOut.model_validate(r).model_dump() for r in rows]}


@router.post("")
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    data = _validate(payload)
    lead = Lead(**{k: v for k, v in data.items() if hasattr(Lead, k)})
    db.add(lead)
    db.flush()
    recompute_lead_score(db, lead, reason="create")
    db.add(Activity(lead_id=lead.id, type="system", message="Lead created"))
    db.commit()
    db.refresh(lead)
    return LeadDetailOut.model_validate(lead).model_dump()


@router.get("/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).options(
        joinedload(Lead.score_factors), joinedload(Lead.activities),
        joinedload(Lead.emails), joinedload(Lead.engagement_events),
        joinedload(Lead.deals), joinedload(Lead.tasks),
    ).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return LeadDetailOut.model_validate(lead).model_dump()


@router.patch("/{lead_id}")
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    data = _validate(payload)
    for k, v in data.items():
        if hasattr(Lead, k):
            setattr(lead, k, v)
    recompute_lead_score(db, lead, reason="update")
    db.commit()
    db.refresh(lead)
    return LeadDetailOut.model_validate(lead).model_dump()


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    db.delete(lead)
    db.commit()
    return {"ok": True}


@router.get("/{lead_id}/score_explanation")
def score_explanation(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).options(joinedload(Lead.score_factors)).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {
        "score": lead.score,
        "classification": lead.classification,
        "conversion_probability": lead.conversion_probability,
        "factors": [dict(f) for f in (ScoreFactor.factor, )] if False else [
            {"factor": f.factor, "points": f.points, "max_points": f.max_points,
             "explanation": f.explanation, "kind": f.kind} for f in lead.score_factors],
    }

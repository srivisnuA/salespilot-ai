import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Deal, Lead, Prediction, StageHistory, Activity, EngagementEvent
from ..services.prediction import predict_deal

router = APIRouter(prefix="/api/deals", tags=["deals"])

STAGES = ["NEW", "QUALIFIED", "CONTACTED", "ENGAGED", "DEMO", "NEGOTIATION", "WON", "LOST"]


class DealCreate(BaseModel):
    lead_id: int
    name: str = ""
    value: float
    expected_close_date: dt.date | None = None


class DealUpdate(BaseModel):
    stage: str | None = None
    value: float | None = None
    name: str | None = None
    expected_close_date: dt.date | None = None


def _serialize(deal: Deal) -> dict:
    lead = deal.lead
    last_activity = None
    if lead:
        ev = db_last_activity(deal)
        last_activity = ev
    return {
        "id": deal.id, "name": deal.name, "stage": deal.stage, "value": float(deal.value),
        "win_probability": deal.win_probability, "expected_revenue": float(deal.expected_revenue),
        "risk_level": deal.risk_level, "expected_close_date": str(deal.expected_close_date) if deal.expected_close_date else None,
        "created_at": deal.created_at.isoformat(),
        "lead_id": deal.lead_id,
        "company": lead.company_name if lead else "",
        "contact": lead.name if lead else "",
        "lead_score": lead.score if lead else 0,
        "classification": lead.classification if lead else "",
        "last_activity": last_activity,
    }


def db_last_activity(deal: Deal):
    lead = deal.lead
    if not lead:
        return None
    events = sorted(lead.engagement_events, key=lambda e: e.occurred_at)
    if not events:
        return None
    last = events[-1]
    return {"type": last.event_type, "at": last.occurred_at.isoformat()}


@router.get("/stages")
def stages():
    return {"stages": STAGES}


@router.get("")
def list_deals(db: Session = Depends(get_db)):
    deals = db.query(Deal).options(joinedload(Deal.lead)).all()
    grouped = {s: [] for s in STAGES}
    for d in deals:
        grouped.setdefault(d.stage, []).append(_serialize(d))
    summary = {"open_value": 0.0, "weighted_value": 0.0, "won_value": 0.0, "counts": {}}
    for d in deals:
        summary["counts"][d.stage] = summary["counts"].get(d.stage, 0) + 1
        if d.stage in ("WON", "LOST"):
            if d.stage == "WON":
                summary["won_value"] += float(d.value)
        else:
            summary["open_value"] += float(d.value)
            summary["weighted_value"] += float(d.expected_revenue or 0)
    return {"columns": grouped, "summary": summary}


@router.post("")
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    if payload.value <= 0:
        raise HTTPException(422, "Deal value must be positive")
    deal = Deal(lead_id=lead.id, name=payload.name or f"{lead.company_name} — SalesPilot AI",
                value=payload.value, expected_close_date=payload.expected_close_date)
    db.add(deal)
    db.flush()
    apply_prediction(db, deal, lead)
    db.add(StageHistory(deal_id=deal.id, from_stage="", to_stage=deal.stage))
    db.add(Activity(lead_id=lead.id, type="stage", message=f"Deal created at stage {deal.stage}: ${payload.value:,.0f}"))
    db.commit()
    db.refresh(deal)
    return _serialize(deal)


def apply_prediction(db: Session, deal: Deal, lead: Lead):
    pred = predict_deal(deal, lead)
    deal.win_probability = pred["win_probability"]
    deal.expected_revenue = pred["expected_revenue"]
    deal.risk_level = pred["risk_level"]
    db.add(Prediction(deal_id=deal.id, win_probability=pred["win_probability"],
                      expected_revenue=pred["expected_revenue"], risk_level=pred["risk_level"],
                      positive_factors=pred["positive_factors"], negative_factors=pred["negative_factors"]))


@router.patch("/{deal_id}")
def update_deal(deal_id: int, payload: DealUpdate, db: Session = Depends(get_db)):
    deal = db.query(Deal).options(joinedload(Deal.lead)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    data = payload.model_dump(exclude_unset=True)
    if "stage" in data and data["stage"] not in STAGES:
        raise HTTPException(422, "Invalid stage")
    old_stage = deal.stage
    for k, v in data.items():
        setattr(deal, k, v)
    if deal.stage in ("WON", "LOST") and old_stage not in ("WON", "LOST"):
        deal.closed_at = dt.datetime.now(dt.timezone.utc)
    if old_stage != deal.stage:
        db.add(StageHistory(deal_id=deal.id, from_stage=old_stage, to_stage=deal.stage))
        if deal.lead:
            db.add(Activity(lead_id=deal.lead_id, type="stage",
                            message=f"Deal moved {old_stage} → {deal.stage}"))
        if deal.stage == "DEMO" and deal.lead:
            deal.lead.status = "working"
    apply_prediction(db, deal, deal.lead)
    db.commit()
    db.refresh(deal)
    return _serialize(deal)


@router.get("/{deal_id}/prediction")
def get_prediction(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).options(joinedload(Deal.lead)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    pred = predict_deal(deal, deal.lead)
    latest = db.query(Prediction).filter(Prediction.deal_id == deal.id).order_by(Prediction.created_at.desc()).first()
    return {
        "deal_id": deal.id, "stage": deal.stage, "value": float(deal.value),
        **pred,
        "latest_stored": {
            "win_probability": latest.win_probability,
            "expected_revenue": float(latest.expected_revenue),
            "risk_level": latest.risk_level,
        } if latest else None,
        "stage_history": [
            {"from_stage": h.from_stage, "to_stage": h.to_stage, "changed_at": h.changed_at.isoformat()}
            for h in sorted(deal.stage_history, key=lambda x: x.changed_at)
        ],
    }

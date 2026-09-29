import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import (Automation, AutomationRun, Lead, EmailMessage, Task,
                      Activity, EngagementEvent, Deal, Deal as DealModel)
from ..services.email_gen import generate_email
from ..services.score_service import recompute_lead_score
from ..routers.deals import apply_prediction

router = APIRouter(prefix="/api/automations", tags=["automations"])


class AutomationUpdate(BaseModel):
    enabled: bool | None = None
    name: str | None = None
    description: str | None = None
    conditions: dict | None = None


class RunRequest(BaseModel):
    lead_id: int | None = None


def _log(db: Session, automation: Automation, lead_id, summary: str, result: str, status="success"):
    db.add(AutomationRun(automation_id=automation.id, lead_id=lead_id,
                         trigger_summary=summary, result=result, status=status))
    automation.last_run_at = dt.datetime.now(dt.timezone.utc)


def _execute_actions(db: Session, automation: Automation, lead: Lead, summary: str) -> str:
    results = []
    for action in automation.actions or []:
        t = action.get("type")
        if t == "generate_outreach_email":
            events = db.query(EngagementEvent).filter(EngagementEvent.lead_id == lead.id).all()
            gen = generate_email(lead, "professional", "medium", events)
            db.add(EmailMessage(lead_id=lead.id, subject=gen["subject"], body=gen["body"],
                                status="draft", generated_by=gen.get("generated_by", "demo")))
            results.append("generated outreach email draft")
            db.add(Activity(lead_id=lead.id, type="automation",
                            message="Automation generated a personalized outreach draft (hot lead)"))
        elif t == "create_followup_task":
            days = int(action.get("days", 1))
            due = dt.date.today() + dt.timedelta(days=days)
            db.add(Task(lead_id=lead.id, title=f"Follow up with {lead.name} ({lead.company_name})",
                        due_date=due))
            results.append(f"created follow-up task due {due.isoformat()}")
            db.add(Activity(lead_id=lead.id, type="automation",
                            message=f"Automation created a follow-up task (due {due.isoformat()})"))
        elif t == "increase_intent_score":
            amount = int(action.get("amount", 10))
            lead.intent_score = (lead.intent_score or 0) + amount
            recompute_lead_score(db, lead, reason="engagement")
            results.append(f"increased intent score by {amount} (now {lead.intent_score})")
            db.add(Activity(lead_id=lead.id, type="automation",
                            message=f"Automation increased intent score by {amount} (multiple opens detected)"))
        elif t == "notify_rep":
            db.add(Activity(lead_id=lead.id, type="automation",
                            message=f"🔔 Sales rep notified: strong intent signals from {lead.name} ({lead.company_name})"))
            results.append("notified sales representative")
        elif t == "move_to_stage":
            stage = action.get("stage", "DEMO")
            deal = db.query(Deal).filter(Deal.lead_id == lead.id, ~Deal.stage.in_(["WON", "LOST"])).first()
            if deal and deal.stage != stage:
                old = deal.stage
                deal.stage = stage
                db.add(joined_stage_history(db, deal, old, stage))
                db.add(Activity(lead_id=lead.id, type="automation",
                                message=f"Automation moved deal {old} → {stage} (demo requested)"))
                apply_prediction(db, deal, lead)
                results.append(f"moved deal {old} → {stage}")
            elif not deal:
                deal = Deal(lead_id=lead.id, name=f"{lead.company_name} — SalesPilot AI", value=max(float(lead.budget or 15000), 10000), stage=stage)
                db.add(deal)
                db.flush()
                apply_prediction(db, deal, lead)
                results.append(f"created deal at stage {stage}")
        elif t == "noop":
            results.append("no-op")
    _log(db, automation, lead.id, summary, "; ".join(results))
    return "; ".join(results)


def joined_stage_history(db, deal, old, new):
    from ..models import StageHistory
    return StageHistory(deal_id=deal.id, from_stage=old, to_stage=new)


def evaluate_for_lead(db: Session, lead: Lead, event_type: str | None = None):
    """Run all enabled automations relevant to this lead. Returns list of results."""
    fired = []
    autos = db.query(Automation).filter(Automation.enabled == True).all()
    for a in autos:
        tt = a.trigger_type
        conds = a.conditions or {}
        if tt == "score_above_threshold" and lead.score > conds.get("threshold", 75):
            # avoid duplicate drafts: only if no recent automation email in last day
            recent = db.query(AutomationRun).filter(
                AutomationRun.automation_id == a.id, AutomationRun.lead_id == lead.id,
                AutomationRun.ran_at > dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).count()
            if not recent:
                _execute_actions(db, a, lead, f"Lead score {lead.score} > {conds.get('threshold', 75)}")
                fired.append(a.name)
        elif tt == "email_opened_multiple" and event_type == "opened":
            opens = db.query(EngagementEvent).filter(
                EngagementEvent.lead_id == lead.id, EngagementEvent.event_type == "opened").count()
            if opens >= conds.get("opens", 2):
                recent = db.query(AutomationRun).filter(
                    AutomationRun.automation_id == a.id, AutomationRun.lead_id == lead.id,
                    AutomationRun.ran_at > dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).count()
                if not recent:
                    _execute_actions(db, a, lead, f"Email opened {opens} times (≥{conds.get('opens', 2)})")
                    fired.append(a.name)
        elif tt == "demo_requested" and event_type == "demo_requested":
            _execute_actions(db, a, lead, "Demo requested by lead")
            fired.append(a.name)
    db.commit()
    return fired


@router.get("")
def list_automations(db: Session = Depends(get_db)):
    autos = db.query(Automation).all()
    out = []
    for a in autos:
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == a.id) \
            .order_by(AutomationRun.ran_at.desc()).limit(20).count()
        out.append({
            "id": a.id, "name": a.name, "description": a.description,
            "trigger_type": a.trigger_type, "conditions": a.conditions, "actions": a.actions,
            "enabled": a.enabled, "last_run_at": a.last_run_at.isoformat() if a.last_run_at else None,
            "run_count": runs,
        })
    return {"items": out}


@router.patch("/{automation_id}")
def update_automation(automation_id: int, payload: AutomationUpdate, db: Session = Depends(get_db)):
    a = db.query(Automation).filter(Automation.id == automation_id).first()
    if not a:
        raise HTTPException(404, "Automation not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    return {"ok": True}


@router.get("/{automation_id}/runs")
def automation_runs(automation_id: int, db: Session = Depends(get_db)):
    runs = db.query(AutomationRun).filter(AutomationRun.automation_id == automation_id) \
        .order_by(AutomationRun.ran_at.desc()).limit(100).all()
    return {"items": [{
        "id": r.id, "lead_id": r.lead_id, "trigger_summary": r.trigger_summary,
        "result": r.result, "status": r.status, "ran_at": r.ran_at.isoformat(),
    } for r in runs]}


@router.get("/runs/recent")
def recent_runs(db: Session = Depends(get_db)):
    runs = db.query(AutomationRun).options(joinedload(AutomationRun.automation), joinedload(AutomationRun.lead)) \
        .order_by(AutomationRun.ran_at.desc()).limit(50).all()
    return {"items": [{
        "id": r.id, "automation": r.automation.name if r.automation else "",
        "lead": r.lead.name if r.lead else None, "lead_id": r.lead_id,
        "trigger_summary": r.trigger_summary, "result": r.result,
        "status": r.status, "ran_at": r.ran_at.isoformat(),
    } for r in runs]}


@router.post("/{automation_id}/run")
def run_now(automation_id: int, payload: RunRequest, db: Session = Depends(get_db)):
    a = db.query(Automation).filter(Automation.id == automation_id).first()
    if not a:
        raise HTTPException(404, "Automation not found")
    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
        if not lead:
            raise HTTPException(404, "Lead not found")
        result = _execute_actions(db, a, lead, f"Manual run for {lead.name}")
        db.commit()
        return {"ok": True, "result": result}
    # sweep: evaluate against all leads where trigger condition matches
    executed = 0
    for lead in db.query(Lead).all():
        before = lead.score
        fired = evaluate_for_lead(db, lead)
        executed += len(fired)
    return {"ok": True, "executed": executed}


# Time-based sweep, also callable from background service
def sweep_time_based(db: Session):
    fired = 0
    autos = db.query(Automation).filter(Automation.enabled == True,
                                        Automation.trigger_type == "no_response_days").all()
    for a in autos:
        days = (a.conditions or {}).get("days", 5)
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        leads = db.query(Lead).join(EmailMessage).filter(
            EmailMessage.status == "sent",
            db.query(EngagementEvent).filter(
                EngagementEvent.lead_id == Lead.id,
                EngagementEvent.event_type == "reply").exists() == False,
            EmailMessage.sent_at < cutoff).all()
        for lead in leads:
            recent = db.query(AutomationRun).filter(
                AutomationRun.automation_id == a.id, AutomationRun.lead_id == lead.id,
                AutomationRun.ran_at > dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).count()
            if not recent:
                _execute_actions(db, a, lead, f"No response for {days}+ days after last email")
                fired += 1
    db.commit()
    return fired

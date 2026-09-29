from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Setting
from ..config import AI_PROVIDER, MODEL_BACKEND
from ..services.scoring import WEIGHTS, INDUSTRY_FIT

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULTS = {
    "company_name": "SalesPilot Demo Co",
    "rep_name": "Alex Morgan",
    "rep_email": "alex@salespilot.ai",
    "notify_on_hot_lead": True,
    "default_email_tone": "professional",
    "follow_up_days": 5,
}


class SettingsPayload(BaseModel):
    company_name: str | None = None
    rep_name: str | None = None
    rep_email: str | None = None
    notify_on_hot_lead: bool | None = None
    default_email_tone: str | None = None
    follow_up_days: int | None = None


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    stored = {s.key: s.value for s in db.query(Setting).all()}
    values = {**DEFAULTS, **stored}
    return {
        "values": values,
        "ai_provider": AI_PROVIDER,  # "openai" if configured else "demo" (fallback mode)
        "model_backend": MODEL_BACKEND,
        "scoring_weights": WEIGHTS,
        "industry_fit": INDUSTRY_FIT,
    }


@router.put("")
def update_settings(payload: SettingsPayload, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        row = db.query(Setting).filter(Setting.key == k).first()
        if row:
            row.value = v
        else:
            db.add(Setting(key=k, value=v))
    db.commit()
    return {"ok": True, "values": {**DEFAULTS, **{s.key: s.value for s in db.query(Setting).all()}}}

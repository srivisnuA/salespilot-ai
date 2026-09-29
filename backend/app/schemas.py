import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

router_placeholder = None  # schemas live here as plain models, routers import from this module


class LeadBase(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    company_name: str = ""
    job_title: str = ""
    industry: str = ""
    company_size: str = ""
    annual_revenue: float = 0
    source: str = "website"
    budget: float = 0
    buying_timeline: str = "unknown"
    pain_point: str = ""
    notes: str = ""
    status: str = "new"


class LeadCreate(LeadBase):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)


class LeadUpdate(LeadBase):
    pass


class ScoreFactorOut(BaseModel):
    factor: str
    points: float
    max_points: float
    explanation: str
    kind: str

    class Config:
        from_attributes = True


class EngagementEventOut(BaseModel):
    id: int
    event_type: str
    occurred_at: dt.datetime
    email_id: Optional[int] = None

    class Config:
        from_attributes = True


class EmailOut(BaseModel):
    id: int
    subject: str
    body: str
    tone: str
    length: str
    status: str
    generated_by: str
    sent_at: Optional[dt.datetime] = None
    created_at: dt.datetime
    lead_id: int

    class Config:
        from_attributes = True


class DealOut(BaseModel):
    id: int
    name: str
    stage: str
    value: float
    win_probability: float
    expected_revenue: float
    risk_level: str
    expected_close_date: Optional[dt.date] = None

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    title: str
    status: str
    due_date: Optional[dt.date] = None

    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    id: int
    type: str
    message: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class LeadOut(LeadBase):
    id: int
    score: int
    classification: str
    conversion_probability: float
    intent_score: int
    created_at: dt.datetime

    class Config:
        from_attributes = True


class LeadDetailOut(LeadOut):
    score_factors: list[ScoreFactorOut] = []
    activities: list[ActivityOut] = []
    emails: list[EmailOut] = []
    engagement_events: list[EngagementEventOut] = []
    deals: list[DealOut] = []
    tasks: list[TaskOut] = []

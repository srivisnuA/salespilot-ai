import datetime as dt
import decimal

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey, JSON, Numeric, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    industry: Mapped[str] = mapped_column(String(100), index=True)
    size: Mapped[str] = mapped_column(String(50))  # 1-10, 11-50, 51-200, 201-1000, 1000+
    website: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    leads: Mapped[list["Lead"]] = relationship(back_populates="company")


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(50), default="")
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company_name: Mapped[str] = mapped_column(String(200), default="")
    job_title: Mapped[str] = mapped_column(String(150), default="")
    industry: Mapped[str] = mapped_column(String(100), default="", index=True)
    company_size: Mapped[str] = mapped_column(String(50), default="")
    annual_revenue: Mapped[float] = mapped_column(Float, default=0)  # company revenue, USD
    source: Mapped[str] = mapped_column(String(100), default="website", index=True)
    budget: Mapped[float] = mapped_column(Float, default=0)
    buying_timeline: Mapped[str] = mapped_column(String(50), default="unknown")  # immediate/quarter/half_year/year/unknown
    pain_point: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    classification: Mapped[str] = mapped_column(String(20), default="cold", index=True)  # hot/warm/cold
    conversion_probability: Mapped[float] = mapped_column(Float, default=0)  # 0..1
    status: Mapped[str] = mapped_column(String(30), default="new")  # new/working/nurture
    intent_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company: Mapped[Company | None] = relationship(back_populates="leads")
    score_factors: Mapped[list["ScoreFactor"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    emails: Mapped[list["EmailMessage"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    engagement_events: Mapped[list["EngagementEvent"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    deals: Mapped[list["Deal"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    automation_runs: Mapped[list["AutomationRun"]] = relationship(back_populates="lead")


class ScoreFactor(Base):
    __tablename__ = "score_factors"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    factor: Mapped[str] = mapped_column(String(100))
    points: Mapped[float] = mapped_column(Float)
    max_points: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(10), default="positive")  # positive/negative
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lead: Mapped[Lead] = relationship(back_populates="score_factors")


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    channel: Mapped[str] = mapped_column(String(100), default="email")
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    emails: Mapped[list["EmailMessage"]] = relationship(back_populates="campaign")


class EmailMessage(Base):
    __tablename__ = "emails"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(30), default="professional")
    length: Mapped[str] = mapped_column(String(30), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)  # draft/approved/sent
    generated_by: Mapped[str] = mapped_column(String(30), default="demo")  # demo/openai
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    lead: Mapped[Lead] = relationship(back_populates="emails")
    campaign: Mapped[Campaign | None] = relationship(back_populates="emails")


class EngagementEvent(Base):
    __tablename__ = "engagement_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    email_id: Mapped[int | None] = mapped_column(ForeignKey("emails.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    # sent/delivered/opened/link_clicked/reply/demo_requested/meeting_booked/follow_up_completed
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    lead: Mapped[Lead] = relationship(back_populates="engagement_events")


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    stage: Mapped[str] = mapped_column(String(30), default="NEW", index=True)
    value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    win_probability: Mapped[float] = mapped_column(Float, default=0)
    expected_revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    expected_close_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    lead: Mapped[Lead] = relationship(back_populates="deals")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="deal", cascade="all, delete-orphan")
    stage_history: Mapped[list["StageHistory"]] = relationship(back_populates="deal", cascade="all, delete-orphan")


class StageHistory(Base):
    __tablename__ = "stage_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True)
    from_stage: Mapped[str] = mapped_column(String(30))
    to_stage: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    deal: Mapped[Deal] = relationship(back_populates="stage_history")


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True)
    win_probability: Mapped[float] = mapped_column(Float)
    expected_revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    risk_level: Mapped[str] = mapped_column(String(20))
    positive_factors: Mapped[list] = mapped_column(JSON, default=list)
    negative_factors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    deal: Mapped[Deal] = relationship(back_populates="predictions")


class Automation(Base):
    __tablename__ = "automations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    trigger_type: Mapped[str] = mapped_column(String(50))
    # score_above_threshold / email_opened_multiple / no_response_days / demo_requested / lead_created
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    runs: Mapped[list["AutomationRun"]] = relationship(back_populates="automation")


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    automation_id: Mapped[int] = mapped_column(ForeignKey("automations.id"), index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    trigger_summary: Mapped[str] = mapped_column(String(300), default="")
    result: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="success")  # success/failed
    ran_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    automation: Mapped[Automation] = relationship(back_populates="runs")
    lead: Mapped[Lead | None] = relationship(back_populates="automation_runs")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/done
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    lead: Mapped[Lead | None] = relationship(back_populates="tasks")


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    type: Mapped[str] = mapped_column(String(50))  # engagement/email/score/automation/stage/system
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    lead: Mapped[Lead] = relationship(back_populates="activities")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


Index("ix_engagement_lead_type", EngagementEvent.lead_id, EngagementEvent.event_type)

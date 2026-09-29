import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DB_NAME", "u3346p3833_salespilot_ai")
os.environ.setdefault("DB_USER", "u3346p3833_user")
os.environ.setdefault("DB_PASSWORD", "IzhK10AalUCkbVTr")
os.environ.setdefault("DB_HOST", "127.0.0.1")

from app.services.scoring import score_lead  # noqa: E402
from app.services.prediction import predict_deal  # noqa: E402
from app.services.email_gen import generate_email  # noqa: E402


class FakeEvent:
    def __init__(self, event_type):
        self.event_type = event_type
        self.occurred_at = dt.datetime.now(dt.timezone.utc)


class FakeLead:
    def __init__(self, **kw):
        defaults = dict(name="Jane Doe", email="jane@acme.com", company_name="Acme",
                        job_title="VP Sales", industry="SaaS", company_size="201-1000",
                        annual_revenue=10_000_000, source="inbound", budget=100_000,
                        buying_timeline="immediate", pain_point="manual follow-ups",
                        intent_score=0)
        defaults.update(kw)
        for k, v in defaults.items():
            setattr(self, k, v)


def test_hot_profile_scores_hot():
    lead = FakeLead()
    events = [FakeEvent("reply"), FakeEvent("reply"), FakeEvent("demo_requested"),
              FakeEvent("opened"), FakeEvent("link_clicked")]
    r = score_lead(lead, events)
    assert 75 <= r.score <= 100, f"expected hot, got {r.score}"
    assert r.classification == "hot"
    assert abs(sum(f["points"] for f in r.factors) - r.score) <= 1


def test_cold_profile_scores_cold():
    lead = FakeLead(job_title="Intern", industry="Manufacturing", company_size="1-10",
                    budget=0, buying_timeline="unknown", source="cold_outreach")
    r = score_lead(lead, [])
    assert r.score < 50
    assert r.classification == "cold"


def test_score_clamped():
    lead = FakeLead()
    events = [FakeEvent(t) for t in ["reply"] * 5 + ["opened"] * 10 + ["demo_requested"] * 5]
    r = score_lead(lead, events)
    assert r.score <= 100


def test_reply_increases_score():
    base = score_lead(FakeLead(), [])
    with_reply = score_lead(FakeLead(), [FakeEvent("reply")])
    assert with_reply.score > base.score


def test_prediction_math():
    class FakeDeal:
        stage = "DEMO"
        value = 40000
        created_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10)
        expected_close_date = dt.date.today() + dt.timedelta(days=30)

    lead = FakeLead(score=70)
    lead.engagement_events = [FakeEvent("reply"), FakeEvent("opened")]
    pred = predict_deal(FakeDeal(), lead)
    assert abs(pred["expected_revenue"] - 40000 * pred["win_probability"] / 100) < 0.01
    assert pred["risk_level"] in ("low", "medium", "high")
    assert pred["positive_factors"] and pred["negative_factors"] is not None
    assert 0 <= pred["win_probability"] <= 100


def test_email_personalization():
    lead = FakeLead(pain_point="manual follow-ups waste rep time")
    out = generate_email(lead, tone="consultative", length="medium", events=[])
    assert "Acme" in out["body"]
    assert "Jane" in out["body"]
    assert "manual follow-ups" in out["body"] or "manual follow-ups".title() in out["body"]
    assert out["subject"]


def test_tone_and_length_vary():
    lead = FakeLead()
    short = generate_email(lead, "concise", "short", [])
    detailed = generate_email(lead, "consultative", "detailed", [])
    assert len(short["body"]) < len(detailed["body"])

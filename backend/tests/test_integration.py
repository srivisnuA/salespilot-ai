"""Integration tests against the seeded dev database (no server needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DB_NAME", "u3346p3833_salespilot_ai")
os.environ.setdefault("DB_USER", "u3346p3833_user")
os.environ.setdefault("DB_PASSWORD", "IzhK10AalUCkbVTr")
os.environ.setdefault("DB_HOST", "127.0.0.1")

from app.database import SessionLocal  # noqa: E402
from app import models  # noqa: E402
from app.services.score_service import recompute_lead_score  # noqa: E402
from app.seed import seed  # noqa: E402


def test_seed_idempotent():
    db = SessionLocal()
    assert seed(db) is False  # already seeded → no duplicates
    assert db.query(models.Lead).count() >= 50


def test_all_six_industries_present():
    db = SessionLocal()
    inds = {r[0] for r in db.query(models.Lead.industry).distinct()}
    assert {"SaaS", "FinTech", "Healthcare", "E-commerce", "Manufacturing", "Technology"} <= inds


def test_every_lead_has_factors_and_probability():
    db = SessionLocal()
    for lead in db.query(models.Lead).limit(10):
        assert 0 <= lead.score <= 100
        assert lead.classification in ("hot", "warm", "cold")
        assert 0 <= lead.conversion_probability <= 1
        assert len(lead.score_factors) >= 8


def test_deals_have_predictions():
    db = SessionLocal()
    for d in db.query(models.Deal).limit(10):
        if d.stage not in ("WON", "LOST"):
            assert 0 <= d.win_probability <= 100
            assert abs(float(d.expected_revenue) - float(d.value) * d.win_probability / 100) < 1


def test_stage_history_exists_for_moved_deals():
    db = SessionLocal()
    moved = db.query(models.Deal).filter(models.Deal.stage.in_(["DEMO", "NEGOTIATION", "WON", "LOST"])).first()
    assert moved is not None
    assert len(moved.stage_history) >= 1

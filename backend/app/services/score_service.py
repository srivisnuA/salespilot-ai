"""Central helper: recompute a lead's score, persist factors, log activity."""
from sqlalchemy.orm import Session

from ..models import Lead, ScoreFactor, Activity
from .scoring import score_lead


def recompute_lead_score(db: Session, lead: Lead, reason: str = "update") -> int:
    events = lead.engagement_events
    result = score_lead(lead, events)
    old = lead.score
    lead.score = result.score
    lead.classification = result.classification
    lead.conversion_probability = result.conversion_probability

    lead.score_factors.clear()
    for f in result.factors:
        lead.score_factors.append(ScoreFactor(
            factor=f["factor"], points=f["points"], max_points=f["max_points"],
            explanation=f["explanation"], kind=f["kind"],
        ))

    if reason == "engagement" and old != result.score:
        delta = result.score - old
        sign = "+" if delta >= 0 else ""
        db.add(Activity(
            lead_id=lead.id, type="score",
            message=f"Lead score updated {old} → {result.score} ({sign}{delta}) after engagement activity",
        ))
    db.flush()
    return result.score

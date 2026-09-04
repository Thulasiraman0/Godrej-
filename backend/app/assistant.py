"""LLM never sees pixels. Tool-calling over the event store only."""

from __future__ import annotations

from . import store
from .taxonomy import BEHAVIOURS

COACHING = {b["id"]: b["good"] for b in BEHAVIOURS}
NAMES = {b["id"]: b["name"] for b in BEHAVIOURS}


def answer(question: str) -> dict:
    q = question.lower()
    behaviour = next((b["id"] for b in BEHAVIOURS if b["id"] in q or b["name"].lower() in q), None)
    bay = next((b for b in ["Bay-A", "Bay-B", "Bay-C", "Bay-D"] if b.lower() in q or b[-1].lower() in q and "bay" in q), None)
    band = next((b for b in ["Critical", "High", "Medium", "Low"] if b.lower() in q), None)
    rows = store.query_events(behaviour=behaviour, bay=bay, band=band)
    s = store.summary()
    if not rows and any(k in q for k in ("how many", "today", "exposure", "headline", "summary", "scorecard")):
        text = (
            s["headline"]
            + " We score bays and shifts, not named people. "
            + "Confirmed damage is only claimed with post-impact evidence."
        )
        return {"text": text, "events": rows[:8], "used_pixels": False}
    if not rows:
        return {
            "text": "No matching events in the store. I will not invent incidents. Try a bay (A–D) or a behaviour name.",
            "events": [],
            "used_pixels": False,
        }
    top = rows[0]
    coach = COACHING.get(top["behaviour"], "Follow Godrej good-practice handling.")
    text = (
        f"Retrieved {len(rows)} event(s). Latest: {NAMES.get(top['behaviour'], top['behaviour'])} "
        f"on {top['product_class']} in {top['bay']} ({top['shift']}). "
        f"Honesty state: {top['honesty'].replace('_', ' ')}. Risk {top['band']} "
        f"(~{top['impact_j']} J, ₹{top['exposure_inr']} exposure). "
        f"Coaching: {coach} Identity is clip-local ({top['handler']}) unless a supervisor attributes after review."
    )
    return {"text": text, "events": rows[:8], "used_pixels": False}

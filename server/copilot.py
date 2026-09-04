from __future__ import annotations

from risk.tables import PRACTICE
from server import store

BEHS = list(PRACTICE.keys())


def answer(question: str) -> dict:
    q = question.lower()
    behaviour = next((b for b in BEHS if b.lower().replace("_", " ") in q or b.lower() in q), None)
    bay = None
    for b in ("Bay-A", "Bay-B", "Bay-C", "Bay-D", "Bay-Live"):
        if b.lower() in q or (b[-1].lower() in q and "bay" in q):
            bay = b
            break
    band = next((b for b in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if b.lower() in q), None)
    rows = store.query_events(behaviour=behaviour, bay=bay, band=band)
    s = store.summary()
    if not rows and any(k in q for k in ("how many", "today", "exposure", "headline", "summary", "scorecard")):
        return {
            "text": s["headline"]
            + " We score bays and shifts, not named people. Confirmed damage needs post-impact evidence.",
            "events": [],
            "used_pixels": False,
        }
    if not rows:
        return {
            "text": "No matching events in the store. I will not invent incidents. Try a bay or a behaviour name (DROP, DRAG).",
            "events": [],
            "used_pixels": False,
        }
    top = rows[0]
    coach = PRACTICE.get(top["behaviour"], "")
    text = (
        f"Retrieved {len(rows)} event(s). Latest: {top['behaviour']} on {top['product_class']} in {top['bay']}. "
        f"Honesty: {top['state']}. Risk {top['risk_level']} (~{top.get('impact_j')} J, ₹{top.get('exposure_inr')} exposure). "
        f"Coaching: {coach} Identity is clip-local ({top.get('handler')}). Cites event {top['id']}."
    )
    return {"text": text, "events": rows[:8], "used_pixels": False}

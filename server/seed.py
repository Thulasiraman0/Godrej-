from __future__ import annotations

from core.schemas import Event, EvidenceState, RiskLevel
from risk.scorer import score_event
from risk.tables import PRACTICE
from server import store

SCENES = [
    ("DROP", "refrigerator", "Bay-A", 1.1),
    ("DRAG", "carton", "Bay-B", 0.05),
    ("ROLL", "mattress", "Bay-A", 0.2),
    ("IMPROPER_STACK", "carton", "Bay-C", 0.4),
    ("UNSTABLE_STACK", "kd_pack", "Bay-C", 0.6),
    ("OVERHANG", "appliance", "Bay-D", 0.3),
    ("STANDING_ON_CARTON", "carton", "Bay-B", 0.8),
    ("WRONG_ORIENTATION", "refrigerator", "Bay-A", 0.5),
    ("NO_EQUIPMENT", "appliance", "Bay-D", 0.4),
    ("STRAP_LIFT", "kd_pack", "Bay-C", 0.7),
    ("DROP", "glass_top", "Bay-A", 0.95),
    ("DRAG", "mattress", "Bay-B", 0.08),
]


def run() -> None:
    store.init()
    con = store.connect()
    con.execute("DELETE FROM events")
    con.commit()
    con.close()
    for i, (beh, cls, bay, h) in enumerate(SCENES, start=1):
        sc = score_event(beh, cls, height_m=h, location_hot=bay == "Bay-A", post_impact_still=beh == "DROP")
        e = Event(
            id=f"seed-{i:02d}",
            behaviour=beh,
            camera_id="cam-01",
            bay=bay,
            shift="Shift-1" if i % 2 else "Shift-2",
            t_start=8 * 3600 + i * 180,
            t_end=8 * 3600 + i * 180 + 3,
            object_ids=[i],
            product_class=cls,
            risk_score=sc["risk_score"],
            risk_level=sc["risk_level"],
            state=sc["state"],
            confidence=0.74,
            features={"drop_height_m": h, "impact_j": sc["impact_j"]},
            explanation=f"{beh} on {cls} in {bay}. Impact ~{sc['impact_j']} J → {sc['risk_level'].value}.",
            recommended_action=PRACTICE[beh],
            handler=f"Handler-{(i % 4) + 1}",
            exposure_inr=sc["exposure_inr"],
            impact_j=sc["impact_j"],
        )
        store.insert_event(e)
    print(store.summary()["headline"])


if __name__ == "__main__":
    run()

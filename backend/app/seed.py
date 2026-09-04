"""Seed 10 behaviours across bays so the dashboard is never empty."""

from __future__ import annotations

from . import store
from .risk import honesty_state, risk_score
from .taxonomy import BEHAVIOURS

SCENES = [
    ("drop_throw", "refrigerator", "Bay-A", "Shift-1", 1.1, True, False, True, "Fridge lowered then released from ~1.1 m."),
    ("dragging", "carton", "Bay-B", "Shift-1", 0.05, False, False, False, "Carton dragged 4 m along dock plate."),
    ("rolling", "mattress", "Bay-A", "Shift-2", 0.2, False, False, False, "Mattress rolled on edge to truck."),
    ("improper_stack", "carton", "Bay-C", "Shift-1", 0.4, False, False, False, "Small carton under a wide KD pack."),
    ("unstable_stack", "kd_flatpack", "Bay-C", "Shift-1", 0.6, False, False, False, "Stack axis tilt 11°, overhang 90 mm."),
    ("oversize_pallet", "appliance", "Bay-D", "Shift-2", 0.3, False, False, False, "Washer wider than 1200×800 pallet."),
    ("standing_on_cartons", "carton", "Bay-B", "Shift-2", 0.8, True, False, False, "Handler-A both ankles on carton top."),
    ("wrong_orientation", "refrigerator", "Bay-A", "Shift-1", 0.5, False, False, False, "Upright SKU laid flat on pallet."),
    ("manual_vs_equipment", "appliance", "Bay-D", "Shift-1", 0.4, False, False, False, "Two people carry a 28 kg unit; no trolley in frame."),
    ("strap_lift", "kd_flatpack", "Bay-C", "Shift-2", 0.7, False, False, False, "Hands on polypropylene strap while lifting."),
    ("drop_throw", "glass_top", "Bay-A", "Shift-2", 0.95, True, False, True, "Glass-top tabletop free-fall, sudden stop."),
    ("dragging", "mattress", "Bay-B", "Shift-1", 0.08, False, False, False, "Mattress dragged off trailer floor."),
]


def run() -> None:
    store.init()
    # wipe for a clean demo
    con = store.connect()
    con.execute("DELETE FROM events")
    con.commit()
    con.close()
    names = {b["id"]: b["name"] for b in BEHAVIOURS}
    for i, (beh, cls, bay, shift, h, defo, spill, still, note) in enumerate(SCENES, start=1):
        r = risk_score(beh, cls, height_m=h, repetition=1 + (i % 3), location_hot=bay == "Bay-A")
        row = {
            "ts": f"2026-09-04T0{8 + i % 8}:{10 + i * 3:02d}:00",
            "bay": bay,
            "shift": shift,
            "behaviour": beh,
            "product_class": cls,
            "handler": f"Handler-{(i % 4) + 1}",  # clip-local, never a name
            "honesty": honesty_state(beh, defo, spill, still),
            "band": r["band"],
            "impact_j": r["impact_j"],
            "height_m": r["height_m"],
            "p_damage": r["p_damage"],
            "exposure_inr": r["exposure_inr"],
            "evidence": f"{names.get(beh, beh)} — {note} Impact ~{r['impact_j']} J, {r['band']}.",
            "clip": f"clip-{i:02d}.mp4",
        }
        store.insert_event(row)
    print(store.summary()["headline"])


if __name__ == "__main__":
    run()

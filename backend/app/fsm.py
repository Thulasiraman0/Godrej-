"""Geometry / FSM detectors — the 10 behaviours without a trained action model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Track:
    tid: int
    cls: str
    xs: list[float] = field(default_factory=list)
    ys: list[float] = field(default_factory=list)
    bottoms: list[float] = field(default_factory=list)
    areas: list[float] = field(default_factory=list)
    contacts: list[bool] = field(default_factory=list)


def detect_behaviours(tracks: list[Track], floor_y: float, pallet_area: float | None = None) -> list[dict]:
    events: list[dict] = []
    for t in tracks:
        if len(t.ys) < 4:
            continue
        vy = [t.ys[i] - t.ys[i - 1] for i in range(1, len(t.ys))]
        ay = [vy[i] - vy[i - 1] for i in range(1, len(vy))]
        # 1 drop / throw: accelerating down then stop, no contact
        if ay and max(ay) > 4 and t.ys[-1] > floor_y * 0.72 and not any(t.contacts[-3:]):
            events.append({"behaviour": "drop_throw", "track": t.tid, "cls": t.cls})
        # 2 dragging: bottom glued to floor, centroid translates
        if t.bottoms and abs(t.bottoms[-1] - floor_y) < 12:
            dx = abs(t.xs[-1] - t.xs[0])
            lift = min(t.ys) < min(t.ys[0], t.ys[-1]) - 20
            if dx > 40 and not lift:
                events.append({"behaviour": "dragging", "track": t.tid, "cls": t.cls})
        # 3 rolling: area oscillates while translating
        if len(t.areas) > 6:
            osc = max(t.areas) / max(min(t.areas), 1)
            if osc > 1.35 and abs(t.xs[-1] - t.xs[0]) > 30:
                events.append({"behaviour": "rolling", "track": t.tid, "cls": t.cls})
        # 8 wrong orientation: unexpected aspect
        if t.areas and t.cls in {"refrigerator", "appliance"} and t.areas[-1] > 0:
            events.append({"behaviour": "wrong_orientation", "track": t.tid, "cls": t.cls})
    # 4/5/6 stack geometry across tracks
    products = [t for t in tracks if t.cls not in {"person", "pallet", "trolley", "forklift"}]
    pallets = [t for t in tracks if t.cls == "pallet"]
    if len(products) >= 2:
        by_y = sorted(products, key=lambda t: t.ys[-1] if t.ys else 0)
        if by_y[0].areas and by_y[-1].areas and by_y[0].areas[-1] < by_y[-1].areas[-1] * 0.7:
            events.append({"behaviour": "improper_stack", "track": by_y[0].tid, "cls": by_y[0].cls})
    if products and pallets and products[0].areas and pallets[0].areas:
        if products[0].areas[-1] > pallets[0].areas[-1] * 1.08:
            events.append({"behaviour": "oversize_pallet", "track": products[0].tid, "cls": products[0].cls})
            events.append({"behaviour": "unstable_stack", "track": products[0].tid, "cls": products[0].cls})
    people = [t for t in tracks if t.cls == "person"]
    equipment = [t for t in tracks if t.cls in {"trolley", "forklift"}]
    if products and people and not equipment:
        events.append(
            {
                "behaviour": "manual_vs_equipment",
                "track": products[0].tid,
                "cls": products[0].cls,
            }
        )
    return events

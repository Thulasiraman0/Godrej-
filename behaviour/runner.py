from __future__ import annotations

import math
import uuid
from collections import deque

from core.config import THRESH
from core.schemas import Event, FrameState, TrackFeature
from risk.scorer import score_event
from risk.tables import EQUIPMENT, HEAVY_SET, PRACTICE, PRODUCTS, UPRIGHT_SET


def _make(behaviour: str, feat: TrackFeature, extra: dict, conf: float, bay: str, camera: str) -> Event:
    scored = score_event(
        behaviour,
        feat.cls if feat.cls in PRODUCTS else "carton",
        height_m=max(feat.height_m, extra.get("drop_height_m", 0.4)),
        post_impact_still=behaviour == "DROP",
    )
    expl_map = {
        "DROP": f"Drop from ~{scored['height_m']} m, class {feat.cls}, estimated impact {scored['impact_j']} J → {scored['risk_level'].value}.",
        "DRAG": f"Product dragged {extra.get('drag_distance_m', 0):.2f} m with floor contact.",
        "ROLL": f"Oriented box rotated {extra.get('dtheta', 0):.0f} deg while translating on the floor.",
        "IMPROPER_STACK": "Child footprint/mass exceeds supporting item (small under large).",
        "OVERHANG": f"Load overhang ratio {extra.get('overhang', 0):.2f} beyond pallet footprint.",
        "UNSTABLE_STACK": f"Stack tilt {feat.tilt_deg:.1f} deg or centroid outside base.",
        "STANDING_ON_CARTON": "Person ankles project onto a product top surface.",
        "WRONG_ORIENTATION": "Upright SKU observed with inverted aspect for >2 s.",
        "NO_EQUIPMENT": "Heavy SKU moving with person contact and no trolley/pallet-truck in 2 m.",
        "STRAP_LIFT": "Hands in strap band while product height is rising.",
    }
    return Event(
        id=str(uuid.uuid4())[:8],
        behaviour=behaviour,
        camera_id=camera,
        bay=bay,
        shift="Live",
        t_start=feat.t - 1.5,
        t_end=feat.t + 1.5,
        object_ids=[feat.track_id],
        product_class=feat.cls if feat.cls in PRODUCTS else "carton",
        risk_score=scored["risk_score"],
        risk_level=scored["risk_level"],
        state=scored["state"],
        confidence=conf,
        features={**extra, "impact_j": scored["impact_j"], "height_m": scored["height_m"]},
        explanation=expl_map.get(behaviour, behaviour),
        recommended_action=PRACTICE.get(behaviour, ""),
        handler=f"Handler-{feat.track_id % 4 + 1}",
        exposure_inr=scored["exposure_inr"],
        impact_j=scored["impact_j"],
    )


class BehaviourEngine:
    def __init__(self, bay: str = "Bay-Live", camera: str = "cam-01"):
        self.bay = bay
        self.camera = camera
        self.last_fire: dict[tuple[int, str], float] = {}
        self.drop_state: dict[int, str] = {}
        self.drop_h: dict[int, float] = {}
        self.min_conf = THRESH["min_confidence"]
        self.debounce = THRESH["debounce_s"]

    def _ok(self, tid: int, name: str, t: float) -> bool:
        k = (tid, name)
        if t - self.last_fire.get(k, -999) < self.debounce:
            return False
        self.last_fire[k] = t
        return True

    def update(self, window: dict[int, deque[TrackFeature]], frame: FrameState) -> list[Event]:
        events: list[Event] = []
        feats_now = {tid: w[-1] for tid, w in window.items() if w}
        products = [f for f in feats_now.values() if f.cls in PRODUCTS]
        people = [f for f in feats_now.values() if f.cls == "person"]
        pallets = [f for f in feats_now.values() if f.cls == "pallet"]
        equipment = [f for f in feats_now.values() if f.cls in EQUIPMENT]

        for tid, w in window.items():
            if len(w) < 4:
                continue
            f = w[-1]
            if f.cls not in PRODUCTS:
                continue
            events.extend(self._drop(tid, w, f))
            events.extend(self._drag(tid, w, f))
            events.extend(self._roll(tid, w, f))
            events.extend(self._orient(tid, w, f))
            events.extend(self._strap(tid, w, f))

        events.extend(self._stack(products, pallets, frame.t))
        events.extend(self._standing(people, products, frame.t))
        events.extend(self._no_equip(products, people, equipment, frame.t))
        return [e for e in events if e.confidence >= self.min_conf]

    def _drop(self, tid, w, f) -> list[Event]:
        st = self.drop_state.get(tid, "IDLE")
        cfg = THRESH["drop"]
        if st == "IDLE" and f.in_hand and f.height_m > cfg["carry_height_m"]:
            self.drop_state[tid] = "CARRIED"
        elif st == "CARRIED" and (not f.in_hand) and f.ay < -0.5:
            self.drop_state[tid] = "FALLING"
            self.drop_h[tid] = f.height_m
        elif st == "FALLING":
            prev = list(w)[-2]
            collapse = abs(prev.vy) > 1e-3 and abs(f.vy) < abs(prev.vy) * (1 - cfg["impact_vy_collapse"])
            if f.floor_contact or collapse or f.height_m < 0.12:
                self.drop_state[tid] = "IMPACT"
        elif st == "IMPACT":
            still = all(abs(x.vx) < 0.4 and abs(x.vy) < 0.4 for x in list(w)[-5:])
            if still and self._ok(tid, "DROP", f.t):
                self.drop_state[tid] = "IDLE"
                h = self.drop_h.get(tid, f.height_m)
                return [_make("DROP", f, {"drop_height_m": h}, 0.78, self.bay, self.camera)]
        ys = [x.height_m for x in w]
        if max(ys) - min(ys) > 0.35 and (f.floor_contact or ys[-1] < ys[0] - 0.3) and self._ok(tid, "DROP", f.t):
            return [_make("DROP", f, {"drop_height_m": max(ys)}, 0.62, self.bay, self.camera)]
        return []

    def _drag(self, tid, w, f) -> list[Event]:
        cfg = THRESH["drag"]
        if not f.floor_contact:
            return []
        disp = math.hypot(w[-1].ground_x - w[0].ground_x, w[-1].ground_y - w[0].ground_y)
        max_h = max(x.height_m for x in w)
        if disp > cfg["min_distance_m"] and max_h < cfg["max_height_m"] + 0.25 and self._ok(tid, "DRAG", f.t):
            return [_make("DRAG", f, {"drag_distance_m": disp}, 0.7, self.bay, self.camera)]
        return []

    def _roll(self, tid, w, f) -> list[Event]:
        cfg = THRESH["roll"]
        dtheta = abs(w[-1].theta - w[0].theta)
        disp = math.hypot(w[-1].ground_x - w[0].ground_x, w[-1].ground_y - w[0].ground_y)
        if dtheta > cfg["min_dtheta_deg"] and disp > cfg["min_distance_m"] and f.floor_contact:
            if self._ok(tid, "ROLL", f.t):
                return [_make("ROLL", f, {"dtheta": dtheta}, 0.66, self.bay, self.camera)]
        ar = [x.aspect_ratio for x in w]
        if max(ar) / max(min(ar), 0.05) > 1.6 and disp > 0.3 and self._ok(tid, "ROLL", f.t):
            return [_make("ROLL", f, {"dtheta": 130}, 0.58, self.bay, self.camera)]
        return []

    def _orient(self, tid, w, f) -> list[Event]:
        if f.cls not in UPRIGHT_SET:
            return []
        inverted = [x for x in w if x.aspect_ratio < 0.85]
        dt = (w[-1].t - inverted[0].t) if inverted else 0
        if dt >= THRESH["orientation"]["invert_seconds"] and self._ok(tid, "WRONG_ORIENTATION", f.t):
            return [_make("WRONG_ORIENTATION", f, {"aspect": f.aspect_ratio}, 0.64, self.bay, self.camera)]
        return []

    def _strap(self, tid, w, f) -> list[Event]:
        rising = f.height_m > list(w)[max(0, len(w) - 6)].height_m + 0.12
        if f.in_hand and rising and self._ok(tid, "STRAP_LIFT", f.t):
            return [_make("STRAP_LIFT", f, {}, 0.57, self.bay, self.camera)]
        return []

    def _stack(self, products, pallets, t) -> list[Event]:
        out = []
        cfg = THRESH["stack"]
        if len(products) >= 2:
            by_y = sorted(products, key=lambda p: p.bbox[1] + p.bbox[3])
            child, parent = by_y[0], by_y[-1]
            ca = child.bbox[2] * child.bbox[3]
            pa = parent.bbox[2] * parent.bbox[3]
            if ca > pa * cfg["area_ratio"] and self._ok(child.track_id, "IMPROPER_STACK", t):
                out.append(_make("IMPROPER_STACK", child, {}, 0.68, self.bay, self.camera))
            if child.tilt_deg > cfg["tilt_deg"] and self._ok(child.track_id, "UNSTABLE_STACK", t):
                out.append(_make("UNSTABLE_STACK", child, {}, 0.65, self.bay, self.camera))
        if products and pallets:
            p = products[0]
            if p.overhang_ratio > cfg["overhang"] and self._ok(p.track_id, "OVERHANG", t):
                out.append(_make("OVERHANG", p, {"overhang": p.overhang_ratio}, 0.7, self.bay, self.camera))
        return out

    def _standing(self, people, products, t) -> list[Event]:
        out = []
        for person in people:
            px, py, pw, ph = person.bbox
            ankle_u, ankle_v = px + pw / 2, py + ph * 0.92
            for prod in products:
                x, y, w, h = prod.bbox
                if x <= ankle_u <= x + w and y <= ankle_v <= y + h * 0.45:
                    if self._ok(prod.track_id, "STANDING_ON_CARTON", t):
                        out.append(_make("STANDING_ON_CARTON", prod, {}, 0.72, self.bay, self.camera))
        return out

    def _no_equip(self, products, people, equipment, t) -> list[Event]:
        out = []
        if equipment or not people:
            return out
        for p in products:
            if p.cls not in HEAVY_SET:
                continue
            if p.in_hand and self._ok(p.track_id, "NO_EQUIPMENT", t):
                out.append(_make("NO_EQUIPMENT", p, {}, 0.6, self.bay, self.camera))
        return out

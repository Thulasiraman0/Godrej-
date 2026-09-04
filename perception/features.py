from __future__ import annotations

from collections import defaultdict, deque

from core.schemas import FrameState, TrackFeature
from perception.homography import GroundPlane
from risk.tables import PRODUCTS


def _iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


class Featurizer:
    def __init__(self, plane: GroundPlane | None = None, ring: int = 90):
        self.plane = plane or GroundPlane()
        self.hist: dict[int, deque[TrackFeature]] = defaultdict(lambda: deque(maxlen=ring))

    def update(self, frame: FrameState) -> dict[int, deque[TrackFeature]]:
        products = [d for d in frame.detections if d.cls in PRODUCTS]
        people = [d for d in frame.detections if d.cls == "person"]
        pallets = [d for d in frame.detections if d.cls == "pallet"]
        floor_v = 0.88 * frame.height

        for d in frame.detections:
            x, y, w, h = d.bbox
            cx, cy = x + w / 2, y + h / 2
            gx, gy = self.plane.to_ground(cx, cy)
            height_m = self.plane.height_m(y + h, y, frame.height)
            prev = self.hist[d.track_id][-1] if self.hist[d.track_id] else None
            dt = max((frame.t - prev.t) if prev else 0.1, 1e-3)
            vx = (gx - prev.ground_x) / dt if prev else 0.0
            vy = (height_m - prev.height_m) / dt if prev else 0.0
            ay = (vy - prev.vy) / dt if prev else 0.0
            floor_contact = abs((y + h) - floor_v) < 0.12 * frame.height and height_m < 0.45
            in_hand = False
            if d.cls in PRODUCTS:
                for p in people:
                    if _iou(d.bbox, p.bbox) > 0.02 or abs((p.bbox[0] + p.bbox[2] / 2) - cx) < (w + p.bbox[2]) * 0.45:
                        in_hand = True
                        break
            support_id = None
            overhang = 0.0
            if d.cls in PRODUCTS:
                for other in products:
                    if other.track_id == d.track_id:
                        continue
                    ox, oy, ow, oh = other.bbox
                    if abs(oy - (y + h)) < 24 and abs((ox + ow / 2) - cx) < (w + ow) * 0.4:
                        support_id = other.track_id
                if pallets:
                    overhang = max(0.0, 1.0 - _iou(d.bbox, pallets[0].bbox))
            tilt = abs((d.theta or 0.0) % 180)
            if tilt > 90:
                tilt = 180 - tilt
            feat = TrackFeature(
                track_id=d.track_id,
                cls=d.cls,
                t=frame.t,
                height_m=height_m,
                vx=vx,
                vy=vy,
                ay=ay,
                floor_contact=floor_contact,
                in_hand=in_hand,
                support_id=support_id,
                overhang_ratio=min(overhang, 1.0),
                tilt_deg=float(tilt),
                stack_level=1 if support_id else 0,
                aspect_ratio=h / max(w, 1),
                theta=float(d.theta or 0.0),
                ground_x=gx,
                ground_y=gy,
                conf=d.conf,
                bbox=d.bbox,
            )
            self.hist[d.track_id].append(feat)
        return self.hist

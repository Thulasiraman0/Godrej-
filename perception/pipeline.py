from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from behaviour.runner import BehaviourEngine
from core.config import THRESH
from core.schemas import Detection, FrameState
from perception.detector import Detector
from perception.features import Featurizer
from perception.homography import GroundPlane


def run_video(
    path: str | Path,
    camera_id: str = "cam-01",
    bay: str = "Bay-Live",
    max_frames: int = 400,
    out_overlay: Path | None = None,
) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(path)
    native_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
    target = THRESH["process_fps"]
    step = max(int(round(native_fps / target)), 1)

    det = Detector()
    feat = Featurizer(GroundPlane())
    engine = BehaviourEngine(bay=bay, camera=camera_id)
    events = []
    overlays = []
    writer = None
    if out_overlay:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_overlay), fourcc, target, (w, h))

    idx = 0
    processed = 0
    last_events = []
    while processed < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step != 0:
            idx += 1
            continue
        t = idx / native_fps
        raw = det.infer(frame)
        tracked = det.track(raw)
        detections = [
            Detection(track_id=tid, cls=cls, conf=conf, bbox=(x, y, bw, bh))
            for tid, x, y, bw, bh, cls, conf in tracked
        ]
        fs = FrameState(frame_idx=idx, t=t, camera_id=camera_id, detections=detections, width=w, height=h)
        window = feat.update(fs)
        new_events = engine.update(window, fs)
        if new_events:
            last_events = new_events
            events.extend(new_events)
        vis = frame.copy()
        for d in detections:
            x, y, bw, bh = map(int, d.bbox)
            color = (80, 80, 220) if d.cls == "person" else (40, 180, 90)
            cv2.rectangle(vis, (x, y), (x + bw, y + bh), color, 2)
            cv2.putText(vis, f"{d.cls} #{d.track_id}", (x, max(y - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y0 = 28
        for e in last_events[-3:]:
            msg = f"{e.behaviour} {e.risk_level.value} {e.impact_j}J"
            cv2.putText(vis, msg, (12, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 60, 255), 2)
            y0 += 24
        if writer:
            writer.write(vis)
        overlays.append(
            {
                "t": t,
                "frame": idx,
                "boxes": [
                    {"id": d.track_id, "cls": d.cls, "bbox": list(d.bbox), "conf": d.conf} for d in detections
                ],
            }
        )
        processed += 1
        idx += 1
    cap.release()
    if writer:
        writer.release()

    uniq = []
    seen = set()
    for e in events:
        key = (e.behaviour, tuple(e.object_ids))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    return {
        "frames": processed,
        "width": w,
        "height": h,
        "fps": native_fps,
        "events": [e.model_dump() for e in uniq],
        "overlays": overlays[:: max(len(overlays) // 40, 1)][:40],
        "backend": "yolo" if det.yolo is not None else "mog2",
        "overlay_video": str(out_overlay) if out_overlay else None,
    }


def make_demo_clip(path: Path, seconds: int = 6) -> Path:
    """Synthetic dock: person + falling carton so DROP/DRAG fire without warehouse footage."""
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h, fps = 960, 540, 20
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    n = seconds * fps
    for i in range(n):
        rng = np.random.default_rng(i)
        img = np.full((h, w, 3), 40, np.uint8)
        noise = rng.integers(0, 8, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        cv2.rectangle(img, (0, int(h * 0.84)), (w, h), (62, 56, 50), -1)
        # person walks left
        px = 80 + i
        cv2.rectangle(img, (px, 170), (px + 55, int(h * 0.84)), (50, 100, 210), -1)
        # carton drops on the right, independent
        cx = 620
        if i < 30:
            cy = 90
        else:
            cy = min(90 + (i - 30) * 12, int(h * 0.70))
        cv2.rectangle(img, (cx, cy), (cx + 130, cy + 100), (15, 190, 240), -1)
        writer.write(img)
    writer.release()
    return path

"""Cheap motion tracks so the demo runs without a trained YOLO weight."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .fsm import Track, detect_behaviours
from .risk import honesty_state, risk_score


def process_video(path: str | Path, max_frames: int = 240) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(path)
    fg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    floor_y = h * 0.88
    tracks: dict[int, Track] = {}
    next_id = 1
    overlays = []
    frame_i = 0
    while frame_i < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        mask = fg.apply(frame)
        mask = cv2.medianBlur(mask, 5)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blobs = []
        for c in cnts:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw * bh < 800:
                continue
            blobs.append((x, y, bw, bh))
        used = set()
        for x, y, bw, bh in blobs:
            cx, cy = x + bw / 2, y + bh / 2
            best, bid = 80.0, None
            for tid, t in tracks.items():
                if not t.xs or tid in used:
                    continue
                d = abs(t.xs[-1] - cx) + abs(t.ys[-1] - cy)
                if d < best:
                    best, bid = d, tid
            cls = "person" if bh > bw * 1.4 else "carton"
            if bid is None:
                bid = next_id
                next_id += 1
                tracks[bid] = Track(tid=bid, cls=cls)
            used.add(bid)
            t = tracks[bid]
            t.xs.append(cx)
            t.ys.append(cy)
            t.bottoms.append(y + bh)
            t.areas.append(bw * bh)
            t.contacts.append(False)
            overlays.append(
                {
                    "frame": frame_i,
                    "tid": bid,
                    "cls": cls,
                    "box": [int(x), int(y), int(bw), int(bh)],
                }
            )
        frame_i += 1
    cap.release()
    events = detect_behaviours(list(tracks.values()), floor_y=floor_y)
    enriched = []
    for e in events:
        height_m = 0.9 if e["behaviour"] == "drop_throw" else 0.35
        r = risk_score(e["behaviour"], e["cls"], height_m=height_m, repetition=1)
        state = honesty_state(e["behaviour"], False, False, e["behaviour"] == "drop_throw")
        enriched.append({**e, **r, "honesty": state, "fps": fps, "size": [w, h]})
    # unique by behaviour
    seen = set()
    uniq = []
    for e in enriched:
        if e["behaviour"] in seen:
            continue
        seen.add(e["behaviour"])
        uniq.append(e)
    return {
        "frames": frame_i,
        "tracks": len(tracks),
        "events": uniq,
        "overlay_count": len(overlays),
        "sample_overlays": overlays[:: max(len(overlays) // 12, 1)][:12],
    }

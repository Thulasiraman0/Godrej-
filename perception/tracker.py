"""Simple IoU / centroid tracker used when Ultralytics ByteTrack is unavailable."""

from __future__ import annotations


class SimpleTracker:
    def __init__(self, max_dist: float = 80.0):
        self.max_dist = max_dist
        self.next_id = 1
        self.prev: dict[int, tuple[float, float]] = {}

    def update(self, boxes: list[tuple[float, float, float, float, str, float]]) -> list[tuple]:
        """boxes: x,y,w,h,cls,conf → list of (track_id, x,y,w,h,cls,conf)"""
        used: set[int] = set()
        out = []
        for x, y, w, h, cls, conf in boxes:
            cx, cy = x + w / 2, y + h / 2
            best, bid = self.max_dist, None
            for tid, (px, py) in self.prev.items():
                if tid in used:
                    continue
                d = abs(px - cx) + abs(py - cy)
                if d < best:
                    best, bid = d, tid
            if bid is None:
                bid = self.next_id
                self.next_id += 1
            used.add(bid)
            out.append((bid, x, y, w, h, cls, conf))
        self.prev = {tid: (x + w / 2, y + h / 2) for tid, x, y, w, h, *_ in out}
        return out

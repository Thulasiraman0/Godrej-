"""YOLO if Ultralytics is installed; otherwise MOG2 blobs mapped to warehouse classes."""

from __future__ import annotations

from perception.tracker import SimpleTracker

COCO_MAP = {
    "person": "person",
    "refrigerator": "refrigerator",
    "tv": "appliance",
    "laptop": "appliance",
    "suitcase": "carton",
    "backpack": "carton",
    "book": "carton",
    "box": "carton",
    "couch": "mattress",
    "bed": "mattress",
    "chair": "carton",
    "dining table": "pallet",
    "truck": "vehicle",
    "car": "vehicle",
    "motorcycle": "pallet_truck",
    "bicycle": "trolley",
}


class Detector:
    def __init__(self):
        self.yolo = None
        self.tracker = SimpleTracker()
        self.fg = None
        try:
            from ultralytics import YOLO

            self.yolo = YOLO("yolo11n.pt")
        except Exception:
            self.yolo = None

    def infer(self, frame) -> list[tuple]:
        """Return list of (x,y,w,h,cls,conf)."""
        if self.yolo is not None:
            try:
                res = self.yolo.predict(frame, verbose=False, conf=0.25)[0]
                out = []
                names = res.names
                for b in res.boxes:
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    cls = names[int(b.cls[0])]
                    mapped = COCO_MAP.get(cls)
                    if not mapped:
                        continue
                    out.append((x1, y1, x2 - x1, y2 - y1, mapped, float(b.conf[0])))
                return out
            except Exception:
                pass
        return self._mog2(frame)

    def _mog2(self, frame):
        import cv2

        if self.fg is None:
            self.fg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
        raw = self.fg.apply(frame)
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        mask = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, k)
        mask = cv2.dilate(mask, k, iterations=2)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        boxes = []
        for c in cnts:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw < 24 or bh < 24 or bw * bh < 1200:
                continue
            cls = "person" if bh > bw * 1.35 else "carton"
            if y + bh > 0.86 * h and bw > 90 and bh < 80:
                cls = "pallet"
            boxes.append((float(x), float(y), float(bw), float(bh), cls, 0.55))
        return boxes

    def track(self, boxes):
        return self.tracker.update(boxes)

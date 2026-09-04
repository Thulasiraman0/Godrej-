from __future__ import annotations

import numpy as np

from core.config import THRESH


class GroundPlane:
    def __init__(self, image_points=None, world_points=None, camera_height_m: float = 4.2):
        cfg = THRESH.get("homography", {})
        img = np.array(image_points or cfg["image_points"], dtype=np.float32)
        wrd = np.array(world_points or cfg["world_points"], dtype=np.float32)
        self.H, _ = self._fit(img, wrd)
        self.camera_height_m = camera_height_m or cfg.get("camera_height_m", 4.2)

    @staticmethod
    def _fit(img, wrd):
        import cv2

        H, mask = cv2.findHomography(img, wrd, 0)
        if H is None:
            H = np.eye(3)
        return H, mask

    def to_ground(self, u: float, v: float) -> tuple[float, float]:
        p = np.array([u, v, 1.0], dtype=np.float64)
        q = self.H @ p
        if abs(q[2]) < 1e-8:
            return 0.0, 0.0
        return float(q[0] / q[2]), float(q[1] / q[2])

    def height_m(self, bbox_bottom_v: float, bbox_top_v: float, frame_h: int) -> float:
        """Crude: fraction of frame above floor scaled by camera height."""
        floor = 0.88 * frame_h
        lift_px = max(floor - bbox_bottom_v, 0.0)
        return float(min(self.camera_height_m * (lift_px / max(floor, 1.0)) * 1.6, 2.4))

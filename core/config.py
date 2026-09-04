from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

THRESH = {
    "debounce_s": 3.0,
    "min_confidence": 0.55,
    "process_fps": 10,
    "ring_frames": 90,
    "homography": {
        "image_points": [[80, 500], [1200, 500], [1260, 700], [20, 700]],
        "world_points": [[0.0, 0.0], [6.0, 0.0], [6.0, 4.0], [0.0, 4.0]],
        "camera_height_m": 4.2,
    },
    "drop": {
        "carry_height_m": 0.30,
        "free_fall_ay": 6.0,
        "fall_frames": 3,
        "impact_vy_collapse": 0.70,
        "still_frames": 8,
    },
    "drag": {"min_distance_m": 0.50, "max_height_m": 0.15},
    "roll": {"min_dtheta_deg": 120, "min_distance_m": 0.40},
    "stack": {"area_ratio": 1.15, "tilt_deg": 8.0, "overhang": 0.15},
    "standing": {"ankle_height_m": 0.20},
    "orientation": {"invert_seconds": 2.0},
    "equipment": {"heavy_radius_m": 2.0},
    "strap": {"band_frac": 0.20},
}

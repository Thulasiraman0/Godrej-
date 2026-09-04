"""Hour-one contract. Downstream never sees pixels — only TrackFeatures."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Point(BaseModel):
    u: float
    v: float
    x: float | None = None
    y: float | None = None


class Detection(BaseModel):
    track_id: int
    cls: str
    conf: float
    bbox: tuple[float, float, float, float]  # x, y, w, h
    theta: float | None = None
    keypoints: list[Point] | None = None


class FrameState(BaseModel):
    frame_idx: int
    t: float
    camera_id: str
    detections: list[Detection]
    width: int = 1280
    height: int = 720


class TrackFeature(BaseModel):
    track_id: int
    cls: str
    t: float
    height_m: float
    vx: float
    vy: float
    ay: float
    floor_contact: bool
    in_hand: bool
    support_id: int | None = None
    overhang_ratio: float = 0.0
    tilt_deg: float = 0.0
    stack_level: int = 0
    aspect_ratio: float = 1.0
    theta: float = 0.0
    ground_x: float = 0.0
    ground_y: float = 0.0
    conf: float = 0.0
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceState(str, Enum):
    OBSERVED = "OBSERVED"
    POTENTIAL_RISK = "POTENTIAL_RISK"
    CONFIRMED_DAMAGE = "CONFIRMED_DAMAGE"


class Event(BaseModel):
    id: str
    behaviour: str
    camera_id: str
    bay: str
    shift: str
    t_start: float
    t_end: float
    object_ids: list[int]
    product_class: str
    risk_score: float
    risk_level: RiskLevel
    state: EvidenceState
    confidence: float
    features: dict[str, Any] = Field(default_factory=dict)
    explanation: str
    recommended_action: str
    clip_path: str = ""
    thumb_path: str = ""
    reviewed_by: str | None = None
    handler: str = "Handler-A"
    exposure_inr: int = 0
    impact_j: float = 0.0

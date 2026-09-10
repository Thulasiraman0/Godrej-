# Sahaayak — Warehouse Handling Co-pilot

**Godrej Enterprises Group @ graVITas 2026**

> *Your warehouse camera, promoted from witness to coach.*

Sahaayak watches warehouse footage and turns unsafe material handling into risk alerts and coaching notes — before a mishandled refrigerator becomes a damage claim.

## How it works

The behaviour engine consumes **tracklets, not pixels**. Perception (YOLO + tracker + pose) produces `TrackFeature` objects, and everything downstream — behaviour detection, risk scoring, the assistant, and the dashboard — reads only that stream.

## Run

```bash
# API (repo root on PYTHONPATH)
cd /path/to/Godrej-
backend/.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=. backend/.venv/bin/python -m server.seed
PYTHONPATH=. backend/.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8000

# UI
cd frontend && npm install && npm run dev
```

Upload any MP4 on **Ingest**, or click **Run synthetic DROP clip** on the **Live wall**.

## Layout

| Path | Responsibility |
| --- | --- |
| `core/schemas.py` | Track contract (frozen) |
| `core/config.py` | Thresholds (YAML-equivalent) |
| `perception/detector.py` | YOLOv11-n or MOG2 fallback + SimpleTracker |
| `perception/features.py` | Detection → `TrackFeature` + homography metres |
| `perception/pipeline.py` | 10 fps sampler, overlay writer |
| `behaviour/runner.py` | 10 FSM detectors + debounce |
| `risk/` | Impact energy × fragility × history |
| `server/app.py` | FastAPI ingest, chat, review, WS |
| `frontend/` | Supervisor dashboard |
| `tests/fixtures/` | Synthetic tracklets |

## The ten behaviours

`DROP`, `DRAG`, `ROLL`, `IMPROPER_STACK`, `OVERHANG`, `UNSTABLE_STACK`, `STANDING_ON_CARTON`, `WRONG_ORIENTATION`, `NO_EQUIPMENT`, `STRAP_LIFT`.

Explanations are **templates**, not LLM text — the assistant only calls `query_events`.

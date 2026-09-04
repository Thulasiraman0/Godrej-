# Sahaayak — Warehouse Handling Co-pilot

Godrej Enterprises Group @ graVITas 2026

**Your warehouse camera, promoted from witness to coach.**

The behaviour engine consumes **tracklets, not pixels**. Perception (YOLO + tracker + pose) produces `TrackFeature` objects. Everything downstream — behaviour detection, risk scoring, the LLM, the dashboard — reads only that stream.

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

Upload any MP4 on **Ingest**, or click **Run synthetic DROP clip** on Live wall.

## Layout

```
core/schemas.py          Track contract (frozen)
core/config.py           thresholds (YAML-equivalent)
perception/detector.py   YOLOv11-n or MOG2 fallback + SimpleTracker
perception/features.py   Detection → TrackFeature + homography metres
perception/pipeline.py   10 fps sampler, overlay writer
behaviour/runner.py      10 FSM detectors + debounce
risk/                    impact energy × fragility × history
server/app.py            FastAPI ingest, chat, review, WS
frontend/                supervisor dashboard
tests/fixtures/          synthetic tracklets
```

## Ten behaviours

DROP, DRAG, ROLL, IMPROPER_STACK, OVERHANG, UNSTABLE_STACK, STANDING_ON_CARTON, WRONG_ORIENTATION, NO_EQUIPMENT, STRAP_LIFT.

Explanations are **templates**, not LLM text. The assistant only calls `query_events`.

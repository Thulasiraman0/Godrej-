# Sahaayak — Warehouse Handling Co-pilot

Godrej Enterprises Group @ graVITas 2026

**Your warehouse camera, promoted from witness to coach.**

Damage Detection → Damage Prevention. CCTV Surveillance → Operational Intelligence.

Sahaayak scores the *process*, not the person. It turns an ordinary camera into a system that understands loading/unloading as it happens, flags behaviour that will probably cause damage, scores risk with a physics-grounded impact-energy proxy, and tells the supervisor what to do — before the product is damaged.

## Positioning

Four differentiators:

1. **Physics-grounded risk** — drop height via homography, vertical velocity, fragility class → impact energy (J), not “DROP DETECTED”.
2. **Three-state honesty** — Observed Behaviour → Potential Risk → Confirmed Damage. We never claim damage without post-impact evidence.
3. **Anonymous-by-default** — faces blurred at the edge; Handler-A IDs live inside a single clip only; reporting by bay / shift / process.
4. **Prevention loop with a rupee number** — Avoided Cost = P(damage | behaviour, risk) × replacement value.

## Behaviour taxonomy (10)

1. Drop / throw  
2. Dragging on floor  
3. Rolling a carton/mattress  
4. Improper stack (small under large)  
5. Unstable stack / overhang  
6. Product larger than pallet  
7. Stepping / standing on cartons  
8. Wrong orientation (vertical kept flat)  
9. Manual handling where equipment required  
10. Lifting by packaging straps  

## Architecture

```
Video (RTSP / phone / MP4)
  → Edge: YOLO + ByteTrack + pose + homography
  → Temporal FSM / tracklet features (2–3 s window)
  → Risk engine (energy × fragility × frequency × location)
  → Event store (SQLite + 6 s evidence clips)
  → LLM assistant (tool-calling over events only — never pixels)
  → React dashboard
```

The LLM never sees pixels. It only sees structured event rows. If nothing matches, it says so.

## Stack

Python, FastAPI, OpenCV, Ultralytics YOLOv8/11 (optional), SQLite, React + Vite + Tailwind, Recharts.

## Run locally

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000

# frontend
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open the dashboard, then use **Live inference** to process a warehouse clip, or explore seeded events.

## Repository layout

```
backend/app/     FastAPI, risk engine, FSM behaviours, seed data, LLM tools
frontend/        Supervisor dashboard (timeline, heatmap, replay, chat, scorecard)
docs/            Pitch lines, responsible-AI notes
```

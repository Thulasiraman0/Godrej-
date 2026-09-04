from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from perception.pipeline import make_demo_clip, run_video
from risk.tables import PRACTICE
from server import store
from server.copilot import answer
from server.seed import run as seed_run

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "data" / "uploads"
CLIPS = ROOT / "data" / "clips"
UPLOADS.mkdir(parents=True, exist_ok=True)
CLIPS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Sahaayak", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    store.init()
    if not store.all_events():
        seed_run()
    demo = CLIPS / "demo_drop.mp4"
    if not demo.exists():
        make_demo_clip(demo)


@app.get("/api/health")
def health():
    return {"ok": True, "name": "Sahaayak"}


@app.get("/api/taxonomy")
def taxonomy():
    return [{"id": k, "name": k.replace("_", " ").title(), "good": v, "detection": k} for k, v in PRACTICE.items()]


@app.get("/api/events")
def events(behaviour: str | None = None, bay: str | None = None, band: str | None = None):
    return store.query_events(behaviour, bay, band)


@app.get("/api/summary")
def summary():
    return store.summary()


class ChatIn(BaseModel):
    question: str


@app.post("/api/chat")
def chat(body: ChatIn):
    return answer(body.question)


class ReviewIn(BaseModel):
    event_id: str
    verdict: str
    note: str = ""


@app.post("/api/review")
def review(body: ReviewIn):
    store.review(body.event_id, body.verdict, body.note)
    return {"ok": True, "summary": store.summary()}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), bay: str = "Bay-Live"):
    dest = UPLOADS / (file.filename or "clip.mp4")
    dest.write_bytes(await file.read())
    overlay = CLIPS / f"overlay_{dest.name}"
    result = run_video(dest, bay=bay, out_overlay=overlay)
    for e in result["events"]:
        store.insert_event(e)
    return result


@app.post("/api/ingest-demo")
def ingest_demo():
    demo = CLIPS / "demo_drop.mp4"
    if not demo.exists():
        make_demo_clip(demo)
    overlay = CLIPS / "overlay_demo.mp4"
    result = run_video(demo, bay="Bay-Live", out_overlay=overlay)
    for e in result["events"]:
        store.insert_event(e)
    return result


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return


@app.get("/")
def root():
    return {"service": "Sahaayak API", "docs": "/docs"}


if CLIPS.exists():
    app.mount("/clips", StaticFiles(directory=str(CLIPS)), name="clips")

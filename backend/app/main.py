from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import store
from .assistant import answer
from .seed import run as seed_run
from .taxonomy import BEHAVIOURS
from .video import process_video

app = FastAPI(title="Sahaayak", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)


@app.on_event("startup")
def startup() -> None:
    store.init()
    if not store.all_events():
        seed_run()


@app.get("/api/health")
def health():
    return {"ok": True, "name": "Sahaayak"}


@app.get("/api/taxonomy")
def taxonomy():
    return BEHAVIOURS


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


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    dest = UPLOADS / file.filename
    dest.write_bytes(await file.read())
    result = process_video(dest)
    # persist detected events
    from datetime import datetime, timezone

    from .risk import honesty_state
    from .taxonomy import BEHAVIOURS

    names = {b["id"]: b["name"] for b in BEHAVIOURS}
    saved = []
    for e in result["events"]:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "bay": "Bay-Live",
            "shift": "Live",
            "behaviour": e["behaviour"],
            "product_class": e.get("cls", "carton"),
            "handler": "Handler-Live",
            "honesty": e.get("honesty", honesty_state(e["behaviour"], False, False, False)),
            "band": e.get("band", "Medium"),
            "impact_j": e.get("impact_j", 0),
            "height_m": e.get("height_m", 0),
            "p_damage": e.get("p_damage", 0),
            "exposure_inr": e.get("exposure_inr", 0),
            "evidence": f"{names.get(e['behaviour'], e['behaviour'])} from uploaded clip {file.filename}",
            "clip": file.filename,
        }
        store.insert_event(row)
        saved.append(row)
    result["saved"] = saved
    return result


@app.get("/")
def root():
    return {"service": "Sahaayak API", "docs": "/docs"}

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.schemas import Event

DB = Path(__file__).resolve().parent.parent / "data" / "sahaayak.db"


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init() -> None:
    con = connect()
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY,
          payload TEXT NOT NULL,
          ts REAL,
          behaviour TEXT,
          bay TEXT,
          risk_level TEXT,
          state TEXT,
          dismissed INTEGER DEFAULT 0
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id TEXT,
          verdict TEXT,
          note TEXT
        )
        """
    )
    con.commit()
    con.close()


def insert_event(e: Event | dict) -> None:
    payload = e.model_dump(mode="json") if isinstance(e, Event) else e
    lvl = payload.get("risk_level")
    st = payload.get("state")
    if hasattr(lvl, "value"):
        payload["risk_level"] = lvl.value
    if hasattr(st, "value"):
        payload["state"] = st.value
    con = connect()
    con.execute(
        "INSERT OR REPLACE INTO events (id, payload, ts, behaviour, bay, risk_level, state) VALUES (?,?,?,?,?,?,?)",
        (
            payload["id"],
            json.dumps(payload),
            payload.get("t_start", 0),
            payload.get("behaviour"),
            payload.get("bay"),
            payload.get("risk_level"),
            payload.get("state"),
        ),
    )
    con.commit()
    con.close()


def all_events() -> list[dict]:
    con = connect()
    rows = list(con.execute("SELECT payload, dismissed FROM events ORDER BY ts DESC"))
    con.close()
    out = []
    for r in rows:
        d = json.loads(r["payload"])
        d["dismissed"] = r["dismissed"]
        out.append(d)
    return out


def query_events(behaviour=None, bay=None, band=None) -> list[dict]:
    rows = all_events()
    if behaviour:
        rows = [r for r in rows if r.get("behaviour") == behaviour]
    if bay:
        rows = [r for r in rows if r.get("bay") == bay]
    if band:
        rows = [r for r in rows if r.get("risk_level") == band]
    return rows


def review(event_id: str, verdict: str, note: str = "") -> None:
    con = connect()
    con.execute("INSERT INTO reviews (event_id, verdict, note) VALUES (?,?,?)", (event_id, verdict, note))
    if verdict == "dismiss":
        con.execute("UPDATE events SET dismissed=1 WHERE id=?", (event_id,))
    con.commit()
    con.close()


def summary() -> dict:
    rows = [r for r in all_events() if not r.get("dismissed")]
    exposure = sum(int(r.get("exposure_inr") or 0) for r in rows)
    high = [r for r in rows if r.get("risk_level") in {"HIGH", "CRITICAL"}]
    by_bay: dict[str, int] = {}
    by_beh: dict[str, int] = {}
    by_state: dict[str, int] = {}
    for r in rows:
        by_bay[r.get("bay") or "?"] = by_bay.get(r.get("bay") or "?", 0) + 1
        by_beh[r.get("behaviour") or "?"] = by_beh.get(r.get("behaviour") or "?", 0) + 1
        by_state[r.get("state") or "?"] = by_state.get(r.get("state") or "?", 0) + 1
    return {
        "events": len(rows),
        "high_risk": len(high),
        "exposure_inr": exposure,
        "by_bay": by_bay,
        "by_behaviour": by_beh,
        "by_honesty": by_state,
        "headline": (
            f"Today: {len(high)} high-risk handling events flagged. "
            f"Estimated ₹{exposure:,} of damage exposure surfaced for intervention."
        ),
    }

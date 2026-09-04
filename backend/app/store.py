from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "sahaayak.db"


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init() -> None:
    con = connect()
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY,
          ts TEXT,
          bay TEXT,
          shift TEXT,
          behaviour TEXT,
          product_class TEXT,
          handler TEXT,
          honesty TEXT,
          band TEXT,
          impact_j REAL,
          height_m REAL,
          p_damage REAL,
          exposure_inr INTEGER,
          evidence TEXT,
          clip TEXT
        )
        """
    )
    con.commit()
    con.close()


def insert_event(row: dict) -> int:
    con = connect()
    cur = con.execute(
        """
        INSERT INTO events (ts,bay,shift,behaviour,product_class,handler,honesty,band,impact_j,height_m,p_damage,exposure_inr,evidence,clip)
        VALUES (:ts,:bay,:shift,:behaviour,:product_class,:handler,:honesty,:band,:impact_j,:height_m,:p_damage,:exposure_inr,:evidence,:clip)
        """,
        row,
    )
    con.commit()
    eid = cur.lastrowid
    con.close()
    return int(eid)


def all_events() -> list[dict]:
    con = connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM events ORDER BY ts DESC")]
    con.close()
    return rows


def query_events(behaviour: str | None = None, bay: str | None = None, band: str | None = None) -> list[dict]:
    con = connect()
    q = "SELECT * FROM events WHERE 1=1"
    args: list = []
    if behaviour:
        q += " AND behaviour = ?"
        args.append(behaviour)
    if bay:
        q += " AND bay = ?"
        args.append(bay)
    if band:
        q += " AND band = ?"
        args.append(band)
    q += " ORDER BY ts DESC"
    rows = [dict(r) for r in con.execute(q, args)]
    con.close()
    return rows


def summary() -> dict:
    rows = all_events()
    exposure = sum(r["exposure_inr"] or 0 for r in rows)
    high = [r for r in rows if r["band"] in {"High", "Critical"}]
    by_bay: dict[str, int] = {}
    by_beh: dict[str, int] = {}
    by_honesty: dict[str, int] = {}
    for r in rows:
        by_bay[r["bay"]] = by_bay.get(r["bay"], 0) + 1
        by_beh[r["behaviour"]] = by_beh.get(r["behaviour"], 0) + 1
        by_honesty[r["honesty"]] = by_honesty.get(r["honesty"], 0) + 1
    return {
        "events": len(rows),
        "high_risk": len(high),
        "exposure_inr": exposure,
        "by_bay": by_bay,
        "by_behaviour": by_beh,
        "by_honesty": by_honesty,
        "headline": f"Today: {len(high)} high-risk handling events flagged. Estimated ₹{exposure:,} of damage exposure surfaced for intervention.",
    }

"""Shared helpers for the J1 lineups repo. Standard library only."""
import csv
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
GWDIR = os.path.join(ROOT, "gw")

XI_COLS = ["club", "club_id", "slot", "player_id", "player", "start_pct",
           "alt_id", "alt", "alt_pct"]
FINAL_COLS = XI_COLS + ["layer", "flags"]
AVAIL_COLS = ["logged_at", "player_id", "player", "club", "status", "label",
              "grade", "reason", "source", "source_date", "by"]
ELGOLAZO_COLS = ["club", "slot", "player_id", "player", "start_pct",
                 "alt_id", "alt", "alt_pct", "issue", "published", "by"]
OVERRIDE_COLS = ["club", "slot", "player_id", "player", "start_pct",
                 "alt_id", "alt", "alt_pct", "note"]

STATUSES = {"OUT", "SUSPENDED", "DOUBT", "AVAILABLE"}
LABELS = {"CONFIRMED", "LIKELY", "WATCH", "UNKNOWN"}
GRADES = {"A", "B", "C", "D"}


def now_gmt():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def gw_path(gw, name=""):
    return os.path.join(GWDIR, f"gw{int(gw):02d}", name)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # ignore blank lines and comment rows starting with '#'
    return [r for r in rows
            if any((v or "").strip() for v in r.values())
            and not (list(r.values())[0] or "").startswith("#")]


def write_csv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def players():
    """player_id -> row from data/players.csv"""
    return {r["player_id"]: r for r in read_csv(os.path.join(DATA, "players.csv"))}


def clubs():
    """club name -> row from data/clubs.csv (also accepts club_id)"""
    out = {}
    for r in read_csv(os.path.join(DATA, "clubs.csv")):
        out[r["club"]] = r
        out[r["club_id"]] = r
    return out


def current_gw():
    with open(os.path.join(GWDIR, "CURRENT")) as f:
        return int(f.read().strip())


def pct(v):
    v = (v or "").strip().rstrip("%")
    if v == "":
        return None
    try:
        return int(round(float(v)))
    except ValueError:
        return None

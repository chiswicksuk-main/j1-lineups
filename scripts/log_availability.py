"""Append one availability event safely (for agents and for you).

Usage:
  python scripts/log_availability.py --player-id fihnFope --status DOUBT \
      --label WATCH --grade A --reason "Concussion sub R14" \
      --source "J.League R14 match page" --source-date 2026-11-15 --by grok

Or by name if the ID is unknown (must match the register exactly, within club):
  python scripts/log_availability.py --player "Kim Ju-Sung" --club "Sanfrecce Hiroshima" ...

Only ever appends. Never edits or deletes old rows: a correction is a new row
with a later source_date. A return needs its own AVAILABLE row with a source.
"""
import argparse
import csv
import os
import sys
from common import AVAIL_COLS, STATUSES, LABELS, GRADES, gw_path, players, current_gw, now_gmt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gw", type=int)
    ap.add_argument("--player-id", default="")
    ap.add_argument("--player", default="")
    ap.add_argument("--club", default="")
    ap.add_argument("--status", required=True, choices=sorted(STATUSES))
    ap.add_argument("--label", required=True, choices=sorted(LABELS))
    ap.add_argument("--grade", required=True, choices=sorted(GRADES))
    ap.add_argument("--reason", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--source-date", required=True, help="YYYY-MM-DD, date of the evidence")
    ap.add_argument("--by", required=True, help="who logged it: matsu, claude, grok, chatgpt")
    a = ap.parse_args()

    reg = players()
    pid = a.player_id
    if not pid:
        hits = [p for p in reg.values() if p["player"] == a.player and (not a.club or p["club"] == a.club)]
        if len(hits) != 1:
            sys.exit(f"could not match '{a.player}' to exactly one player ({len(hits)} hits). Use --player-id.")
        pid = hits[0]["player_id"]
    if pid not in reg:
        sys.exit(f"{pid} not in data/players.csv")
    p = reg[pid]
    gw = a.gw or current_gw()
    path = gw_path(gw, "availability.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=AVAIL_COLS)
        if new:
            w.writeheader()
        w.writerow(dict(logged_at=now_gmt(), player_id=pid, player=p["player"], club=p["club"],
                        status=a.status, label=a.label, grade=a.grade, reason=a.reason,
                        source=a.source, source_date=a.source_date, by=a.by))
    print(f"logged {p['player']} ({p['club']}) {a.status} {a.label}/{a.grade} to gw{gw:02d}")


if __name__ == "__main__":
    main()

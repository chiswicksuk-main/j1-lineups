"""Start a new gameweek from the previous one.

Usage: python scripts/new_gw.py 16          (copies gw15/final.csv)
       python scripts/new_gw.py 16 --from 15

Creates gw/gw16/ with:
  base.csv          previous round's final XIs (step 1)
  availability.csv  empty, plus still-open OUT/SUSPENDED/DOUBT rows carried
                    from the previous round, marked for re-check (step 2)
  elgolazo.csv      empty template (step 3)
  overrides.csv     empty template (you)
Then points gw/CURRENT at the new round. Refuses to overwrite an existing round.
"""
import os
import sys
from common import (XI_COLS, AVAIL_COLS, ELGOLAZO_COLS, OVERRIDE_COLS, GWDIR,
                    gw_path, read_csv, write_csv, now_gmt)


def latest_by_player(events):
    out = {}
    for e in events:
        key = e["player_id"] or (e["club"], e["player"])
        prev = out.get(key)
        if prev is None or (e["source_date"], e["logged_at"]) >= (prev["source_date"], prev["logged_at"]):
            out[key] = e
    return out


def main(gw, prev):
    dest = gw_path(gw)
    if os.path.exists(dest):
        sys.exit(f"gw{gw:02d} already exists, not overwriting")
    prev_final = read_csv(gw_path(prev, "final.csv"))
    if not prev_final:
        sys.exit(f"gw{prev:02d}/final.csv missing or empty")

    base = [{**{c: r.get(c, "") for c in XI_COLS}} for r in prev_final]
    write_csv(gw_path(gw, "base.csv"), XI_COLS, base)

    carried = []
    for e in latest_by_player(read_csv(gw_path(prev, "availability.csv"))).values():
        if e["status"] in ("OUT", "SUSPENDED", "DOUBT"):
            c = dict(e)
            c["logged_at"] = now_gmt()
            c["label"] = "WATCH" if e["status"] != "OUT" else e["label"]
            c["reason"] = f"{e['reason']} [carried from GW{prev}, re-check]".strip()
            c["by"] = "new_gw"
            # one-match bans should not carry: flag so a human or agent checks
            if e["status"] == "SUSPENDED":
                c["reason"] += " [ban length unknown here, confirm]"
            carried.append(c)
    write_csv(gw_path(gw, "availability.csv"), AVAIL_COLS, carried)
    write_csv(gw_path(gw, "elgolazo.csv"), ELGOLAZO_COLS, [])
    write_csv(gw_path(gw, "overrides.csv"), OVERRIDE_COLS, [])
    with open(os.path.join(GWDIR, "CURRENT"), "w") as f:
        f.write(f"{gw}\n")
    print(f"gw{gw:02d} created from gw{prev:02d}: {len(base)} base rows, "
          f"{len(carried)} availability rows carried")


if __name__ == "__main__":
    a = sys.argv[1:]
    gw = int(a[0])
    prev = int(a[a.index("--from") + 1]) if "--from" in a else gw - 1
    main(gw, prev)

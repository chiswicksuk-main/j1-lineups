"""One-off import of a gameweek's XIs read from the Google Sheet club tabs.

Usage: python scripts/import_sheet_gw.py 15 import/gw15_slots.txt
Writes gw/gw15/final.csv (layer = sheet). Alternates are matched to an ID by
exact name within the same club. Anything unmatched is left blank and flagged.
"""
import sys
from common import XI_COLS, FINAL_COLS, gw_path, write_csv, players, clubs, pct


def main(gw, src):
    reg = players()
    by_name = {}
    for p in reg.values():
        by_name.setdefault((p["club"], p["player"]), []).append(p["player_id"])
    cl = clubs()
    rows = []
    for line in open(src, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        club, slot, pid, name, sp, alt, ap = line.split("|")
        flags = []
        if pid not in reg:
            flags.append("ID not in register")
        alt_id = ""
        if alt:
            ids = by_name.get((club, alt), [])
            if len(ids) == 1:
                alt_id = ids[0]
            else:
                flags.append(f"alternate '{alt}' not matched to an ID")
        rows.append(dict(club=club, club_id=cl.get(club, {}).get("club_id", ""),
                         slot=slot, player_id=pid, player=name,
                         start_pct=pct(sp) if sp else "", alt_id=alt_id, alt=alt,
                         alt_pct=pct(ap) if ap else "", layer="sheet",
                         flags="; ".join(flags)))
    write_csv(gw_path(gw, "final.csv"), FINAL_COLS, rows)
    print(f"wrote {len(rows)} rows to gw{int(gw):02d}/final.csv")
    bad = [r for r in rows if r["flags"]]
    for r in bad:
        print(" ", r["club"], r["slot"], r["player"], "->", r["flags"])


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])

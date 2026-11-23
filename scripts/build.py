"""Build final.csv for a gameweek from its layers, validate it, and write changes.md.

Usage: python scripts/build.py          (uses gw/CURRENT)
       python scripts/build.py 16

Layer order, per club:
  1. base.csv       previous round copied over
  2. availability   agents' dated, graded injury/suspension events
  3. elgolazo.csv   if the club has El Golazo rows, they replace the base XI
  4. overrides.csv  Matsu's calls, always win

Availability rules (never infer a return from silence, never let a rumour
silently beat the paper):
  - On the base XI, OUT/SUSPENDED graded A or B removes the starter. His
    alternate is promoted with Start % "?" for you to set. No alternate means
    the starter stays at 0% and the slot is flagged NEEDS PICK.
  - On an El Golazo XI, only a grade A event dated after the issue is applied.
    Anything else is flagged CONFLICT and left alone.
  - Grade C/D, DOUBT, or unlabelled news is flagged only.
"""
import sys
from collections import OrderedDict
from common import (XI_COLS, FINAL_COLS, STATUSES, LABELS, GRADES, gw_path,
                    read_csv, write_csv, players, clubs, current_gw, now_gmt, pct)

UNAVAILABLE = ("OUT", "SUSPENDED")


def latest_events(rows):
    out = {}
    for e in rows:
        pid = (e.get("player_id") or "").strip()
        if not pid:
            continue
        prev = out.get(pid)
        if prev is None or (e["source_date"], e["logged_at"]) >= (prev["source_date"], prev["logged_at"]):
            out[pid] = e
    return out


def group(rows):
    g = OrderedDict()
    for r in rows:
        g.setdefault(r["club"], []).append(dict(r))
    return g


def ev_text(e):
    return (f"{e['status']} {e.get('label','')}/{e.get('grade','')} "
            f"({e.get('reason','')}; {e.get('source','')} {e.get('source_date','')})").strip()


def build(gw):
    reg = players()
    cl = clubs()
    base = group(read_csv(gw_path(gw, "base.csv")))
    if not base:
        sys.exit(f"gw{gw:02d}/base.csv missing or empty, not building (would wipe final.csv)")
    elg = group(read_csv(gw_path(gw, "elgolazo.csv")))
    avail_rows = read_csv(gw_path(gw, "availability.csv"))
    events = latest_events(avail_rows)
    overrides = read_csv(gw_path(gw, "overrides.csv"))
    needs_you, problems = [], []

    # sanity-check the availability log itself
    for i, e in enumerate(avail_rows, start=2):
        bad = []
        if e.get("status") not in STATUSES:
            bad.append(f"status '{e.get('status')}'")
        if e.get("grade") and e["grade"] not in GRADES:
            bad.append(f"grade '{e['grade']}'")
        if e.get("label") and e["label"] not in LABELS:
            bad.append(f"label '{e['label']}'")
        if e.get("player_id") and e["player_id"] not in reg:
            bad.append(f"player_id {e['player_id']} not in register")
        if not e.get("player_id"):
            bad.append("no player_id (row ignored)")
        if bad:
            problems.append(f"availability.csv line {i} ({e.get('player','?')}): " + ", ".join(bad))

    final = []
    club_names = list(base.keys()) + [c for c in elg if c not in base]
    for club in club_names:
        if club in elg:
            xi = []
            for r in elg[club]:
                r = dict(r)
                r["club_id"] = r.get("club_id") or cl.get(club, {}).get("club_id", "")
                if not r.get("player_id"):
                    r["player_id"] = _id_for(reg, club, r.get("player", ""))
                if r.get("alt") and not r.get("alt_id"):
                    r["alt_id"] = _id_for(reg, club, r["alt"])
                r["start_pct"] = r.get("start_pct") or "90"
                r["layer"] = "elgolazo"
                r["_published"] = r.get("published", "")
                r["flags"] = []
                xi.append(r)
        else:
            xi = [dict(r, layer="base", flags=[], _published="") for r in base.get(club, [])]

        for r in xi:
            e = events.get(r["player_id"])
            if e and e["status"] in UNAVAILABLE:
                if r["layer"] == "base":
                    auto = e.get("grade") in ("A", "B")
                else:
                    auto = e.get("grade") == "A" and e["source_date"] > r["_published"]
                if auto:
                    alt_ev = events.get(r.get("alt_id", ""))
                    alt_ok = r.get("alt_id") and not (alt_ev and alt_ev["status"] in UNAVAILABLE)
                    if alt_ok:
                        r["flags"].append(f"{r['player']} removed: {ev_text(e)}. Alternate promoted, set Start %")
                        r["player_id"], r["player"] = r["alt_id"], r["alt"]
                        r["start_pct"], r["alt_id"], r["alt"], r["alt_pct"] = "?", "", "", ""
                        needs_you.append((club, r["slot"], f"{club} {r['slot']}: {r['player']} promoted, set Start %"))
                    else:
                        r["start_pct"] = "0"
                        r["flags"].append(f"NEEDS PICK: {r['player']} {ev_text(e)}, no usable alternate")
                        needs_you.append((club, r["slot"], f"{club} {r['slot']}: NEEDS PICK, {r['player']} {e['status']}"))
                else:
                    kind = "CONFLICT with El Golazo" if r["layer"] == "elgolazo" else "WATCH"
                    r["flags"].append(f"{kind}: {ev_text(e)}")
                    if r["layer"] == "elgolazo":
                        needs_you.append((club, r["slot"], f"{club} {r['slot']}: {r['player']} in El Golazo XI but {ev_text(e)}"))
            elif e and e["status"] == "DOUBT":
                r["flags"].append(f"DOUBT: {ev_text(e)}")
            a = events.get(r.get("alt_id", ""))
            if a and a["status"] in UNAVAILABLE and a.get("grade") in ("A", "B"):
                r["flags"].append(f"alternate {r['alt']} removed: {ev_text(a)}")
                r["alt_id"], r["alt"], r["alt_pct"] = "", "", ""
        final.extend(xi)

    # overrides always win
    idx = {(r["club"], r["slot"]): r for r in final}
    for o in overrides:
        key = (o["club"], o["slot"])
        r = idx.get(key)
        if r is None:
            problems.append(f"override for {o['club']} {o['slot']} matches no slot")
            continue
        pid = o.get("player_id") or (_id_for(reg, o["club"], o["player"]) if o.get("player") else "")
        if pid:
            r["player_id"] = pid
            r["player"] = o.get("player") or reg.get(pid, {}).get("player", "")
        for f in ("start_pct", "alt_id", "alt", "alt_pct"):
            v = (o.get(f) or "").strip()
            if v == "-":
                r[f] = ""
            elif v:
                r[f] = v
        if o.get("alt") and not o.get("alt_id"):
            r["alt_id"] = _id_for(reg, o["club"], o["alt"])
        r["layer"] = "override"
        needs_you = [n for n in needs_you if (n[0], n[1]) != key]
        r["flags"] = [f for f in r["flags"] if not f.startswith(("NEEDS PICK", "CONFLICT"))]
        r["flags"].append(f"override: {o.get('note','')}".strip())

    # validation
    for club, rows in group(final).items():
        ids = [r["player_id"] for r in rows]
        if len(rows) != 11:
            problems.append(f"{club}: {len(rows)} players, need 11")
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            problems.append(f"{club}: duplicate player(s) " + ", ".join(reg.get(d, {}).get("player", d) for d in dupes))
        for r in rows:
            p = reg.get(r["player_id"])
            if not r["player_id"]:
                problems.append(f"{club} {r['slot']}: no player ID for '{r['player']}'")
            elif p is None:
                problems.append(f"{club} {r['slot']}: {r['player']} ({r['player_id']}) not in register")
            elif p["club"] != club:
                problems.append(f"{club} {r['slot']}: {r['player']} is registered at {p['club']}")
            sp = pct(r.get("start_pct"))
            if r.get("start_pct") not in ("?",) and sp is not None and sp < 50 and r["layer"] != "override" and not r.get("alt"):
                r["flags"].append(f"ticked starter at {sp}% with no alternate, check")
            if r.get("alt") and not r.get("alt_id"):
                r["flags"].append(f"alternate '{r['alt']}' has no ID")

    needs_you = [n[2] for n in needs_you]
    for r in final:
        r["flags"] = "; ".join(r["flags"])
    write_csv(gw_path(gw, "final.csv"), FINAL_COLS, final)
    write_report(gw, base, final, needs_you, problems, len(avail_rows), set(elg))
    return final, needs_you, problems


def _id_for(reg, club, name):
    hits = [p["player_id"] for p in reg.values() if p["club"] == club and p["player"] == name]
    return hits[0] if len(hits) == 1 else ""


def write_report(gw, base, final, needs_you, problems, n_events, elg_clubs):
    lines = [f"# GW{gw} lineups", "", f"Built {now_gmt()} GMT. "
             f"{n_events} availability rows. El Golazo in for {len(elg_clubs)}/20 clubs.", ""]
    lines += ["## Needs you", ""] + ([f"- {x}" for x in needs_you] or ["- Nothing"]) + [""]
    lines += ["## Problems", ""] + ([f"- {x}" for x in problems] or ["- None"]) + [""]
    lines += ["## By club", ""]
    for club, rows in group(final).items():
        before = {r["player_id"] for r in base.get(club, [])}
        after = {r["player_id"] for r in rows}
        name = {r["player_id"]: r["player"] for r in base.get(club, []) + rows}
        src = "El Golazo" if club in elg_clubs else "GW base"
        if any(r["layer"] == "override" for r in rows):
            src += " + overrides"
        lines.append(f"### {club} ({src})")
        out_, in_ = before - after, after - before
        if out_ or in_:
            lines.append(f"- Out: {', '.join(name[i] for i in out_) or 'none'}. In: {', '.join(name[i] for i in in_) or 'none'}")
        for r in rows:
            if r["flags"]:
                lines.append(f"- {r['slot']} {r['player']}: {r['flags']}")
        if not (out_ or in_) and not any(r["flags"] for r in rows):
            lines.append("- No change")
        lines.append("")
    with open(gw_path(gw, "changes.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    gw = int(sys.argv[1]) if len(sys.argv) > 1 else current_gw()
    _, needs, probs = build(gw)
    print(f"GW{gw}: {len(needs)} need you, {len(probs)} problems")
    for x in needs + probs:
        print(" -", x)
    # problems do not fail the build: a half-finished round is normal mid-week

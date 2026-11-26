# J1 lineups

Predicted J1 XIs, one folder per gameweek, built from layers so no agent can overwrite Matsu's calls.

## Each round

1. **Copy last round over.** Actions tab, "build lineups", Run workflow, action `new_gw`, gw `17`. (Or `python scripts/new_gw.py 17`.) Open injuries and suspensions carry over marked for re-check.
2. **Injuries and suspensions.** Agents append to `gw/gw17/availability.csv`. Grade A/B OUT or SUSPENDED removes a base starter and promotes his alternate with Start % `?`.
3. **El Golazo.** Once the issue is in, its XI goes in `elgolazo.csv` and becomes the truth for that club.
4. **Your calls.** Add a row to `overrides.csv` (club, slot, then whatever you want to change). Overrides always win. `-` clears a field.
5. **Lock** at teamsheet time: run the workflow with action `lock`. That freezes `locked.csv` for scoring.

Every push rebuilds `final.csv` and `changes.md`. Read `changes.md`: "Needs you" is the to-do list.

## Files

```
data/players.csv     Flashscore ID register (from the Player Register tab)
data/clubs.csv       club IDs
gw/CURRENT           the live round
gw/gwNN/base.csv     previous round copied over
gw/gwNN/availability.csv  injury/suspension events (append only)
gw/gwNN/elgolazo.csv El Golazo XIs
gw/gwNN/overrides.csv     yours
gw/gwNN/final.csv    generated, the answer
gw/gwNN/changes.md   generated, what moved and why
gw/gwNN/locked.csv   frozen at teamsheet time
```

Rules for AIs are in `AGENTS.md`.

GW15 was imported from the "J1 Lineups GW15" sheet club tabs on 23 Nov 2026 (`import/gw15_slots.txt`). Start % values are editorial judgements, not calibrated probabilities.

GW17 base was imported from the "J1 Lineups GW17" sheet club tabs on 26 Nov 2026 (`import/gw17_slots.txt`, `python scripts/import_sheet_gw.py 17 import/gw17_slots.txt --base`). Blank Start % in the sheet is read as 90. GW16 was an auto-created copy of GW15 and is kept only as a record.

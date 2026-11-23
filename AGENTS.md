# Rules for any AI working in this repo (Claude, ChatGPT, Grok, anyone)

Read this before touching anything. Matsu owns the lineups. You supply evidence.

## What you may write

| File | Who writes it | How |
|---|---|---|
| `gw/gwNN/availability.csv` | agents, Matsu | **append only**, ideally via `scripts/log_availability.py` |
| `gw/gwNN/elgolazo.csv` | whoever reads that round's El Golazo (usually from Matsu's screenshots) | one row per starter per club, full XI only |
| `gw/gwNN/overrides.csv` | **Matsu only** | never written by an agent |
| `gw/gwNN/base.csv`, `final.csv`, `changes.md`, `locked.csv` | scripts only | never hand-edit |
| `data/players.csv` | Matsu, or an agent he has asked | IDs are Flashscore IDs |

## Availability rows

Columns: `logged_at, player_id, player, club, status, label, grade, reason, source, source_date, by`

- `status`: OUT, SUSPENDED, DOUBT, AVAILABLE
- `label`: CONFIRMED, LIKELY, WATCH, UNKNOWN
- `grade`: A official notice/team sheet, B named Japanese press or directly observed, C inference/manager hint/single secondary, D boards/rumour
- `source_date` is the date of the evidence, not today. `by` is your name.
- Match players by Flashscore ID from `data/players.csv`. If you cannot match exactly, do not guess: leave the row out and report it.
- Never delete or edit an old row. A correction is a new row with a later `source_date`.
- Never infer a return from silence. A return needs its own AVAILABLE row with a source.
- Never convert an absence into an injury. A missing player is UNKNOWN until there is evidence.
- Paid El Golazo/Targma detail can inform a row, but keep `source` to the outlet and issue, no copied text.

## El Golazo rows

Columns: `club, slot, player_id, player, start_pct, alt_id, alt, alt_pct, issue, published, by`

- Enter all 11 for a club or none. Use the same slot names as `base.csv` where possible.
- Bracketed alternates go in `alt`. Leave `start_pct` blank unless Matsu gave one (blank becomes 90).
- `published` is the issue date (YYYY-MM-DD). Later grade A news is applied, anything weaker is flagged as a conflict.

## Order of precedence

overrides > El Golazo > base adjusted by A/B availability news. C/D news is only ever a flag.

## Commits

Small commits, one source per commit, message like `avail: Hiroshima Kim Ju-sung DOUBT A (J.League R14)`.
Pushing triggers the build. Check `gw/gwNN/changes.md` afterwards for anything flagged.

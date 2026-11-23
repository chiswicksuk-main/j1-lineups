# Notes to paste into the other bots

## Grok (daily J1 intelligence brief)

Add to the end of the brief prompt:

> From now on, end every brief with a block called AVAILABILITY ROWS, one line per player item, in this exact format:
> `player | club | status | label | grade | reason | source | source_date`
> status is OUT, SUSPENDED, DOUBT or AVAILABLE. label is CONFIRMED, LIKELY, WATCH or UNKNOWN. grade is A to D on the shared scale. source_date is the date of the evidence (YYYY-MM-DD), not today. Use the romanised name exactly as in my Player Register where you know it. If nothing changed, write "AVAILABILITY ROWS: none". Do not include predicted XIs or percentages in this block.

Grok does not write to GitHub. Its rows reach the repo through the Hub and the Claude sync.

## ChatGPT (Daily Squad Review and the site builder)

> My predicted lineups are moving to a GitHub repo (chiswicksuk-main/j1-lineups). Nothing changes for you this week. Keep verifying and promoting items in the J1 Knowledge Hub exactly as now. Do not edit Start %, Label, Alternate or ticks in any GW tab, and do not write to the repo. A Claude task copies verified Hub rows into the repo. If you build anything on the site that shows predicted lineups, the future source is `gw/gwNN/final.csv` in that repo, not the sheet.

## Why only one writer

Grok finds, ChatGPT verifies in the Hub, Claude moves verified rows into `availability.csv`, the build decides, Matsu overrides. One writer per file means no two bots ever fight over the same cell.

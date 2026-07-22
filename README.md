# NZ Economic Watch — dashboard

A single-page dashboard that answers one question in plain English:
**is the "Korea → US market crash" story actually reaching New Zealand, and what
should I do about my money?** Built to track the Andrei Jikh video you sent
(`youtu.be/hy90LdpEUvQ`) and its reference videos.

## What's here

| File | What it is |
|---|---|
| `index.html` | The dashboard. Open it in any browser. Two tabs. |
| `data/market-data.js` | The live numbers. Auto-refreshed each weekday (see below). |
| `fetch_data.py` | The refresh script (stdlib only). |
| `../.github/workflows/refresh-market-data.yml` | Runs the script daily and commits the new data. |
| `FACT-CHECK.md` | Claim-by-claim fact-check of the video, with sources. |

## The two tabs

1. **Global & NZ Watch** — a single **warning level** (Calm → Watch → Elevated →
   High → Severe) computed from a handful of indicators (KOSPI, S&P 500, Nasdaq,
   the VIX fear gauge, NZX 50, the NZ dollar, dairy prices). Each indicator has a
   plain-English "what this means" line and a drawdown bar. A **domino chain**
   shows how a Seoul crash travels Korea → US → NZ → your bank account, lighting
   up the links that are actually moving today. A **structural** panel carries the
   video's real thesis (record US margin debt, the ~$750bn AI-capex loop, the
   Chanos return-on-investment figures) as slow-moving fragility gauges.

2. **Your Money (NZ)** — practical guidance for an ordinary NZ household across
   cash buffer, credit-card debt, mortgage, KiwiSaver/retirement, and savings.
   **The advice changes with the warning level** — the same engine that sets the
   level rewrites how hard to lean on each action. A plain-English glossary is at
   the bottom.

> **Not financial advice.** It's an educational tool built from public data. It
> doesn't know your situation — see a licensed NZ adviser for real decisions.

## How the daily refresh works

There are three layers, so the page is **never blank and never stale-by-surprise**:

1. **Seed / baseline** — real values (as at 21 Jul 2026) are embedded in
   `data/market-data.js` and inside `fetch_data.py`. If nothing else runs, the page
   still works and every number is a real, sourced figure.
2. **Automated daily refresh (the reliable path)** — the GitHub Action runs
   `fetch_data.py` every weekday ~07:30 NZ time. It pulls the latest index levels
   and the NZ dollar from **Stooq** (free, keyless), rewrites `market-data.js`, and
   commits it. The dashboard reads that file on load.
3. **Best-effort live nudge** — when you open the page online, it also tries a
   direct Stooq fetch to freshen prices intra-day. If your browser or network
   blocks it, it silently keeps the committed data. (Because of this, opening the
   file by double-click still shows the last committed numbers; a browser can't
   fetch a sibling file over `file://`, which is exactly why the data lives in a
   `.js` file loaded by a `<script>` tag rather than JSON.)

### Which numbers update automatically vs by hand

- **Daily, automatic:** KOSPI, S&P 500, Nasdaq, VIX, NZX 50, NZD/USD (values,
  previous close, and rolling 1-year peak for the drawdown bars).
- **By hand (they only change monthly/quarterly):** the NZ `context` (OCR,
  mortgage rates, KiwiSaver totals, Fonterra payout) and the `structural` gauges
  (US margin debt, hyperscaler capex, Chanos ROI). Edit the `BASELINE` dict at the
  top of `fetch_data.py` when a new print lands, and the next run ships it.

## Run it yourself

```bash
cd nz-economic-dashboard
python3 fetch_data.py        # refreshes data/market-data.js from Stooq
python3 -m http.server 8000  # then open http://localhost:8000
```

(A plain double-click on `index.html` also works — it just uses the last
committed data instead of doing a fresh fetch.)

## Tuning the warning engine

All the logic lives in one `<script>` block in `index.html`:

- `assess()` scores each indicator and sums to a 0–16 warning score → level band.
- `summaryText()` writes the daily plain-English paragraph from the data.
- `adviceModel()` returns the personal-finance guidance for each of the five
  levels. Change a threshold in `assess()` and both the summary and the money
  advice move with it — one brain, two dashboards.

## Data sources

Stooq (market prices) · RBNZ (OCR) · Global Dairy Trade / Fonterra (dairy) ·
FINRA via Advisor Perspectives (margin debt) · company filings / Tom's Hardware /
Statista (hyperscaler capex) · news wires (NBR, RNZ). Full source links are in
`FACT-CHECK.md`.

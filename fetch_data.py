#!/usr/bin/env python3
"""
fetch_data.py — regenerate data/market-data.js from live sources.

Design goals:
  * Standard library only (no pip install) so the GitHub Action is trivial.
  * NEVER produce a broken/empty dashboard: every field has a baseline, and if
    a live fetch fails we fall back to that baseline for THAT field only.
  * The slow-moving NZ context + the video's structural gauges live in the
    BASELINE dict below and are hand-maintained (edit here when new prints land:
    FINRA margin debt monthly, hyperscaler capex quarterly, RBNZ OCR, GDT).

Data source for the daily market indicators: Stooq (stooq.com) CSV endpoints,
which are free, keyless and CORS-friendly. Symbols can change; if one stops
resolving the script keeps that indicator's baseline and logs a warning.

Run locally:   python3 fetch_data.py
In CI:         see .github/workflows/refresh-market-data.yml
"""
import csv, io, json, sys, urllib.request, datetime, re

# --- BASELINE (matches data/market-data.js seed; the safety net) -------------
BASELINE = {
  "indicators": {
    "kospi":  {"label":"KOSPI","country":"South Korea","flag":"🇰🇷","value":7474,"prevClose":7620,"peak52w":9000,"unit":"pts","stooq":"^kospi"},
    "spx":    {"label":"S&P 500","country":"USA","flag":"🇺🇸","value":7437,"prevClose":7458,"peak52w":7520,"unit":"pts","stooq":"^spx"},
    "ndq":    {"label":"Nasdaq Composite","country":"USA (tech)","flag":"🇺🇸","value":24050,"prevClose":24080,"peak52w":24800,"unit":"pts","stooq":"^ndq"},
    "vix":    {"label":"VIX — Wall St fear gauge","country":"USA","flag":"🌡️","value":18.77,"prevClose":17.90,"peak52w":None,"unit":"","stooq":"^vix"},
    "nzx50":  {"label":"NZX 50","country":"New Zealand","flag":"🇳🇿","value":13679,"prevClose":13710,"peak52w":13860,"unit":"pts","stooq":"^nz50"},
    "nzdusd": {"label":"NZD / USD","country":"New Zealand","flag":"💵","value":0.578,"prevClose":0.576,"ref1m":0.588,"peak52w":None,"unit":"","stooq":"nzdusd"},
    "gdt":    {"label":"Global Dairy Trade (last auction)","country":"New Zealand","flag":"🥛","value":-4.9,"kind":"event_pct","wmp":3425,"prevEvent":-1.2,"unit":"%"},
  },
  "context": {
    "ocr":2.50,"ocrChangedDate":"2026-07-08","ocrDirection":"up",
    "inflation":3.9,"inflationTarget":2.0,
    "mortgageAvgYield":5.4,"mortgage1yrFixed":5.1,"mortgageFloating":6.9,
    "termDeposit1yr":4.3,
    "kiwisaverTotalB":138.8,"kiwisaverMembersM":3.3,
    "kiwisaverOffshoreB":86,"kiwisaverUSEquityB":35,
    "fonterraPayout":9.25,"fonterraPayoutPrev":9.75,
  },
  "structural": {
    "marginDebtGdp":{"value":4.71,"prevValue":4.55,"record":True,"asOf":"Jun 2026","label":"US margin debt vs GDP","note":"All-time record. Borrowed money buying US shares."},
    "marginDebtT":{"value":1.53,"asOf":"Jun 2026","label":"US margin debt (total)","unit":"T"},
    "hyperscalerCapexB":{"value":725,"prevValue":410,"asOf":"2026 est","label":"Big-4 AI capex / yr","note":"MSFT+GOOG+AMZN+META. +77% YoY. ~75% is AI."},
    "capexRoiCents":{"value":20,"from":40,"toward":10,"label":"Return per $ of AI spend","note":"Chanos: was ~40¢, now ~20¢, heading to ~10¢."},
    "spxTop10Pct":{"value":36,"label":"Top-10 = % of S&P 500","note":"Record US concentration."},
  },
}

STOOQ_HIST = "https://stooq.com/q/d/l/?s={sym}&i=d"   # full daily history CSV

def fetch_history(sym):
    """Return list of (date, close) rising by date, or None on failure."""
    url = STOOQ_HIST.format(sym=urllib.parse.quote(sym))
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"nz-econ-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")
        rows = list(csv.DictReader(io.StringIO(text)))
        out = []
        for row in rows:
            c = row.get("Close") or row.get("close")
            d = row.get("Date") or row.get("date")
            if c and c not in ("N/D","",) :
                out.append((d, float(c)))
        return out or None
    except Exception as e:
        print(f"  ! {sym}: {e}", file=sys.stderr)
        return None

def refresh(data):
    live_any = False
    today = datetime.date.today()
    for key, ind in data["indicators"].items():
        sym = ind.get("stooq")
        if not sym:
            continue
        hist = fetch_history(sym)
        if not hist or len(hist) < 2:
            print(f"  - {key}: kept baseline (no live data)")
            continue
        ind["value"] = round(hist[-1][1], 4)
        ind["prevClose"] = round(hist[-2][1], 4)
        # rolling ~52-week peak from the last 260 trading days
        if ind.get("peak52w") is not None:
            window = [c for _, c in hist[-260:]]
            ind["peak52w"] = round(max(window), 4)
        live_any = True
        print(f"  ✓ {key}: {ind['value']} (prev {ind['prevClose']})")
    return live_any

def write_js(data, live):
    # strip the internal "stooq" helper keys from the shipped file
    inds = {k: {kk: vv for kk, vv in v.items() if kk != "stooq"} for k, v in data["indicators"].items()}
    payload = {
        "updated": datetime.date.today().isoformat(),
        "source": "live" if live else "seed",
        "note": "Auto-generated by fetch_data.py. Slow-moving fields edited in the script.",
        "indicators": inds,
        "context": data["context"],
        "structural": data["structural"],
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    header = ("/* AUTO-GENERATED by fetch_data.py — do not hand-edit the numbers here.\n"
              "   Loaded by index.html via <script>. See fetch_data.py to change baselines. */\n")
    return header + "window.MARKET_DATA = " + body + ";\n"

if __name__ == "__main__":
    print("Refreshing market indicators from Stooq…")
    live = refresh(BASELINE)
    out = write_js(BASELINE, live)
    with open("data/market-data.js", "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote data/market-data.js (source={'live' if live else 'seed'})")

#!/usr/bin/env python3
"""
fetch_data.py — regenerate data/market-data.js from live sources.

Primary source: Yahoo Finance chart API (query1.finance.yahoo.com) — reliable
from CI/datacenter IPs, no API key. Fallback: Stooq CSV. If both fail for an
indicator, its hand-entered baseline is kept, so the dashboard is never blank.

Standard library only (no pip install). Run: python3 fetch_data.py
"""
import csv, io, json, sys, urllib.request, urllib.parse, datetime

# --- BASELINE (safety net; also holds the slow-moving NZ + structural data) --
BASELINE = {
  "indicators": {
    "kospi":  {"label":"KOSPI","country":"South Korea","flag":"🇰🇷","value":7474,"prevClose":7620,"peak52w":9000,"unit":"pts",
               "yahoo":["^KS11"], "stooq":"^kospi"},
    "spx":    {"label":"S&P 500","country":"USA","flag":"🇺🇸","value":7437,"prevClose":7458,"peak52w":7520,"unit":"pts",
               "yahoo":["^GSPC"], "stooq":"^spx"},
    "ndq":    {"label":"Nasdaq Composite","country":"USA (tech)","flag":"🇺🇸","value":24050,"prevClose":24080,"peak52w":24800,"unit":"pts",
               "yahoo":["^IXIC"], "stooq":"^ndq"},
    "vix":    {"label":"VIX — Wall St fear gauge","country":"USA","flag":"🌡️","value":18.77,"prevClose":17.90,"peak52w":None,"unit":"",
               "yahoo":["^VIX"], "stooq":"^vix"},
    "nzx50":  {"label":"NZX 50","country":"New Zealand","flag":"🇳🇿","value":13679,"prevClose":13710,"peak52w":13860,"unit":"pts",
               "yahoo":["^NZ50","^NZX50"], "stooq":"^nz50"},
    "nzdusd": {"label":"NZD / USD","country":"New Zealand","flag":"💵","value":0.578,"prevClose":0.576,"ref1m":0.588,"peak52w":None,"unit":"",
               "yahoo":["NZDUSD=X"], "stooq":"nzdusd"},
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

UA = {"User-Agent": "Mozilla/5.0 (compatible; nz-econ-dashboard/1.0)"}

def _get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)

def yahoo_series(sym):
    """(value, prevClose, peak52w) from Yahoo chart API, or None."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=1y&interval=1d"
    try:
        with _get(url) as r:
            data = json.load(r)
        res = data["chart"]["result"][0]
        meta = res.get("meta", {})
        closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
        if not closes:
            return None
        value = meta.get("regularMarketPrice") or closes[-1]
        prev = closes[-2] if len(closes) >= 2 else meta.get("chartPreviousClose", closes[-1])
        peak = max(closes + [value])
        return (float(value), float(prev), float(peak))
    except Exception as e:
        print(f"    yahoo {sym}: {e}", file=sys.stderr)
        return None

def stooq_series(sym):
    """(value, prevClose, peak52w) from Stooq history CSV, or None."""
    url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(sym)}&i=d"
    try:
        with _get(url) as r:
            rows = list(csv.DictReader(io.StringIO(r.read().decode("utf-8", "replace"))))
        closes = [float(x["Close"]) for x in rows if x.get("Close") not in (None, "", "N/D")]
        if len(closes) < 2:
            return None
        return (closes[-1], closes[-2], max(closes[-260:]))
    except Exception as e:
        print(f"    stooq {sym}: {e}", file=sys.stderr)
        return None

def refresh(data):
    live_any = False
    for key, ind in data["indicators"].items():
        if "yahoo" not in ind and "stooq" not in ind:
            continue
        series = None
        for sym in ind.get("yahoo", []):
            series = yahoo_series(sym)
            if series:
                break
        if not series and ind.get("stooq"):
            series = stooq_series(ind["stooq"])
        if not series:
            print(f"  - {key}: kept baseline (no live data)")
            continue
        value, prev, peak = series
        ind["value"] = round(value, 4)
        ind["prevClose"] = round(prev, 4)
        if ind.get("peak52w") is not None:
            ind["peak52w"] = round(peak, 4)
        live_any = True
        print(f"  ✓ {key}: {ind['value']} (prev {ind['prevClose']})")
    return live_any

def write_js(data, live):
    inds = {k: {kk: vv for kk, vv in v.items() if kk not in ("yahoo", "stooq")}
            for k, v in data["indicators"].items()}
    payload = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
        "source": "live" if live else "seed",
        "note": "Auto-generated by fetch_data.py. Slow-moving fields edited in the script.",
        "indicators": inds,
        "context": data["context"],
        "structural": data["structural"],
    }
    header = ("/* AUTO-GENERATED by fetch_data.py — do not hand-edit the numbers here.\n"
              "   Loaded by index.html via <script>. See fetch_data.py to change baselines. */\n")
    return header + "window.MARKET_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"

if __name__ == "__main__":
    print("Refreshing market indicators (Yahoo Finance, Stooq fallback)…")
    live = refresh(BASELINE)
    with open("data/market-data.js", "w", encoding="utf-8") as f:
        f.write(write_js(BASELINE, live))
    print(f"Wrote data/market-data.js (source={'live' if live else 'seed'})")

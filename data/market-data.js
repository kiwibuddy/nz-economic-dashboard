/* ============================================================================
 * market-data.js  —  the ONLY place live numbers live.
 * ----------------------------------------------------------------------------
 * This file is loaded by index.html via a <script> tag (so it works even from
 * a double-clicked file:// page, where fetch() of a local JSON is blocked).
 *
 * It is REGENERATED automatically each weekday by fetch_data.py, run by the
 * GitHub Action in .github/workflows/refresh-market-data.yml. You never edit
 * the numbers by hand — but if you want to, they're all right here.
 *
 * "source": "seed"  -> hand-entered baseline snapshot (below)
 * "source": "live"  -> last written by the automated fetch
 *
 * Every value below is a REAL figure as at ~20–21 July 2026, sourced in
 * FACT-CHECK.md. Peaks (peak52w) let the dashboard compute drawdowns live.
 * ==========================================================================*/
window.MARKET_DATA = {
  updated: "2026-07-21",
  source: "seed",
  note: "Baseline snapshot. Refreshes each weekday via GitHub Action.",

  // --- The moving indicators the warning engine reads --------------------
  indicators: {
    kospi:  { label: "KOSPI",            country: "South Korea", flag: "🇰🇷",
              value: 7474,  prevClose: 7620,  peak52w: 9000, unit: "pts" },
    spx:    { label: "S&P 500",          country: "USA",         flag: "🇺🇸",
              value: 7437,  prevClose: 7458,  peak52w: 7520, unit: "pts" },
    ndq:    { label: "Nasdaq Composite", country: "USA (tech)",  flag: "🇺🇸",
              value: 24050, prevClose: 24080, peak52w: 24800, unit: "pts" },
    vix:    { label: "VIX — Wall St fear gauge", country: "USA", flag: "🌡️",
              value: 18.77, prevClose: 17.90, peak52w: null,  unit: "" },
    nzx50:  { label: "NZX 50",           country: "New Zealand", flag: "🇳🇿",
              value: 13679, prevClose: 13710, peak52w: 13860, unit: "pts" },
    nzdusd: { label: "NZD / USD",        country: "New Zealand", flag: "💵",
              value: 0.578, prevClose: 0.576, ref1m: 0.588,  peak52w: null, unit: "" },
    gdt:    { label: "Global Dairy Trade (last auction)", country: "New Zealand", flag: "🥛",
              value: -4.9, kind: "event_pct", wmp: 3425, prevEvent: -1.2, unit: "%" }
  },

  // --- Slower-moving NZ context (updated less often; drives Your Money tab)
  context: {
    ocr: 2.50, ocrChangedDate: "2026-07-08", ocrDirection: "up",
    inflation: 3.9, inflationTarget: 2.0,
    mortgageAvgYield: 5.4, mortgage1yrFixed: 5.1, mortgageFloating: 6.9,
    termDeposit1yr: 4.3,
    kiwisaverTotalB: 138.8, kiwisaverMembersM: 3.3,
    kiwisaverOffshoreB: 86, kiwisaverUSEquityB: 35,
    fonterraPayout: 9.25, fonterraPayoutPrev: 9.75
  },

  // --- The video's structural thesis (slow-moving: monthly / quarterly) -----
  // These don't refresh daily. They're the "how fragile is the ground?" layer
  // the video actually argues, kept honest and sourced. Updated when new data
  // prints (FINRA monthly; capex quarterly).
  structural: {
    marginDebtGdp:  { value: 4.71, prevValue: 4.55, record: true, asOf: "Jun 2026",
                      label: "US margin debt vs GDP", note: "All-time record. Borrowed money buying US shares." },
    marginDebtT:    { value: 1.53, asOf: "Jun 2026", label: "US margin debt (total)", unit: "T" },
    hyperscalerCapexB:{ value: 725, prevValue: 410, asOf: "2026 est", label: "Big-4 AI capex / yr",
                      note: "MSFT+GOOG+AMZN+META. +77% YoY. ~75% is AI." },
    capexRoiCents:  { value: 20, from: 40, toward: 10, label: "Return per $ of AI spend",
                      note: "Chanos: was ~40¢, now ~20¢, heading to ~10¢." },
    spxTop10Pct:    { value: 36, label: "Top-10 = % of S&P 500", note: "Record US concentration." }
  }
};

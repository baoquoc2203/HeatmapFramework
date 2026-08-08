# Crypto Reconnaissance Engine — Interactive Dashboards

Interactive heatmap dashboards combining the framework's timing layers (Shmita,
Mercury Retrograde, Fear & Greed) and a retrospective Wyckoff structural map
against real price history, for **BTC (Jan 2014 → present, forward calendar to
Sep 2029)** and **ADA (Sep 2017 → present, forward cone to Dec 2028)**.

**Live demo:** open `index.html` directly in any browser, or enable GitHub
Pages on this repo (Settings → Pages → Deploy from branch → `main` → `/ (root)`)
to get a hosted link.

## Structure

| File | Purpose |
| --- | --- |
| `index.html` | Landing page — token switcher showing each asset's current Wyckoff phase, confidence and last tracked price |
| `btc-dashboard.html` | BTC interactive heatmap + price chart, with the current report's level ladder |
| `ada-dashboard.html` | ADA interactive heatmap + price chart, with the current report's level ladder and its forward volatility cone |
| `BTC_report_*.html` | The authoritative BTC analysis for the current date |
| `ADA_monthly_map_*.html` | The authoritative ADA monthly strategy map for the current date |
| `cardano-logo.svg` | ADA mark used by the ADA dashboard and landing page |

There is exactly **one authoritative report per asset** at any time. When a newer
report supersedes it, the old file is removed and every reference is updated in
the same change, so no stale analysis remains reachable.

Every page is self-contained — inline CSS and JS, no build step, and no external
dependencies or CDN scripts.

## What's real vs. retrospective

- **Price** — real monthly closes anchored to public price history; the current
  month is month-to-date from the report's authoritative exchange feed. Months
  beyond the present carry no price data and are drawn only as forecast bands or
  forward calendar.
- **Fear & Greed** — real Alternative.me index (launched Feb 2018, so earlier
  months genuinely have no reading), regime-anchored to documented extremes. It
  is the crypto-wide, BTC-driven index; on the ADA dashboard it is market
  context, not an ADA-specific signal.
- **Mercury Retrograde** — real astronomical retrograde windows (calendar
  on/off, not an invented intensity score). Zero predictive weight.
- **Shmita** — real Hebrew-calendar release years. The BTC dashboard covers
  **5775** (Sep'14–Sep'15), **5782** (Sep'21–Sep'22) and the forward **5789**
  (Sep 2028–Sep 2029); the ADA dashboard covers 5782 and the opening months of
  5789 that fall inside its horizon. The two completed observations produced
  *opposite* outcomes, which is the empirical case for zero-weighting it
  directionally.
- **Wyckoff cycle map** — retrospective phase labeling (Accumulation / Markup /
  Distribution / Markdown) derived month-by-month from the price line above.
  This is **not** a live backtest — a dashed cyan seam marks where the
  framework's own real-time tracking begins; everything left of it is
  retrospective context, everything right of it is the framework's actual
  reported calls.
- **Level ladder** — forward-looking price references quoted from the current
  report, not price history. Both dashboards carry one.
- **Zone Layer** (BTC) — pre-registered price bands whose bounds are *immutable
  once issued*, so that a touch becomes a scoreable event rather than a story
  told afterwards. Drawn through the same component as the level ladder but
  dimmed, because they are scoring objects rather than trading levels. Note the
  report's own disclosure that the uncovered gap between the zones contains
  every active trigger, so the operating range is currently unscoreable under
  the layer's own rules.
- **Confidence** — the BTC framework (CRE v2.1) computes confidence **per
  horizon class — tactical / swing / cycle — and never blends them**, so the
  landing card shows all three rather than inventing a single number. ADA still
  issues one composite score. The card renders whichever shape its asset
  actually reports.
- **ADA volatility cone** — the ADA report's own forward distribution, computed
  from its stated realized σ rather than transcribed: driftless lognormal,
  anchored at spot, with a **flat median by construction** because no drift is
  assumed. Hovering a forecast month gives its 5th/25th/75th/95th percentiles
  and its probability split against the two fixed campaign thresholds. These are
  month-end distributions, **not price targets**.

No buy/sell signal markers, liquidity-regime classifications, or "hit rate"
statistics are included — those would require either fabricated data or a
sample size too small to be meaningful, so they're left out rather than
dressed up to look more complete than they are.

## How to use

- **Drag / swipe** to pan across time
- **Scroll / pinch** to zoom in or out; **double-click** resets the view
- **Hover or tap** any cell or price point for an exact tooltip
- **Layer toggles** show/hide Wyckoff, Shmita, Mercury, Fear & Greed and the
  report's level ladder independently
- **Zoom presets** — BTC: full range, 2014–17, 2021–23, live window, reset;
  ADA: full range, 2020–22, live window, reset
- **Log / Linear** price scale toggle
- **Light / Dark** theme toggle, remembered across visits
- **Report button** opens the current authoritative report; each report links
  back to its dashboard

## Local preview

```bash
python3 -m http.server 3000
```

Then open <http://localhost:3000/index.html>.

## Disclaimer

Structural and contextual analysis only — not financial advice.

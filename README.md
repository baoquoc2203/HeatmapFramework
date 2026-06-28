# BTC Framework Dashboard — Interactive

An interactive heatmap dashboard combining the Crypto Reconnaissance Engine's
timing layers (Shmita, Mercury Retrograde, Fear & Greed) and a retrospective
Wyckoff structural map against real Bitcoin price history, Jan 2018 → present.

**Live demo:** open `index.html` directly in any browser, or enable GitHub
Pages on this repo (Settings → Pages → Deploy from branch → `main` → `/ (root)`)
to get a hosted link.

## What's real vs. retrospective

- **BTC price** — monthly closes, anchored to public price data; June of the
  current year is month-to-date from live exchange data.
- **Fear & Greed** — real Alternative.me index (live since Feb 2018),
  regime-anchored to documented extremes.
- **Mercury Retrograde** — real astronomical retrograde windows (calendar
  on/off, not an invented intensity score).
- **Shmita** — real Hebrew-calendar year boundary (5782 = Sep 2021–Sep 2022).
- **Wyckoff cycle map** — retrospective phase labeling (Accumulation / Markup /
  Distribution / Markdown) derived month-by-month from the price line above,
  following how the Wyckoff method is conventionally applied to BTC's known
  history. This is **not** a live backtest — a dashed cyan seam marks where
  the framework's own real-time tracking begins; everything left of it is
  retrospective context, everything right of it is the framework's actual
  reported calls.

No buy/sell signal markers, liquidity-regime classifications, or "hit rate"
statistics are included — those would require either fabricated data or a
sample size too small to be meaningful, so they're left out rather than
dressed up to look more complete than they are.

## How to use

- **Drag** to pan across time
- **Scroll / pinch** to zoom in or out
- **Hover** any cell or price point for an exact tooltip
- **Layer toggle buttons** to show/hide Wyckoff, Shmita, Mercury, Fear & Greed independently
- **Zoom presets** for the full range, the 2021–23 cycle, or the live-tracked window
- **Log / Linear** price scale toggle

## Disclaimer

Structural and contextual analysis only — not financial advice.

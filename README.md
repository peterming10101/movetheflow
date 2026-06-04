# Movetheflow Orderflow Platform

Full-surface rebuild of a BTCUSDT Binance USD-M Futures orderflow analytics platform.

The backend owns exchange ingestion, normalization, order-book reconstruction,
local persistence, derived live state, candles, DOM snapshots, executed prints,
profiles, footprint data, Speed Tape, VWAP, Time and Sales, and metrics. The
frontend consumes backend APIs/WebSockets only; it never connects directly to
Binance.

## Run Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If the backend is not on port `8000`, point the frontend at it:

```powershell
$env:NEXT_PUBLIC_BACKEND_URL="http://127.0.0.1:8005"
npm run dev -- --port 3002
```

## Workspace

The trading workspace includes:

- Main live candlestick chart.
- 1m and 5m timeframes plus chart-mode controls for Time, Tick, Volume, Dollar,
  Range, and Footprint views.
- Live candle updates derived from normalized trades.
- Session-style profile and delta profile overlay.
- Market-order bubbles.
- VWAP line.
- Speed Tape lower indicator.
- DOM ladder with bid/ask depth, profile/delta, and executed buy/sell prints.
- Right-side Time and Sales tape, newest first.
- Time footprint panel.
- Pause/resume live updates.
- Refresh snapshots.
- Compact backend status strip for trades, candles, depth, and recorder queue.

## Backend Endpoints

- `GET /api/candles/time?timeframe=60&limit=180`
- `GET /api/trades/recent?limit=150`
- `GET /api/workspace?timeframe=60&limit=240&priceStep=5`
- `WS /api/ws/candles/time?timeframe=60`
- `WS /api/ws/trades`
- `GET /api/diagnostics`
- `GET /api/metrics/market-data`

## Current Scope

- Binance raw trade ingestion.
- Binance depth snapshot plus diff ingestion.
- Canonical normalized trade stream and depth stream.
- SQLite/WAL persistence for trades and recorder state.
- Recorder and market-data metrics.
- Time candles from the canonical trade stream.
- Main chart, DOM, profile, bubbles, Speed Tape, Time and Sales, VWAP, and time
  footprint surface.

Non-goals for the current build: order execution, alerts, backtesting, account
state, and automation.

## Checks

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

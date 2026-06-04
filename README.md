# Movetheflow Orderflow Platform

Phase 2 rebuild of a BTCUSDT Binance USD-M Futures orderflow analytics platform.

The backend owns exchange ingestion, normalization, order-book reconstruction,
local persistence, derived live state, candle aggregation, Time and Sales, and
metrics. The frontend consumes backend APIs/WebSockets only; it never connects
directly to Binance.

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

## Phase 2 Workspace

The first usable trading workspace includes:

- Main live candlestick chart.
- 1m and 5m timeframes.
- Live candle updates derived from normalized trades.
- Right-side Time and Sales tape, newest first.
- Pause/resume live updates.
- Refresh snapshots.
- Compact backend status strip for trades, candles, depth, and recorder queue.

## Backend Endpoints

- `GET /api/candles/time?timeframe=60&limit=180`
- `GET /api/trades/recent?limit=150`
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
- Main chart and Time and Sales tape.

Non-goals for the current phase: DOM ladder UI, profiles, indicators, generated
candles, footprint charts, execution, alerts, backtesting, account state, and
automation.

## Checks

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

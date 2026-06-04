# Movetheflow Orderflow Platform

Phase 1 rebuild of a BTCUSDT Binance USD-M Futures orderflow analytics platform.

The backend owns exchange ingestion, normalization, order-book reconstruction,
local persistence, derived live state, and metrics. The frontend is intentionally
diagnostic only in Phase 1.

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

## Phase 1 Scope

- Binance aggregate trade ingestion.
- Binance depth snapshot plus diff ingestion.
- Canonical normalized trade stream and depth stream.
- SQLite/WAL persistence for trades and recorder state.
- Recorder and market-data metrics.
- Tiny diagnostic frontend only.

Non-goals: charting, DOM ladder UI, profile, indicators, execution, alerts,
backtesting, account state, automation.

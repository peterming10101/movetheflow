# Handoff

## Phase 1 Architecture

Data ownership is explicit:

- `app.exchanges.binance_futures` fetches and normalizes Binance payloads.
- `TradeBus` is the only internal live trade stream.
- `DepthBus` is the only internal live depth stream.
- `DepthManager` owns Binance order-book reconstruction and sequence checks.
- `SQLiteRecorder` persists normalized trades and recorder metadata.
- API routes expose state and metrics without reinterpreting market data.

The diagnostic frontend reads backend snapshots from `/api/diagnostics` and
`/api/metrics/market-data`. It does not connect to Binance.

## Run Checks

```powershell
cd backend
python -m pytest
```

## Known Phase 1 Limits

- Live validation requires public Binance futures network access.
- Depth persistence is deferred behind repository boundaries.
- The frontend is a status panel, not the trading UI.

## Phase 1 Validation Evidence

Automated checks on 2026-06-04:

```powershell
cd backend
python -m pytest -q
# 10 passed

cd frontend
npm run build
# production build completed successfully
```

Live BTCUSDT validation was run with backend on `127.0.0.1:8003` and frontend on
`127.0.0.1:3000`. Over a 60 second polling window:

- `trade_ws_messages_received` increased from `7981` to `25233`.
- `trade_messages_normalized` increased from `7981` to `25233`.
- `trade_messages_persisted` increased from `2336` to `9543`.
- `depth_ws_messages_received` increased from `326` to `915`.
- `depth_updates_applied` increased from `325` to `914`.
- `depth_resync_count` stayed flat at `1`.
- `depth_status` stayed `synced`.
- `depthLastUpdateId` advanced from `10708669971462` to `10708681257145`.
- `recorder_queue_size` ended at `0`.

SQLite evidence:

- DB path: `backend/data/market_data.db`.
- `PRAGMA journal_mode` returned `wal`.
- Live trade table contained `89136` rows at inspection time.
- Latest persisted trade at inspection time: trade id `7729831365`.

Frontend browser validation:

- Diagnostic page rendered at `http://127.0.0.1:3000`.
- Page showed `BTCUSDT`, `Synced`, `Latest Trade`, and `Recorder`.
- Browser console errors: none.
- Screenshot artifact: `C:\Users\Riley\Documents\Movetheflow\phase1-diagnostics.png`.

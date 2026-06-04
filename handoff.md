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

## Phase 2 Architecture

Phase 2 adds the first chart-and-tape workspace while preserving Phase 1 data
ownership:

- `TimeCandleEngine` derives live time candles from canonical `TradeBus` trades.
- `GET /api/candles/time` returns the live-buffer candle snapshot with explicit
  `live_only` coverage.
- `GET /api/trades/recent` returns newest-first normalized trades from the
  backend live buffer.
- `WS /api/ws/candles/time` streams backend-derived live candle updates.
- `WS /api/ws/trades` streams canonical normalized trades for Time and Sales.
- The frontend consumes only backend `/api` and `/api/ws` endpoints.

Phase 2 intentionally does not add DOM, profiles, indicators, generated candles,
execution, alerts, or direct exchange access from the browser.

## Phase 2 Validation Evidence

Automated checks on 2026-06-04:

```powershell
cd backend
python -m pytest -q
# 13 passed

cd frontend
npm run build
# production build completed successfully
```

Live BTCUSDT validation was run with backend on `127.0.0.1:8005` and frontend on
`127.0.0.1:3002`.

- `GET /api/candles/time?timeframe=60&limit=5` returned live candles.
- Latest candle had sane price bounds: low `63103.7`, high `63174.1`.
- `GET /api/trades/recent?limit=5` returned newest-first normalized trades.
- `trade_ws_messages_received`: `5368`.
- `trade_messages_normalized`: `5366`.
- `trade_messages_rejected`: `2` non-positive trade payloads rejected.
- `candle_updates_published`: `10732`.
- `depth_status`: `synced`.
- `recorder_queue_size`: `1`.

Browser validation at `http://127.0.0.1:3002` showed:

- `BTCUSDT`
- `Main Chart`
- `Time and Sales`
- `Live`
- `Candles`
- Browser console errors: none.

Local dev CORS now permits `localhost` and `127.0.0.1` on arbitrary ports via
regex so validation can use throwaway frontend ports without editing backend
config.

Known Phase 2 limits:

- Candle history is live-buffer only and labelled `live_only`.
- SQLite-backed candle history is deferred to the next backend hardening task.
- The chart renderer is a lightweight SVG candlestick renderer, not yet
  `lightweight-charts`.

## Full Surface Build

The platform no longer follows the original phase gates. The current build adds
a broad live workspace modeled on the provided reference image:

- Backend `/api/workspace` snapshot with candles, recent trades, DOM rows,
  trade-derived profile/delta profile, market-order bubbles, Speed Tape,
  time-footprint levels, VWAP, coverage metadata, and latest depth.
- Frontend chart/profile/speed stack, right-side DOM ladder, far-right Time and
  Sales tape, toolbar chart modes, and optional footprint panel.
- DOM bid/ask state is derived from backend depth only.
- Executed buy/sell prints, profile, speed tape, bubbles, VWAP, and footprint
  data are derived from canonical normalized trades.
- Frontend still has no direct Binance connectivity.

Validation evidence on 2026-06-04:

```powershell
cd backend
python -m pytest -q
# 13 passed

cd frontend
npm run build
# production build completed successfully
```

Live validation ran with backend on `127.0.0.1:8006` and frontend on
`127.0.0.1:3003`.

- `/api/workspace` returned `2` candles, `200` trades, `111` DOM rows, `9`
  profile rows, `2` bubbles, `17` speed-tape bars, `1` footprint candle, and
  VWAP bands.
- Depth status was `synced`.
- `trade_ws_messages_received`: `6851`.
- `trade_messages_normalized`: `6838`.
- `trade_messages_rejected`: `13`.
- `candle_updates_published`: `13676`.
- Browser validation showed `BTCUSDT`, `DOM`, `Time and Sales`, `Main Chart`,
  `Speed Tape`, and the `Footprint` option.
- Browser console errors: none.

Known full-surface limits:

- Generated Tick/Volume/Dollar/Range chart modes are present in the toolbar but
  still render the live time-candle stream until dedicated generated engines are
  wired.
- DOM clear is currently frontend-local for the visible executed-print columns.
- Profile/session coverage remains `live_only` until persisted session backfill
  and 08:00 UTC+8 coverage auditing are added.

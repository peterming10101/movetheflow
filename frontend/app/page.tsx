"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { MainChart } from "../components/MainChart";
import { TimeAndSales } from "../components/TimeAndSales";
import { Toolbar } from "../components/Toolbar";
import { DomPanel } from "../components/DomPanel";
import { FootprintPanel } from "../components/FootprintPanel";
import {
  connectCandleStream,
  connectTradeStream,
  getDiagnostics,
  getMarketMetrics,
  getRecentTrades,
  getTimeCandles,
  getWorkspace,
} from "../lib/api";
import type { DiagnosticSnapshot, Metrics, TimeCandle, Trade, WorkspaceSnapshot } from "../lib/types";

export default function Page() {
  const [timeframeSec, setTimeframeSec] = useState(60);
  const [chartMode, setChartMode] = useState("Time");
  const [live, setLive] = useState(true);
  const [domHidden, setDomHidden] = useState(false);
  const [clearedPrintsAt, setClearedPrintsAt] = useState(0);
  const [connected, setConnected] = useState(false);
  const [candles, setCandles] = useState<TimeCandle[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticSnapshot | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshSnapshots = useCallback(async () => {
    try {
      const [nextWorkspace, nextCandles, nextTrades, nextDiagnostics, nextMetrics] = await Promise.all([
        getWorkspace(timeframeSec),
        getTimeCandles(timeframeSec),
        getRecentTrades(),
        getDiagnostics(),
        getMarketMetrics(),
      ]);
      setWorkspace(nextWorkspace);
      setCandles(nextCandles.data);
      setTrades(nextTrades);
      setDiagnostics(nextDiagnostics);
      setMetrics(nextMetrics);
      window.__marketDataMetrics = { snapshot: () => nextMetrics };
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backend unavailable");
      setConnected(false);
    }
  }, [timeframeSec]);

  useEffect(() => {
    refreshSnapshots();
    const timer = window.setInterval(async () => {
      try {
        const [nextDiagnostics, nextMetrics, nextWorkspace] = await Promise.all([getDiagnostics(), getMarketMetrics(), getWorkspace(timeframeSec)]);
        setDiagnostics(nextDiagnostics);
        setMetrics(nextMetrics);
        setWorkspace(nextWorkspace);
        window.__marketDataMetrics = { snapshot: () => nextMetrics };
      } catch {
        setConnected(false);
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [refreshSnapshots]);

  useEffect(() => {
    if (!live) return;
    const candleSocket = connectCandleStream(timeframeSec, (candle) => {
      setConnected(true);
      setCandles((current) => upsertCandle(current, candle).slice(-240));
    });
    const tradeSocket = connectTradeStream((trade) => {
      setConnected(true);
      setTrades((current) => [trade, ...current.filter((row) => row.tradeId !== trade.tradeId)].slice(0, 160));
    });
    const markDisconnected = () => setConnected(false);
    candleSocket.onerror = markDisconnected;
    candleSocket.onclose = markDisconnected;
    tradeSocket.onerror = markDisconnected;
    tradeSocket.onclose = markDisconnected;
    return () => {
      candleSocket.close();
      tradeSocket.close();
    };
  }, [live, timeframeSec]);

  const latestTrade = trades[0] ?? diagnostics?.latestTrade ?? null;
  const statusCards = useMemo(
    () => [
      { label: "Trades", value: `${metrics?.trade_messages_normalized ?? 0}`, detail: "normalized" },
      { label: "Candles", value: `${metrics?.candle_updates_published ?? 0}`, detail: "updates" },
      { label: "Depth", value: diagnostics?.depthSynced ? "Synced" : "Waiting", detail: metrics?.depth_status ?? "stopped" },
      { label: "Recorder", value: `${metrics?.recorder_queue_size ?? 0}`, detail: "queued" },
    ],
    [diagnostics, metrics],
  );

  return (
    <main className="workspace">
      <Toolbar
        symbol={diagnostics?.symbol ?? "BTCUSDT"}
        timeframeSec={timeframeSec}
        chartMode={chartMode}
        live={live}
        connected={connected}
        lastPrice={latestTrade?.price ?? null}
        onTimeframeChange={setTimeframeSec}
        onChartModeChange={setChartMode}
        onLiveToggle={() => setLive((value) => !value)}
        onRefresh={refreshSnapshots}
      />
      {error ? <div className="warning">{error}</div> : null}
      <section className="marketGrid">
        <div className="leftStack">
          <MainChart
            candles={workspace?.candles.length ? workspace.candles : candles}
            profile={workspace?.profile ?? []}
            bubbles={workspace?.bubbles ?? []}
            speedTape={workspace?.speedTape ?? []}
            vwap={workspace?.vwap ?? { vwap: null, upperBand: null, lowerBand: null }}
            mode={chartMode}
          />
          {chartMode === "Footprint" ? <FootprintPanel footprints={workspace?.footprints ?? []} /> : null}
        </div>
        <DomPanel
          rows={clearedPrintsAt ? (workspace?.dom ?? []).map((row) => ({ ...row, buyPrint: 0, sellPrint: 0 })) : workspace?.dom ?? []}
          onClear={() => setClearedPrintsAt(Date.now())}
          hidden={domHidden}
          onHideToggle={() => setDomHidden((value) => !value)}
        />
        <TimeAndSales trades={workspace?.trades.length ? workspace.trades.slice(0, 120) : trades} paused={!live} />
      </section>
      <section className="statusStrip">
        {statusCards.map((card) => (
          <div className="statusCell" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.detail}</small>
          </div>
        ))}
      </section>
    </main>
  );
}

function upsertCandle(candles: TimeCandle[], candle: TimeCandle) {
  const index = candles.findIndex((current) => current.timeframeSec === candle.timeframeSec && current.openTime === candle.openTime);
  if (index === -1) return [...candles, candle];
  const next = candles.slice();
  next[index] = candle;
  return next;
}

declare global {
  interface Window {
    __marketDataMetrics?: { snapshot: () => Metrics };
  }
}

"use client";

import { Activity, Database, Radio, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

type Trade = {
  tradeId: string;
  tradeTime: number;
  price: number;
  quantity: number;
  notional: number;
  aggressorSide: "buy" | "sell";
};

type DiagnosticSnapshot = {
  symbol: string;
  liveTradeCount: number;
  latestTrade: Trade | null;
  bestBid: number | null;
  bestAsk: number | null;
  depthSynced: boolean;
  depthLastUpdateId: number | null;
};

type Metrics = {
  trade_ws_messages_received: number;
  trade_messages_normalized: number;
  trade_messages_deduped: number;
  trade_messages_persisted: number;
  depth_ws_messages_received: number;
  depth_updates_applied: number;
  depth_resync_count: number;
  depth_status: string;
  recorder_queue_size: number;
  recorder_flush_latency_ms: number;
};

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

export default function Page() {
  const [diagnostics, setDiagnostics] = useState<DiagnosticSnapshot | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const [diagResponse, metricResponse] = await Promise.all([
        fetch(`${backendUrl}/api/diagnostics`, { cache: "no-store" }),
        fetch(`${backendUrl}/api/metrics/market-data`, { cache: "no-store" }),
      ]);
      if (!diagResponse.ok || !metricResponse.ok) {
        throw new Error("Backend diagnostics request failed");
      }
      setDiagnostics(await diagResponse.json());
      const nextMetrics = await metricResponse.json();
      setMetrics(nextMetrics);
      window.__marketDataMetrics = { snapshot: () => nextMetrics };
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown diagnostics error");
    }
  }

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const latest = diagnostics?.latestTrade;
  const spread =
    diagnostics?.bestBid != null && diagnostics.bestAsk != null
      ? diagnostics.bestAsk - diagnostics.bestBid
      : null;

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <h1>{diagnostics?.symbol ?? "BTCUSDT"}</h1>
          <span>Phase 1 market-data diagnostics</span>
        </div>
        <button onClick={refresh} title="Refresh diagnostics">
          <RefreshCw size={18} />
        </button>
      </section>

      {error ? <div className="warning">{error}</div> : null}

      <section className="grid">
        <StatusPanel
          icon={<Radio size={18} />}
          label="Live Trades"
          value={diagnostics?.liveTradeCount.toLocaleString() ?? "0"}
          detail={`WS ${metrics?.trade_ws_messages_received ?? 0} / persisted ${metrics?.trade_messages_persisted ?? 0}`}
        />
        <StatusPanel
          icon={<Activity size={18} />}
          label="Depth"
          value={diagnostics?.depthSynced ? "Synced" : "Waiting"}
          detail={`Best ${formatPrice(diagnostics?.bestBid)} x ${formatPrice(diagnostics?.bestAsk)} / spread ${formatPrice(spread)}`}
        />
        <StatusPanel
          icon={<Database size={18} />}
          label="Recorder"
          value={`${metrics?.recorder_queue_size ?? 0} queued`}
          detail={`${(metrics?.recorder_flush_latency_ms ?? 0).toFixed(2)} ms flush / ${metrics?.depth_status ?? "stopped"}`}
        />
      </section>

      <section className="panels">
        <div className="panel">
          <h2>Latest Trade</h2>
          {latest ? (
            <dl>
              <dt>ID</dt>
              <dd>{latest.tradeId}</dd>
              <dt>Side</dt>
              <dd className={latest.aggressorSide}>{latest.aggressorSide.toUpperCase()}</dd>
              <dt>Price</dt>
              <dd>{formatPrice(latest.price)}</dd>
              <dt>Quantity</dt>
              <dd>{latest.quantity.toFixed(3)}</dd>
              <dt>Notional</dt>
              <dd>${latest.notional.toLocaleString(undefined, { maximumFractionDigits: 0 })}</dd>
            </dl>
          ) : (
            <p>No live trade received yet.</p>
          )}
        </div>
        <div className="panel">
          <h2>Core Metrics</h2>
          <dl>
            <dt>Normalized</dt>
            <dd>{metrics?.trade_messages_normalized ?? 0}</dd>
            <dt>Dedupe</dt>
            <dd>{metrics?.trade_messages_deduped ?? 0}</dd>
            <dt>Depth updates</dt>
            <dd>{metrics?.depth_updates_applied ?? 0}</dd>
            <dt>Depth resyncs</dt>
            <dd>{metrics?.depth_resync_count ?? 0}</dd>
            <dt>Last update id</dt>
            <dd>{diagnostics?.depthLastUpdateId ?? "-"}</dd>
          </dl>
        </div>
      </section>
    </main>
  );
}

function StatusPanel({
  icon,
  label,
  value,
  detail,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="status">
      <div className="statusHead">
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function formatPrice(value: number | null | undefined) {
  if (value == null) return "-";
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

declare global {
  interface Window {
    __marketDataMetrics?: { snapshot: () => Metrics };
  }
}

import type { CandleSnapshot, DiagnosticSnapshot, Metrics, TimeCandle, Trade } from "./types";

export const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

const websocketBaseUrl = backendUrl.replace(/^http/, "ws");

export async function getDiagnostics(): Promise<DiagnosticSnapshot> {
  return getJson(`${backendUrl}/api/diagnostics`);
}

export async function getMarketMetrics(): Promise<Metrics> {
  return getJson(`${backendUrl}/api/metrics/market-data`);
}

export async function getTimeCandles(timeframeSec: number, limit = 180): Promise<CandleSnapshot> {
  return getJson(`${backendUrl}/api/candles/time?timeframe=${timeframeSec}&limit=${limit}`);
}

export async function getRecentTrades(limit = 150): Promise<Trade[]> {
  return getJson(`${backendUrl}/api/trades/recent?limit=${limit}`);
}

export function connectCandleStream(timeframeSec: number, onMessage: (candle: TimeCandle) => void) {
  return connectJsonStream(`${websocketBaseUrl}/api/ws/candles/time?timeframe=${timeframeSec}`, onMessage);
}

export function connectTradeStream(onMessage: (trade: Trade) => void) {
  return connectJsonStream(`${websocketBaseUrl}/api/ws/trades`, onMessage);
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function connectJsonStream<T>(url: string, onMessage: (message: T) => void) {
  const socket = new WebSocket(url);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data) as T);
  return socket;
}

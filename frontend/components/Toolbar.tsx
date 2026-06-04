import { Pause, Play, Plus, RefreshCw, Wifi, WifiOff } from "lucide-react";

type ToolbarProps = {
  symbol: string;
  timeframeSec: number;
  chartMode: string;
  live: boolean;
  connected: boolean;
  lastPrice: number | null;
  onTimeframeChange: (timeframeSec: number) => void;
  onChartModeChange: (mode: string) => void;
  onLiveToggle: () => void;
  onRefresh: () => void;
};

const intervals = [
  { label: "1m", value: 60 },
  { label: "5m", value: 300 },
  { label: "15m", value: 900 },
  { label: "1h", value: 3600 },
  { label: "2m", value: 120 },
];

const primaryIntervals = [
  { label: "1m", value: 60 },
  { label: "5m", value: 300 },
  { label: "15m", value: 900 },
  { label: "1h", value: 3600 },
];

const chartModes = ["Time", "Tick", "Volume", "Dollar", "Range", "Footprint"];

export function Toolbar({
  symbol,
  timeframeSec,
  chartMode,
  live,
  connected,
  lastPrice,
  onTimeframeChange,
  onChartModeChange,
  onLiveToggle,
  onRefresh,
}: ToolbarProps) {
  return (
    <header className="toolbar">
      <div className="instrument">
        <strong>{symbol} Perp</strong>
      </div>
      <select className="modeSelect compact" value={chartMode} onChange={(event) => onChartModeChange(event.target.value)} aria-label="Chart type">
        {chartModes.map((mode) => (
          <option key={mode} value={mode}>{mode}</option>
        ))}
      </select>
      <select className="modeSelect compact" value="Candles" aria-label="Display type" onChange={() => undefined}>
        <option>Candles</option>
        <option>Heikin Ashi</option>
        <option>Footprint</option>
      </select>
      <div className="segmented" aria-label="Timeframe">
        {primaryIntervals.map((interval) => (
          <button
            className={interval.value === timeframeSec ? "active" : ""}
            key={interval.value}
            onClick={() => onTimeframeChange(interval.value)}
            type="button"
          >
            {interval.label}
          </button>
        ))}
      </div>
      <select className="modeSelect tiny" value={timeframeSec} onChange={(event) => onTimeframeChange(Number(event.target.value))} aria-label="Secondary timeframe">
        {intervals.map((interval) => (
          <option key={interval.value} value={interval.value}>{interval.label}</option>
        ))}
      </select>
      <button className="textButton" type="button"><Plus size={14} />Add</button>
      <button className="textButton" type="button">Style</button>
      <button className="textButton" type="button">Indicators</button>
      <button className="iconButton" onClick={onLiveToggle} title={live ? "Pause live updates" : "Resume live updates"} type="button">
        {live ? <Pause size={17} /> : <Play size={17} />}
      </button>
      <button className="iconButton" onClick={onRefresh} title="Refresh market data" type="button">
        <RefreshCw size={17} />
      </button>
      <div className={connected ? "connection connected" : "connection"}>
        {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
        <span>{connected ? "Live" : "Offline"}</span>
      </div>
      <div className="lastPriceTop">{formatPrice(lastPrice)}</div>
    </header>
  );
}

function formatPrice(value: number | null) {
  if (value == null) return "-";
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

import { Pause, Play, RefreshCw, Wifi, WifiOff } from "lucide-react";

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
        <strong>{symbol}</strong>
        <span>{formatPrice(lastPrice)}</span>
      </div>
      <div className="segmented" aria-label="Timeframe">
        {intervals.map((interval) => (
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
      <select className="modeSelect" value={chartMode} onChange={(event) => onChartModeChange(event.target.value)} aria-label="Chart mode">
        {chartModes.map((mode) => (
          <option key={mode} value={mode}>{mode}</option>
        ))}
      </select>
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
    </header>
  );
}

function formatPrice(value: number | null) {
  if (value == null) return "-";
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

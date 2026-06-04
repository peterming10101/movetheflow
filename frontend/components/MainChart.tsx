import type { MarketOrderBubble, ProfileRow, SpeedTapeBar, TimeCandle, VwapState } from "../lib/types";

type MainChartProps = {
  candles: TimeCandle[];
  profile: ProfileRow[];
  bubbles: MarketOrderBubble[];
  speedTape: SpeedTapeBar[];
  vwap: VwapState;
  mode: string;
};

export function MainChart({ candles, profile, bubbles, speedTape, vwap, mode }: MainChartProps) {
  const visible = candles.slice(-90);
  const bounds = getBounds(visible);
  const width = 1000;
  const height = 500;
  const padTop = 22;
  const padBottom = 42;
  const chartHeight = height - padTop - padBottom;
  const slot = visible.length > 0 ? width / visible.length : width;
  const bodyWidth = Math.max(4, Math.min(12, slot * 0.58));

  return (
    <section className="chartSurface">
      <div className="chartHeader">
        <div className="chartStats">
          <span>O {formatPrice(visible.at(-1)?.open)}</span>
          <span>H {formatPrice(visible.at(-1)?.high)}</span>
          <span>L {formatPrice(visible.at(-1)?.low)}</span>
          <span>C {formatPrice(visible.at(-1)?.close)}</span>
          <span>V {formatVolume(visible.at(-1)?.volume)}</span>
          <span>Trades {visible.at(-1)?.tradeCount ?? 0}</span>
          <span>Delta {formatSigned(visible.at(-1)?.delta ?? 0)}</span>
          <span>VWAP {formatPrice(vwap.vwap ?? undefined)}</span>
        </div>
        <span>{mode}</span>
      </div>
      <div className="indicatorStack">
        <span>Profile</span>
        <span>Market Orders</span>
        <span>Delta Map</span>
      </div>
      <svg className="candles" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Live BTCUSDT candlestick chart">
        <rect x="0" y="0" width={width} height={height} rx="0" className="plotBg" />
        {[0, 1, 2, 3, 4].map((index) => {
          const y = padTop + (chartHeight / 4) * index;
          return <line className="gridLine" key={index} x1="0" x2={width} y1={y} y2={y} />;
        })}
        {visible.map((candle, index) => {
          const x = index * slot + slot / 2;
          const highY = scale(candle.high, bounds.min, bounds.max, padTop, chartHeight);
          const lowY = scale(candle.low, bounds.min, bounds.max, padTop, chartHeight);
          const openY = scale(candle.open, bounds.min, bounds.max, padTop, chartHeight);
          const closeY = scale(candle.close, bounds.min, bounds.max, padTop, chartHeight);
          const up = candle.close >= candle.open;
          const bodyY = Math.min(openY, closeY);
          const bodyHeight = Math.max(2, Math.abs(openY - closeY));
          return (
            <g key={`${candle.timeframeSec}-${candle.openTime}`}>
              <line className={up ? "wick up" : "wick down"} x1={x} x2={x} y1={highY} y2={lowY} />
              <rect
                className={up ? "candleBody up" : "candleBody down"}
                x={x - bodyWidth / 2}
                y={bodyY}
                width={bodyWidth}
                height={bodyHeight}
              />
            </g>
          );
        })}
        {vwap.vwap ? <line className="vwapLine" x1="0" x2={width} y1={scale(vwap.vwap, bounds.min, bounds.max, padTop, chartHeight)} y2={scale(vwap.vwap, bounds.min, bounds.max, padTop, chartHeight)} /> : null}
        {bubbles.map((bubble) => {
          const index = visible.findIndex((candle) => candle.openTime === bubble.candleOpenTime);
          if (index === -1) return null;
          const x = index * slot + slot / 2;
          const y = scale(bubble.price, bounds.min, bounds.max, padTop, chartHeight);
          const radius = Math.max(10, Math.min(38, Math.sqrt(bubble.notional) / 32));
          return (
            <g key={`${bubble.candleOpenTime}-${bubble.side}-${bubble.label}`}>
              <circle className={bubble.side === "buy" ? "bubble buyBubble" : "bubble sellBubble"} cx={x} cy={y} r={radius} />
              <text className="bubbleText" x={x} y={y + 4}>
                {bubble.label}
              </text>
            </g>
          );
        })}
        <ProfileOverlay profile={profile} min={bounds.min} max={bounds.max} padTop={padTop} chartHeight={chartHeight} width={width} />
        <text className="axisLabel" x={width - 92} y={padTop + 14}>
          {formatPrice(bounds.max)}
        </text>
        <text className="axisLabel" x={width - 92} y={height - padBottom}>
          {formatPrice(bounds.min)}
        </text>
        <g className="timeAxis">
          {[0, 0.2, 0.4, 0.6, 0.8, 1].map((pct) => {
            const idx = Math.min(visible.length - 1, Math.max(0, Math.floor((visible.length - 1) * pct)));
            const candle = visible[idx];
            return candle ? <text key={pct} x={pct * width + 8} y={height - 10}>{new Date(candle.openTime).toLocaleDateString([], { day: "2-digit", month: "short" })}</text> : null;
          })}
        </g>
      </svg>
      <SpeedTape bars={speedTape} />
    </section>
  );
}

function ProfileOverlay({
  profile,
  min,
  max,
  padTop,
  chartHeight,
  width,
}: {
  profile: ProfileRow[];
  min: number;
  max: number;
  padTop: number;
  chartHeight: number;
  width: number;
}) {
  const visibleRows = profile.filter((row) => row.price >= min && row.price <= max);
  const maxVolume = Math.max(1, ...visibleRows.map((row) => row.volume));
  return (
    <g>
      {visibleRows.map((row) => {
        const y = scale(row.price, min, max, padTop, chartHeight);
        const barWidth = (row.volume / maxVolume) * 120;
        return (
          <g key={row.price}>
            <rect className={row.delta >= 0 ? "profileBuy" : "profileSell"} x={width - barWidth - 14} y={y - 2} width={barWidth} height={4} />
            {row.isPoc ? <rect className="profilePoc" x={width - barWidth - 14} y={y - 3} width={barWidth} height={6} /> : null}
          </g>
        );
      })}
    </g>
  );
}

function SpeedTape({ bars }: { bars: SpeedTapeBar[] }) {
  const max = Math.max(1, ...bars.map((bar) => Math.abs(bar.value)));
  return (
    <div className="speedTape">
      <div className="indicatorLabel">Speed Tape</div>
      <div className="speedBars">
        {bars.slice(-120).map((bar) => {
          const height = Math.max(2, (Math.abs(bar.value) / max) * 70);
          return <span className={bar.value >= 0 ? "speedBar buySpeed" : "speedBar sellSpeed"} key={bar.time} style={{ height }} />;
        })}
      </div>
    </div>
  );
}

function getBounds(candles: TimeCandle[]) {
  if (!candles.length) return { min: 0, max: 1 };
  const min = Math.min(...candles.map((candle) => candle.low));
  const max = Math.max(...candles.map((candle) => candle.high));
  const padding = Math.max((max - min) * 0.08, 1);
  return { min: min - padding, max: max + padding };
}

function scale(value: number, min: number, max: number, padTop: number, chartHeight: number) {
  return padTop + ((max - value) / (max - min)) * chartHeight;
}

function formatPrice(value: number | undefined) {
  if (value == null) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

function formatVolume(value: number | undefined) {
  if (value == null) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function formatSigned(value: number) {
  return value >= 0 ? value.toFixed(3) : value.toFixed(3);
}

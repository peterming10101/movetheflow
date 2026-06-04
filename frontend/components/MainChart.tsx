import type { TimeCandle } from "../lib/types";

type MainChartProps = {
  candles: TimeCandle[];
};

export function MainChart({ candles }: MainChartProps) {
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
        <div>
          <h2>Main Chart</h2>
          <span>{visible.length ? `${visible.length} live-buffer candles` : "Waiting for live candles"}</span>
        </div>
        <div className="chartStats">
          <span>O {formatPrice(visible.at(-1)?.open)}</span>
          <span>H {formatPrice(visible.at(-1)?.high)}</span>
          <span>L {formatPrice(visible.at(-1)?.low)}</span>
          <span>C {formatPrice(visible.at(-1)?.close)}</span>
        </div>
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
        <text className="axisLabel" x={width - 92} y={padTop + 14}>
          {formatPrice(bounds.max)}
        </text>
        <text className="axisLabel" x={width - 92} y={height - padBottom}>
          {formatPrice(bounds.min)}
        </text>
      </svg>
    </section>
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

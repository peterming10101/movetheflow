import type { FootprintCandle } from "../lib/types";

export function FootprintPanel({ footprints }: { footprints: FootprintCandle[] }) {
  return (
    <section className="footprintPanel">
      <div className="panelTitle">
        <strong>Time Footprint</strong>
        <span>{footprints.length} candles</span>
      </div>
      <div className="footprints">
        {footprints.slice(-10).map((candle) => (
          <div className="footprintCandle" key={candle.openTime}>
            <div className="footprintTime">{new Date(candle.openTime).toLocaleTimeString([], { hour12: false, minute: "2-digit", second: "2-digit" })}</div>
            {candle.levels.slice(0, 12).map((level) => (
              <div className="footprintLevel" key={`${candle.openTime}-${level.price}`}>
                <span className="sell">{level.bidVolume.toFixed(2)}</span>
                <strong>{level.price.toFixed(0)}</strong>
                <span className="buy">{level.askVolume.toFixed(2)}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

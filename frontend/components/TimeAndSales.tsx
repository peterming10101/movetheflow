import type { Trade } from "../lib/types";

type TimeAndSalesProps = {
  trades: Trade[];
  paused: boolean;
};

export function TimeAndSales({ trades, paused }: TimeAndSalesProps) {
  return (
    <aside className="tape">
      <div className="tapeHeader">
        <h2>Time and Sales</h2>
        <div><button type="button">Less</button><button type="button">Hide</button></div>
      </div>
      <div className="tapeControls">
        <span>{trades.length} / 2000</span>
        <label>Theme <input value="Sierra Red" readOnly /></label>
        <label>Font <input value="15" readOnly /></label>
        <label>Min size <input value="0.1" readOnly /></label>
        <button type="button">{paused ? "Paused" : "Auto"}</button>
      </div>
      <div className="tapeRows">
        <div className="tapeRow tapeColumnHead">
          <span>Price</span>
          <span>Qty</span>
        </div>
        {trades.map((trade) => (
          <div className="tapeRow" key={trade.tradeId}>
            <span className={trade.aggressorSide}>{formatPrice(trade.price)}</span>
            <span>{trade.quantity.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

function formatPrice(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

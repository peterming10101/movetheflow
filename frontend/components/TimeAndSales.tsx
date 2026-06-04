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
        <span>{paused ? "Paused" : "Newest first"}</span>
      </div>
      <div className="tapeRows">
        <div className="tapeRow tapeColumnHead">
          <span>Time</span>
          <span>Price</span>
          <span>Qty</span>
        </div>
        {trades.map((trade) => (
          <div className="tapeRow" key={trade.tradeId}>
            <span>{formatTime(trade.tradeTime)}</span>
            <span className={trade.aggressorSide}>{formatPrice(trade.price)}</span>
            <span>{trade.quantity.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

function formatTime(value: number) {
  return new Date(value).toLocaleTimeString([], { hour12: false, minute: "2-digit", second: "2-digit" });
}

function formatPrice(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

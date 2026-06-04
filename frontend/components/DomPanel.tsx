import type { DomRow } from "../lib/types";
import type { CSSProperties } from "react";

type DomPanelProps = {
  rows: DomRow[];
  onClear: () => void;
  hidden: boolean;
  onHideToggle: () => void;
};

export function DomPanel({ rows, onClear, hidden, onHideToggle }: DomPanelProps) {
  const visible = rows.slice(0, 96);
  const maxDepth = Math.max(1, ...visible.map((row) => Math.max(row.bid, row.ask)));
  const maxPrint = Math.max(1, ...visible.map((row) => Math.max(row.buyPrint, row.sellPrint)));
  return (
    <section className={hidden ? "domPanel hiddenPanel" : "domPanel"}>
      <div className="panelTitle">
        <strong>DOM <span>Synced</span></strong>
        <div>
          <button onClick={onClear} type="button">Clear</button>
          <button type="button">Filters</button>
          <button onClick={onHideToggle} type="button">{hidden ? "Show" : "Hide"}</button>
        </div>
      </div>
      {hidden ? null : (
        <>
        <div className="domConfig">
          <div><span>Spread</span><strong>0.1</strong></div>
          <div><span>Bid</span><strong>150.51</strong></div>
          <div><span>Ask</span><strong>1,207.9</strong></div>
          <label>Theme <select><option>Sierra Red / £100</option></select></label>
          <label>Group $ <input value="5" readOnly /></label>
          <div className="columnToggles">
            {["VP", "Bid", "Sell", "Price", "Buy", "Ask"].map((item) => <button key={item} type="button">{item}</button>)}
          </div>
        </div>
        <div className="domRows">
          <div className="domRow domHead">
            <span>VP / DP</span><span>Bid</span><span>Sell</span><span>Price</span><span>Buy</span><span>Ask</span>
          </div>
          {visible.map((row) => (
            <div className="domRow" key={row.price}>
              <span className={row.delta >= 0 ? "domProfile buy" : "domProfile sell"} style={{ "--w": `${Math.min(100, (row.profileVolume / maxDepth) * 100)}%` } as CSSProperties} />
              <span className="bidQty" style={{ "--w": `${(row.bid / maxDepth) * 100}%` } as CSSProperties}>{fmt(row.bid)}</span>
              <span className="sellPrint" style={{ "--w": `${(row.sellPrint / maxPrint) * 100}%` } as CSSProperties}>{fmt(row.sellPrint)}</span>
              <strong>{row.price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
              <span className="buyPrint" style={{ "--w": `${(row.buyPrint / maxPrint) * 100}%` } as CSSProperties}>{fmt(row.buyPrint)}</span>
              <span className="askQty" style={{ "--w": `${(row.ask / maxDepth) * 100}%` } as CSSProperties}>{fmt(row.ask)}</span>
            </div>
          ))}
        </div>
        </>
      )}
    </section>
  );
}

function fmt(value: number) {
  if (value <= 0) return "";
  return value.toFixed(value >= 10 ? 0 : 2);
}

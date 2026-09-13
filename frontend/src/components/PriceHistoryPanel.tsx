import { useEffect, useState } from "react";

import { viewPriceHistory } from "@/api/client";
import type { PriceHistorySummary, Product } from "@/api/client";

interface Props {
  product: Product;
}

type State =
  | { status: "loading" }
  | { status: "done"; summary: PriceHistorySummary }
  | { status: "error" };

// Observed direction only — the backend never projects a future price or
// date, so neither does this copy.
const DROP_COPY = {
  down: "Yes — trending down",
  up: "No — trending up",
  flat: "Unclear — holding flat",
} as const;

const LABEL = { flex: "0 0 110px", fontSize: "12.5px" } as const;
const VALUE = { fontSize: "14px", fontWeight: 600 } as const;

// A section, not a card: CouponPanel renders this under its coupon content
// and only once a result is selected, so there is no idle state here.
export default function PriceHistoryPanel({ product }: Props) {
  const [state, setState] = useState<State>({ status: "loading" });

  const title = product.name;
  const brand = product.brand;
  const store = product.retailer;
  const price = product.price;

  useEffect(() => {
    setState({ status: "loading" });
    // Same out-of-order-response guard as CouponPanel: clicking through
    // several cards quickly can land responses out of order.
    let current = true;
    viewPriceHistory(title, brand, store, price)
      .then((summary) => current && setState({ status: "done", summary }))
      .catch(() => current && setState({ status: "error" }));
    return () => {
      current = false;
    };
  }, [title, brand, store, price]);

  const summary = state.status === "done" ? state.summary : null;

  return (
    <div className="flex flex-col" style={{ gap: "var(--space-2)" }}>
      {state.status === "loading" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Checking price history…
        </p>
      )}

      {state.status === "error" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Couldn't check price history right now.
        </p>
      )}

      {summary && !summary.sufficient && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Not enough history yet for this listing — check back after it's been viewed a few
          more times.
        </p>
      )}

      {summary && summary.sufficient && summary.low != null && (
        <>
          <div className="flex items-baseline gap-3 flex-wrap">
            <span className="text-neutral-700 font-bold" style={LABEL}>
              Lowest recorded
            </span>
            <span style={VALUE}>
              ${summary.low.toFixed(2)}{" "}
              <span className="text-neutral-700" style={{ fontSize: "12.5px", fontWeight: 400 }}>
                {summary.pct_above_low
                  ? `${summary.pct_above_low.toFixed(0)}% above it now`
                  : "at it right now"}
              </span>
            </span>
          </div>
          <div className="flex items-baseline gap-3 flex-wrap">
            <span className="text-neutral-700 font-bold" style={LABEL}>
              Likely to drop
            </span>
            <span style={VALUE}>{DROP_COPY[summary.trend ?? "flat"]}</span>
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { LineChart, TrendingDown, TrendingUp } from "lucide-react";

import { viewPriceHistory } from "@/api/client";
import type { PriceHistorySummary, Product } from "@/api/client";

interface Props {
  product: Product | null;
}

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; summary: PriceHistorySummary }
  | { status: "error" };

const KICKER = {
  fontSize: "11px",
  letterSpacing: "0.08em",
  margin: "0 0 var(--space-2)",
} as const;

const TREND_ICON = { up: TrendingUp, down: TrendingDown } as const;

// Hand-rolled sparkline — no charting library, keeps bundle small (same call
// as the extension's no-bundled-assets decision). Three points only
// (low/current/high): the summary payload carries no per-snapshot series.
function Sparkline({ low, current, high }: { low: number; current: number; high: number }) {
  const span = Math.max(high - low, 0.01);
  const y = (v: number) => 26 - ((v - low) / span) * 22;
  const points = `4,${y(low)} 42,${y(current)} 80,${y(high)}`;
  return (
    <svg
      width="84"
      height="28"
      viewBox="0 0 84 28"
      className="text-accent-700"
      style={{ display: "block", margin: "var(--space-2) 0" }}
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function PriceHistoryPanel({ product }: Props) {
  const [state, setState] = useState<State>({ status: "idle" });

  const title = product?.name ?? "";
  const brand = product?.brand ?? "";
  const store = product?.retailer ?? "";
  const price = product?.price ?? 0;

  useEffect(() => {
    if (!product) {
      setState({ status: "idle" });
      return;
    }
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, brand, store, price]);

  return (
    <div className="bg-neutral-100 border border-divider rounded-lg" style={{ padding: "var(--space-6)" }}>
      <p className="uppercase text-neutral-700 font-bold flex items-center gap-2" style={KICKER}>
        <LineChart size={13} strokeWidth={2.75} />
        Price history
      </p>

      {state.status === "idle" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Pick any result to see how its price has moved.
        </p>
      )}

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

      {state.status === "done" && !state.summary.sufficient && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Not enough history yet for this listing — check back after it's been viewed a few
          more times.
        </p>
      )}

      {state.status === "done" &&
        state.summary.sufficient &&
        state.summary.low != null &&
        state.summary.high != null &&
        state.summary.current != null && (
          <>
            <Sparkline low={state.summary.low} current={state.summary.current} high={state.summary.high} />
            <p style={{ fontSize: "13.5px", fontWeight: 700, lineHeight: 1.35, margin: 0 }}>
              {state.summary.pct_above_low === 0
                ? "At its recorded low"
                : `${state.summary.pct_above_low?.toFixed(0)}% above its recorded low of $${state.summary.low.toFixed(2)}`}
            </p>
            {state.summary.trend && state.summary.trend !== "flat" && (
              <p
                className="flex items-center gap-1 text-neutral-700"
                style={{ fontSize: "12.5px", margin: "var(--space-1) 0 0" }}
              >
                {(() => {
                  const Icon = TREND_ICON[state.summary.trend as "up" | "down"];
                  return <Icon size={13} strokeWidth={2.75} />;
                })()}
                Trending {state.summary.trend} recently
              </p>
            )}
          </>
        )}
    </div>
  );
}

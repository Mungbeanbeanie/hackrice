import { useEffect } from "react";
import { ArrowRight, ExternalLink, X } from "lucide-react";

import type { Product, Verdict } from "@/api/client";

interface Props {
  product: Product;
  targetProduct: Product | null;
  onClose: () => void;
}

interface SpecRow {
  spec: string;
  target: string;
  alternative: string;
  verdict: Verdict | null;
}

const VERDICT_STYLE: Record<Verdict, { label: string; bg: string; color: string }> = {
  same: { label: "Same", bg: "var(--color-accent-2-100)", color: "var(--color-accent-2-700)" },
  better: { label: "Better", bg: "var(--color-accent-2-200)", color: "var(--color-accent-2-800)" },
  close: { label: "Close", bg: "var(--color-surface)", color: "var(--color-neutral-700)" },
  different: { label: "Different", bg: "var(--color-accent-100)", color: "var(--color-accent-800)" },
  lower: { label: "Lower", bg: "var(--color-accent-200)", color: "var(--color-accent-800)" },
};

// Rows follow the reference product's spec order (its column defines what's
// worth showing side by side); a candidate spec the reference doesn't have
// has nothing to compare against and is dropped, not appended.
function buildRows(product: Product, target: Product | null): SpecRow[] {
  if (!target) {
    return product.specs.map((s) => ({ spec: s.key, target: "—", alternative: s.value, verdict: s.verdict }));
  }
  return target.specs.map((t) => {
    const match = product.specs.find((s) => s.key === t.key);
    return { spec: t.key, target: t.value, alternative: match?.value ?? "—", verdict: match?.verdict ?? null };
  });
}

export default function SpecBreakdownModal({ product, targetProduct, onClose }: Props) {
  const rows = buildRows(product, targetProduct);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center animate-soft-in"
      style={{ padding: "clamp(12px, 3vw, 32px)", background: "rgba(46, 43, 37, 0.55)", backdropFilter: "blur(5px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full bg-bg rounded-lg shadow-lg overflow-hidden flex flex-col animate-rise-in"
        style={{ maxWidth: "760px", maxHeight: "88vh" }}
      >
        {/* Header */}
        <div
          className="flex items-start gap-4 border-b border-divider"
          style={{ padding: "clamp(20px, 2.6vw, 28px)" }}
        >
          <div className="flex-1 min-w-0">
            <p
              className="uppercase text-neutral-700 font-bold"
              style={{ fontSize: "11px", letterSpacing: "0.08em", marginBottom: "var(--space-1)" }}
            >
              Spec by spec
            </p>
            <h2 style={{ fontSize: "clamp(21px, 2.4vw, 26px)", lineHeight: 1.2 }}>{product.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 flex-shrink-0 rounded-full bg-surface hover:bg-neutral-300 transition-colors flex items-center justify-center cursor-pointer"
          >
            <X size={16} strokeWidth={2.75} />
          </button>
        </div>

        {/* Price band */}
        <div
          className="grid border-b border-divider"
          style={{
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "var(--space-3)",
            padding: "clamp(16px, 2.2vw, 22px) clamp(20px, 2.6vw, 28px)",
          }}
        >
          {targetProduct && (
            <div className="bg-surface rounded-md" style={{ padding: "var(--space-3)" }}>
              <p
                className="uppercase text-neutral-700 font-bold"
                style={{ fontSize: "11px", letterSpacing: "0.08em", marginBottom: "var(--space-1)" }}
              >
                Original
              </p>
              <p style={{ fontFamily: "var(--font-heading)", fontSize: "26px", lineHeight: 1 }}>
                ${targetProduct.price.toFixed(2)}
              </p>
            </div>
          )}
          <div className="bg-accent-2-100 border border-accent-2-300 rounded-md" style={{ padding: "var(--space-3)" }}>
            <p
              className="uppercase text-accent-2-700 font-bold"
              style={{ fontSize: "11px", letterSpacing: "0.08em", marginBottom: "var(--space-1)" }}
            >
              This one
            </p>
            <p className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "26px", lineHeight: 1 }}>
              ${product.price.toFixed(2)}
            </p>
          </div>
          {product.savings != null && product.savings > 0 && (
            <div className="bg-accent-2-100 border border-accent-2-300 rounded-md" style={{ padding: "var(--space-3)" }}>
              <p
                className="uppercase text-accent-2-700 font-bold"
                style={{ fontSize: "11px", letterSpacing: "0.08em", marginBottom: "var(--space-1)" }}
              >
                You keep
              </p>
              <p className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "26px", lineHeight: 1 }}>
                ${product.savings.toFixed(2)}
              </p>
              {product.savingsPercent != null && (
                <p className="text-accent-2-700" style={{ fontSize: "12px", marginTop: "var(--space-1)" }}>
                  {Math.round(product.savingsPercent)}% less
                </p>
              )}
            </div>
          )}
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1" style={{ padding: "clamp(16px, 2.2vw, 24px) clamp(20px, 2.6vw, 28px)" }}>
          {product.rationale && (
            <p className="text-neutral-800" style={{ fontSize: "14px", lineHeight: 1.55, marginBottom: "var(--space-4)" }}>
              {product.rationale}
            </p>
          )}
          {/* Retailer listings publish physical specs unevenly, and plenty of
              pairs share none at all. Saying so beats a body that just stops. */}
          {rows.length === 0 ? (
            <p
              className="text-neutral-700 border-t border-divider"
              style={{ fontSize: "13.5px", paddingTop: "var(--space-3)" }}
            >
              Neither listing publishes specs we can line up side by side.
            </p>
          ) : (
            <div className="flex flex-col">
              {rows.map((row) => {
                const v = row.verdict && VERDICT_STYLE[row.verdict];
                return (
                  <div
                    key={row.spec}
                    className="flex items-center gap-3 flex-wrap border-t border-divider"
                    style={{ padding: "var(--space-3) 0" }}
                  >
                    <span className="text-neutral-700 font-bold" style={{ flex: "0 0 118px", fontSize: "12.5px" }}>
                      {row.spec}
                    </span>
                    <span className="text-neutral-700" style={{ flex: "1 1 120px", fontSize: "14px" }}>
                      {row.target}
                    </span>
                    <ArrowRight size={15} strokeWidth={2.75} color="var(--color-neutral-400)" className="flex-shrink-0" />
                    <span style={{ flex: "1 1 120px", fontSize: "14px", fontWeight: 600 }}>{row.alternative}</span>
                    {v && (
                      <span
                        className="flex-shrink-0 font-bold rounded-full"
                        style={{ fontSize: "11.5px", padding: "3px var(--space-2)", background: v.bg, color: v.color }}
                      >
                        {v.label}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="border-t border-divider flex items-center gap-3 flex-wrap"
          style={{ padding: "clamp(16px, 2.2vw, 22px) clamp(20px, 2.6vw, 28px)" }}
        >
          <span className="text-neutral-700 mr-auto" style={{ fontSize: "13px" }}>
            {Math.round(product.matchScore)}% spec match · {product.rating.toFixed(1)}★ from{" "}
            {product.reviewCount.toLocaleString()} reviews
          </span>
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors"
            style={{ padding: "var(--space-3) var(--space-6)", fontSize: "14.5px" }}
          >
            Buy this instead
            <ExternalLink size={15} strokeWidth={2.75} />
          </a>
        </div>
      </div>
    </div>
  );
}

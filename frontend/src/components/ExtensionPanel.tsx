import { X } from "lucide-react";

import type { Product } from "@/api/client";
import HoneyDrop from "@/components/HoneyDrop";

interface Props {
  targetProduct: Product | null;
  // Flattened, already ranked (group order, then value within group).
  products: Product[];
  onClose: () => void;
  onOpenComparison: () => void;
}

const STRIPE = "repeating-linear-gradient(45deg, var(--color-neutral-200) 0 4px, var(--color-neutral-100) 4px 8px)";

export default function ExtensionPanel({ targetProduct, products, onClose, onOpenComparison }: Props) {
  const best = products[0] ?? null;
  const savings = best && targetProduct ? targetProduct.price - best.price : null;

  return (
    <div
      className="bg-neutral-100 border border-divider rounded-lg shadow-lg animate-rise-in"
      style={{ width: "100%", maxWidth: "386px", padding: "var(--space-4)" }}
    >
      <div className="flex items-center" style={{ gap: "var(--space-2)", marginBottom: "var(--space-4)" }}>
        <div className="animate-bob flex-shrink-0" style={{ width: 22, height: 26 }}>
          <HoneyDrop size={22} />
        </div>
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "17px", color: "var(--color-accent-700)" }} className="mr-auto">
          nectarly
        </span>
        <button
          onClick={onClose}
          className="rounded-full bg-transparent hover:bg-surface transition-colors flex items-center justify-center text-neutral-600 cursor-pointer"
          style={{ width: 28, height: 28, border: "none" }}
        >
          <X size={15} strokeWidth={2.75} />
        </button>
      </div>

      {best && (
        <div className="bg-accent-2-100 border border-accent-2-300 rounded-md" style={{ padding: "var(--space-4)" }}>
          <p
            className="uppercase text-accent-2-700 font-bold"
            style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-1)" }}
          >
            You could keep
          </p>
          <p className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "40px", lineHeight: 1, margin: 0 }}>
            ${savings != null ? savings.toFixed(0) : best.price.toFixed(0)}
          </p>
          <p className="text-accent-2-700" style={{ fontSize: "13px", margin: "var(--space-1) 0 0" }}>
            on a {Math.round(best.matchScore)}% spec match, rated {best.rating.toFixed(1)} across{" "}
            {best.reviewCount.toLocaleString()} reviews
          </p>
        </div>
      )}

      <p
        className="uppercase text-neutral-700 font-bold"
        style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "var(--space-4) 0 var(--space-2)" }}
      >
        Equivalents found
      </p>
      <div className="flex flex-col" style={{ gap: "var(--space-2)" }}>
        {products.slice(0, 4).map((p) => (
          <div
            key={p.id}
            className="flex items-center border border-divider rounded-md"
            style={{ gap: "var(--space-3)", padding: "var(--space-3)" }}
          >
            <div
              className="rounded-sm flex-shrink-0 border border-divider overflow-hidden"
              style={{ width: 36, height: 36, background: STRIPE }}
            >
              {p.image && <img src={p.image} alt={p.short} className="w-full h-full object-contain" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="overflow-hidden text-ellipsis whitespace-nowrap" style={{ fontSize: "13px", fontWeight: 700, lineHeight: 1.3, margin: 0 }}>
                {p.short}
              </p>
              <p className="text-neutral-700" style={{ fontSize: "11.5px", margin: "2px 0 0" }}>
                {Math.round(p.matchScore)}% match · {p.rating.toFixed(1)}★
              </p>
            </div>
            <p style={{ fontFamily: "var(--font-heading)", fontSize: "17px", lineHeight: 1, flexShrink: 0, margin: 0 }}>
              ${p.price.toFixed(0)}
            </p>
          </div>
        ))}
      </div>

      <button
        onClick={onOpenComparison}
        className="w-full rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors cursor-pointer"
        style={{ marginTop: "var(--space-4)", padding: "var(--space-3)", fontSize: "14.5px" }}
      >
        Open full comparison
      </button>
    </div>
  );
}

import { useEffect } from "react";

import type { Product } from "@/api/client";

interface SpecRow {
  spec: string;
  target: string;
  alternative: string;
}

interface Props {
  product: Product;
  targetProduct: Product | null;
  onClose: () => void;
}

// No per-row winner: which side "wins" is only defined for specs whose direction
// is known, and the extracted set mixes higher-is-better (rating) with
// lower-is-better (price) and neither (size). The previous version kept the
// field but scored every row a tie, so two of its three colours were
// unreachable. The table shows both values and lets the reader judge.
function buildSpecComparison(product: Product, target: Product | null): SpecRow[] {
  if (!target) {
    return product.specs.map((s) => ({
      spec: s.key,
      target: "—",
      alternative: s.value,
    }));
  }
  const allKeys = Array.from(
    new Set([...target.specs.map((s) => s.key), ...product.specs.map((s) => s.key)])
  );
  return allKeys.map((key) => ({
    spec: key,
    target: target.specs.find((s) => s.key === key)?.value ?? "—",
    alternative: product.specs.find((s) => s.key === key)?.value ?? "—",
  }));
}

export default function SpecBreakdownModal({ product, targetProduct, onClose }: Props) {
  const rows = buildSpecComparison(product, targetProduct);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ background: "rgba(61, 32, 0, 0.45)", backdropFilter: "blur(6px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="glass-card honey-shadow-lg rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-fade-in-up"
        style={{ animationDelay: "0.05s" }}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b" style={{ borderColor: "rgba(245,166,35,0.2)" }}>
          <div>
            <h2 className="text-lg font-bold" style={{ color: "#3d2000" }}>
              Spec Breakdown
            </h2>
            <p className="text-sm mt-0.5" style={{ color: "#7c4a00" }}>
              {product.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-xl transition-colors hover:bg-amber-100 text-lg leading-none cursor-pointer"
            style={{ color: "#7c4a00" }}
          >
            ×
          </button>
        </div>

        {/* Price comparison */}
        <div className="flex gap-4 px-6 py-4" style={{ borderBottom: "1px solid rgba(245,166,35,0.2)" }}>
          {targetProduct && (
            <div className="flex-1 rounded-2xl p-3 text-center" style={{ background: "rgba(245,166,35,0.1)" }}>
              <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: "#b45309" }}>
                Original
              </p>
              <p className="text-2xl font-extrabold" style={{ color: "#e87d00" }}>
                ${targetProduct.price.toFixed(2)}
              </p>
              <p className="text-xs mt-0.5 truncate" style={{ color: "#7c4a00" }}>
                {targetProduct.name}
              </p>
            </div>
          )}
          <div className="flex-1 rounded-2xl p-3 text-center" style={{ background: "rgba(34,197,94,0.08)" }}>
            <p className="text-xs font-semibold uppercase tracking-wide mb-1 text-green-700">
              Alternative
            </p>
            <p className="text-2xl font-extrabold text-green-600">
              ${product.price.toFixed(2)}
            </p>
            <p className="text-xs mt-0.5 truncate" style={{ color: "#7c4a00" }}>
              {product.name}
            </p>
          </div>
          {targetProduct && product.savings != null && product.savings > 0 && (
            <div className="flex-1 rounded-2xl p-3 text-center" style={{ background: "rgba(34,197,94,0.06)" }}>
              <p className="text-xs font-semibold uppercase tracking-wide mb-1 text-green-700">
                You Save
              </p>
              <p className="text-2xl font-extrabold text-green-600">
                ${product.savings.toFixed(2)}
              </p>
              <p className="text-xs mt-0.5" style={{ color: "#7c4a00" }}>
                {(product.savingsPercent ?? 0).toFixed(0)}% less
              </p>
            </div>
          )}
        </div>

        {/* Spec table */}
        <div className="overflow-y-auto flex-1 p-6">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th
                  className="text-left pb-3 font-semibold text-xs uppercase tracking-wide"
                  style={{ color: "#b45309", width: "30%" }}
                >
                  Specification
                </th>
                {targetProduct && (
                  <th
                    className="text-center pb-3 font-semibold text-xs uppercase tracking-wide"
                    style={{ color: "#b45309", width: "35%" }}
                  >
                    Original
                  </th>
                )}
                <th
                  className="text-center pb-3 font-semibold text-xs uppercase tracking-wide"
                  style={{ color: "#b45309" }}
                >
                  Alternative
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr
                  key={row.spec}
                  className="border-t"
                  style={{
                    borderColor: "rgba(245,166,35,0.12)",
                    animationDelay: `${0.06 + i * 0.03}s`,
                  }}
                >
                  <td className="py-2.5 pr-3 font-mono text-xs font-medium" style={{ color: "#7c4a00" }}>
                    {row.spec}
                  </td>
                  {targetProduct && (
                    <td className="py-2.5 px-3 text-center rounded-l" style={{ color: "#3d2000" }}>
                      {row.target}
                    </td>
                  )}
                  <td
                    className="py-2.5 px-3 text-center rounded font-medium"
                    style={{ color: "#3d2000" }}
                  >
                    {row.alternative}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-between items-center" style={{ borderColor: "rgba(245,166,35,0.2)" }}>
          <span className="text-xs" style={{ color: "#a16207" }}>
            Match score: {product.matchScore}%
          </span>
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2 rounded-2xl text-sm font-semibold text-white transition-opacity hover:opacity-90"
            style={{ background: "linear-gradient(135deg, #f5a623, #e87d00)" }}
          >
            View Deal
          </a>
        </div>
      </div>
    </div>
  );
}

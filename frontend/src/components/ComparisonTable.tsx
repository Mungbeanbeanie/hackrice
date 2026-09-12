import type { Product } from "@/api/client";

interface Props {
  target: Product | null;
  products: Product[];
}

interface Column {
  short: string;
  priceLabel: string;
  savingsLabel: string;
}

function ratingLabel(p: Product): string {
  return `${p.rating.toFixed(1)} (${p.reviewCount.toLocaleString()})`;
}

export default function ComparisonTable({ target, products }: Props) {
  const columns: Column[] = [
    ...(target
      ? [{ short: target.short, priceLabel: `$${target.price.toFixed(2)}`, savingsLabel: "the original" }]
      : []),
    ...products.map((p) => ({
      short: p.short,
      priceLabel: `$${p.price.toFixed(2)}`,
      savingsLabel: p.savings != null ? `−$${p.savings.toFixed(2)}` : "—",
    })),
  ];

  const specKeys = Array.from(
    new Set([...(target?.specs.map((s) => s.key) ?? []), ...products.flatMap((p) => p.specs.map((s) => s.key))])
  );

  const rowsForProducts = (getValue: (p: Product) => string) => [
    ...(target ? [getValue(target)] : []),
    ...products.map(getValue),
  ];

  const specRows = specKeys.map((key) => ({
    spec: key,
    cells: rowsForProducts((p) => p.specs.find((s) => s.key === key)?.value ?? "—"),
  }));

  const summaryRows = [
    {
      spec: "Spec match",
      cells: [...(target ? ["reference"] : []), ...products.map((p) => `${Math.round(p.matchScore)}%`)],
    },
    {
      spec: "Rating",
      cells: rowsForProducts(ratingLabel),
    },
  ];

  return (
    <div className="bg-neutral-100 border border-divider rounded-lg overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse" style={{ fontSize: "13.5px", minWidth: "660px" }}>
          <thead>
            <tr className="bg-surface">
              <th
                className="text-left uppercase text-neutral-700 font-bold"
                style={{ padding: "var(--space-3) var(--space-4)", fontSize: "11px", letterSpacing: "0.08em", width: "150px" }}
              >
                Spec
              </th>
              {columns.map((col, i) => (
                <th
                  key={i}
                  className="text-left align-top border-l border-divider"
                  style={{ padding: "var(--space-3) var(--space-4)" }}
                >
                  <p style={{ fontSize: "13px", fontWeight: 700, lineHeight: 1.3 }}>{col.short}</p>
                  <p style={{ fontFamily: "var(--font-heading)", fontSize: "20px", lineHeight: 1, marginTop: "var(--space-1)" }}>
                    {col.priceLabel}
                  </p>
                  <p className="text-accent-2-700 font-bold" style={{ fontSize: "12px", marginTop: "var(--space-1)" }}>
                    {col.savingsLabel}
                  </p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...specRows, ...summaryRows].map((row) => (
              <tr key={row.spec} className="border-t border-divider">
                <td
                  className="text-neutral-700 font-bold"
                  style={{ padding: "var(--space-3) var(--space-4)", fontSize: "12.5px" }}
                >
                  {row.spec}
                </td>
                {row.cells.map((value, i) => (
                  <td key={i} className="border-l border-divider" style={{ padding: "var(--space-3) var(--space-4)" }}>
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import type { Product } from "@/api/client";

interface Props {
  tiers: {
    tier1: Product[];
    tier2: Product[];
    tier3: Product[];
  };
  onCompare: (product: Product) => void;
}

const TIER_CONFIG = {
  1: {
    label: "Best Value",
    description: "Highest quality match at the lowest price",
    glowClass: "tier-1-glow",
    badgeStyle: { background: "linear-gradient(135deg, #eab308, #f59e0b)", color: "#fff" },
    headerStyle: { color: "#92400e" },
    accentStyle: { color: "#e87d00" },
    dotStyle: { background: "#f5a623" },
  },
  2: {
    label: "Great Alternative",
    description: "Excellent quality with more savings",
    glowClass: "tier-2-glow",
    badgeStyle: { background: "rgba(156,163,175,0.2)", color: "#6b7280" },
    headerStyle: { color: "#374151" },
    accentStyle: { color: "#6b7280" },
    dotStyle: { background: "#9ca3af" },
  },
  3: {
    label: "Budget Pick",
    description: "Maximum savings, solid performance",
    glowClass: "tier-3-glow",
    badgeStyle: { background: "rgba(245,166,35,0.15)", color: "#92400e" },
    headerStyle: { color: "#78350f" },
    accentStyle: { color: "#b45309" },
    dotStyle: { background: "#d97706" },
  },
} as const;

function Stars({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <svg key={i} width="10" height="10" viewBox="0 0 12 12" fill="none">
          <path
            d="M6 1l1.2 3.6H11L8.1 6.9l1.2 3.6L6 8.4l-3.3 2.1 1.2-3.6L1 4.6h3.8z"
            fill={i <= Math.round(rating) ? "#f5a623" : "#e5d6b0"}
          />
        </svg>
      ))}
    </span>
  );
}

function ProductCard({
  product,
  tier,
  index,
  onCompare,
}: {
  product: Product;
  tier: 1 | 2 | 3;
  index: number;
  onCompare: (p: Product) => void;
}) {
  const cfg = TIER_CONFIG[tier];
  return (
    <div
      className={`glass-card ${cfg.glowClass} rounded-2xl p-4 animate-fade-in-up transition-transform duration-200 hover:-translate-y-0.5`}
      style={{ animationDelay: `${0.08 + index * 0.07}s` }}
    >
      <div className="flex gap-3">
        <div
          className="w-16 h-16 rounded-xl flex-shrink-0 overflow-hidden"
          style={{ background: "#fff8e1" }}
        >
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain p-1.5"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              {product.badge && (
                <span
                  className="inline-block text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full mb-1"
                  style={cfg.badgeStyle}
                >
                  {product.badge}
                </span>
              )}
              <h3
                className="text-sm font-bold leading-snug line-clamp-2"
                style={{ color: "#3d2000" }}
              >
                {product.name}
              </h3>
              {/* The payload carries a merchant, not a maker, so brand is
                  usually empty — joining unconditionally left a stray "·". */}
              <p className="text-xs mt-0.5" style={{ color: "#7c4a00" }}>
                {[product.brand, product.retailer].filter(Boolean).join(" · ")}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xl font-extrabold" style={cfg.accentStyle}>
                ${product.price.toFixed(2)}
              </p>
              {product.originalPrice != null && product.originalPrice > product.price && (
                <p className="text-xs line-through" style={{ color: "#a16207" }}>
                  ${product.originalPrice.toFixed(2)}
                </p>
              )}
              {/* Guarded on > 0: a candidate pricier than the target used to
                  render as "Save $-34". */}
              {product.savings != null && product.savings > 0 && (
                <p className="text-xs font-semibold text-green-600">
                  Save ${product.savings.toFixed(0)}
                  {product.savingsPercent != null && ` (${product.savingsPercent.toFixed(0)}%)`}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1.5">
              <Stars rating={product.rating} />
              <span className="text-xs" style={{ color: "#a16207" }}>
                {product.rating.toFixed(1)} ({product.reviewCount.toLocaleString()})
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => onCompare(product)}
                className="text-xs px-2.5 py-1 rounded-xl font-medium border transition-all duration-150 hover:opacity-80 cursor-pointer"
                style={{ borderColor: "rgba(245,166,35,0.4)", color: "#b45309" }}
              >
                Compare
              </button>
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs px-3 py-1 rounded-xl font-semibold text-white transition-all duration-150 hover:opacity-90"
                style={{ background: "linear-gradient(135deg, #f5a623, #e87d00)" }}
              >
                View
              </a>
            </div>
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {product.specs.slice(0, 3).map((s) => (
              <span
                key={s.key}
                className="text-[10px] px-2 py-0.5 rounded-lg font-mono"
                style={{ background: "rgba(245,166,35,0.12)", color: "#7c4a00" }}
              >
                {s.key}: {s.value}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TierSection({
  tier,
  products,
  onCompare,
}: {
  tier: 1 | 2 | 3;
  products: Product[];
  onCompare: (p: Product) => void;
}) {
  if (!products.length) return null;
  const cfg = TIER_CONFIG[tier];
  return (
    <section className="animate-fade-in-up" style={{ animationDelay: `${0.04 * tier}s` }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full flex-shrink-0" style={cfg.dotStyle} />
        <h2 className="text-base font-bold" style={cfg.headerStyle}>
          Tier {tier} — {cfg.label}
        </h2>
        <span className="text-xs" style={{ color: "#a16207" }}>
          {cfg.description}
        </span>
      </div>
      <div className="flex flex-col gap-3">
        {products.map((p, i) => (
          <ProductCard key={p.id} product={p} tier={tier} index={i} onCompare={onCompare} />
        ))}
      </div>
    </section>
  );
}

export default function AlternativeTierList({ tiers, onCompare }: Props) {
  return (
    <div className="flex flex-col gap-8">
      <TierSection tier={1} products={tiers.tier1} onCompare={onCompare} />
      <TierSection tier={2} products={tiers.tier2} onCompare={onCompare} />
      <TierSection tier={3} products={tiers.tier3} onCompare={onCompare} />
    </div>
  );
}

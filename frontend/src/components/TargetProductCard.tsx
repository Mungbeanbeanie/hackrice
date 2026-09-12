import type { Product } from "@/api/client";

interface Props {
  product: Product;
}

function Stars({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <svg key={i} width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path
            d="M6 1l1.2 3.6H11L8.1 6.9l1.2 3.6L6 8.4l-3.3 2.1 1.2-3.6L1 4.6h3.8z"
            fill={i <= Math.round(rating) ? "#f5a623" : "#e5d6b0"}
          />
        </svg>
      ))}
    </span>
  );
}

export default function TargetProductCard({ product }: Props) {
  return (
    <div
      className="glass-card honey-shadow rounded-3xl p-5 animate-fade-in-up"
      style={{ animationDelay: "0.05s" }}
    >
      <div className="flex items-start gap-4">
        <div
          className="w-20 h-20 rounded-2xl flex-shrink-0 overflow-hidden"
          style={{ background: "#fff8e1" }}
        >
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain p-2"
          />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: "#b45309" }}>
            You searched for
          </p>
          <h2 className="text-lg font-bold leading-snug mb-1 truncate" style={{ color: "#3d2000" }}>
            {product.name}
          </h2>
          <p className="text-sm mb-2" style={{ color: "#7c4a00" }}>
            {[product.brand, product.retailer].filter(Boolean).join(" · ")}
          </p>
          <div className="flex items-center gap-3">
            <Stars rating={product.rating} />
            <span className="text-xs" style={{ color: "#a16207" }}>
              ({product.reviewCount.toLocaleString()} reviews)
            </span>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-2xl font-extrabold" style={{ color: "#e87d00" }}>
            ${product.price.toFixed(2)}
          </p>
          {product.originalPrice && (
            <p className="text-sm line-through" style={{ color: "#a16207" }}>
              ${product.originalPrice.toFixed(2)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

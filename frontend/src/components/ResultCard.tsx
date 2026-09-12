import { useState } from "react";
import { ExternalLink, Ticket } from "lucide-react";

import type { Product } from "@/api/client";

interface Props {
  product: Product;
  baselinePrice: number | null;
  baselineLabel: string;
  selected: boolean;
  onCompare: (product: Product) => void;
  onSelect: (product: Product) => void;
}

const STRIPE = "repeating-linear-gradient(45deg, var(--color-neutral-200) 0 5px, var(--color-neutral-100) 5px 10px)";

export default function ResultCard({
  product,
  baselinePrice,
  baselineLabel,
  selected,
  onCompare,
  onSelect,
}: Props) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImg = product.image && !imgFailed;
  const sharePct = baselinePrice ? Math.round((product.price / baselinePrice) * 100) : null;

  return (
    <div
      onClick={() => onSelect(product)}
      className={`bg-neutral-100 border rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-[box-shadow,transform] duration-[180ms] cursor-pointer ${selected ? "border-accent ring-2 ring-accent" : "border-divider"}`}
      style={{ padding: "clamp(14px, 1.8vw, 20px)" }}
    >
      <div className="flex gap-3 items-start">
        <div
          className="w-[68px] h-[68px] rounded-md flex-shrink-0 border border-divider overflow-hidden"
          // Listing thumbnails are overwhelmingly transparent PNGs, so the
          // stripes designed as the missing-image fallback were showing through
          // every product photo.
          style={{ background: showImg ? "#fff" : STRIPE }}
        >
          {showImg && (
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-full object-contain"
              onError={() => setImgFailed(true)}
            />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex gap-3 items-start flex-wrap">
            <div className="flex-1 min-w-[190px]">
              <h4 style={{ fontSize: "15.5px", fontWeight: 700, lineHeight: 1.3 }}>{product.name}</h4>
              <p className="text-neutral-700" style={{ fontSize: "13px", marginTop: "var(--space-1)" }}>
                {[product.brand, product.retailer].filter(Boolean).join(" · ")}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <p style={{ fontFamily: "var(--font-heading)", fontSize: "25px", lineHeight: 1 }}>
                ${product.price.toFixed(2)}
              </p>
              {product.savings != null && product.savings > 0 && (
                <p
                  className="text-accent-2-700 font-bold"
                  style={{ fontSize: "13px", marginTop: "var(--space-1)" }}
                >
                  saves ${product.savings.toFixed(2)}
                </p>
              )}
            </div>
          </div>

          {sharePct != null && (
            <div className="flex items-center gap-2 mt-3">
              <div className="flex-1 h-[9px] rounded-full bg-accent-2-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.min(sharePct, 100)}%` }}
                />
              </div>
              <span className="text-neutral-700 font-bold flex-shrink-0" style={{ fontSize: "12px" }}>
                {sharePct}% of {baselineLabel}
              </span>
            </div>
          )}

          <div className="flex items-center gap-2 flex-wrap mt-3">
            <span
              className="inline-flex items-baseline gap-1 rounded-full bg-accent-100 border border-accent-200"
              style={{ padding: "var(--space-1) var(--space-3)" }}
            >
              <span className="text-accent-800 font-bold" style={{ fontSize: "13px" }}>
                {Math.round(product.matchScore)}%
              </span>
              <span className="text-accent-700" style={{ fontSize: "11.5px" }}>
                match
              </span>
            </span>
            <span
              className="inline-flex items-baseline gap-1 rounded-full bg-surface"
              style={{ padding: "var(--space-1) var(--space-3)" }}
            >
              <span className="font-bold" style={{ fontSize: "13px" }}>
                {product.rating.toFixed(1)}
              </span>
              <span className="text-neutral-700" style={{ fontSize: "11.5px" }}>
                {product.reviewCount.toLocaleString()} reviews
              </span>
            </span>
            <span
              className={`inline-flex items-center gap-1 ${selected ? "text-accent-700 font-bold" : "text-neutral-700"}`}
              style={{ fontSize: "12px" }}
            >
              <Ticket size={12} strokeWidth={2.75} />
              {selected ? "Showing coupons →" : "Click to view coupons"}
            </span>
            {/* Both stop propagation: the whole card is a click target now, and
                without this, Buy would also swap the coupon panel underneath. */}
            <div className="ml-auto flex gap-1 flex-shrink-0">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCompare(product);
                }}
                className="rounded-full border border-divider bg-transparent font-heading hover:bg-neutral-200 transition-colors cursor-pointer"
                style={{ padding: "var(--space-2) var(--space-3)", fontSize: "13.5px" }}
              >
                Compare
              </button>
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1 rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors"
                style={{ padding: "var(--space-2) var(--space-3)", fontSize: "13.5px" }}
              >
                Buy
                <ExternalLink size={13} strokeWidth={2.75} />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

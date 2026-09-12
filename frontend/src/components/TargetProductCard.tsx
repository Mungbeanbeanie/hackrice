import { useState } from "react";

import type { Product } from "@/api/client";

interface Props {
  product: Product;
}

const STRIPE = "repeating-linear-gradient(45deg, var(--color-neutral-200) 0 5px, var(--color-neutral-100) 5px 10px)";

export default function TargetProductCard({ product }: Props) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImg = product.image && !imgFailed;

  return (
    <div
      className="bg-neutral-100 border border-divider rounded-lg flex items-center gap-4 flex-wrap animate-rise-in"
      style={{ padding: "clamp(16px, 2vw, 22px)" }}
    >
      <div
        className="w-[62px] h-[62px] rounded-md flex-shrink-0 border border-divider overflow-hidden"
        style={{ background: STRIPE }}
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
      <div className="flex-1 min-w-[200px]">
        <p
          className="uppercase text-neutral-700 font-bold"
          style={{ fontSize: "11px", letterSpacing: "0.08em", marginBottom: "var(--space-1)" }}
        >
          Your reference product
        </p>
        <h2 style={{ fontSize: "20px", lineHeight: 1.2 }}>{product.name}</h2>
        <p className="text-neutral-700" style={{ fontSize: "13.5px", marginTop: "var(--space-1)" }}>
          {[product.brand, product.retailer].filter(Boolean).join(" · ")}
          {" · "}
          {product.rating.toFixed(1)}★ ({product.reviewCount.toLocaleString()})
        </p>
      </div>
      <div className="text-right flex-shrink-0">
        <p style={{ fontFamily: "var(--font-heading)", fontSize: "28px", lineHeight: 1 }}>
          ${product.price.toFixed(2)}
        </p>
        {product.originalPrice != null && (
          <p
            className="text-neutral-700 line-through"
            style={{ fontSize: "13px", marginTop: "var(--space-1)" }}
          >
            ${product.originalPrice.toFixed(2)}
          </p>
        )}
      </div>
    </div>
  );
}

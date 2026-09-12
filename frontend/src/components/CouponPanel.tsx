import { useEffect, useState } from "react";
import { Check, Copy, Ticket } from "lucide-react";

import { fetchCoupon } from "@/api/client";
import type { CouponOffer, Product } from "@/api/client";

interface Props {
  product: Product | null;
}

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; offer: CouponOffer | null }
  | { status: "error" };

// The feed gives us prose ("Save 35% off with Autoship") and no numeric
// discount field, so the only way to put a dollar figure next to an offer is to
// read one out of the sentence.
//
// ponytail: text heuristic, deliberately conservative — it shows a figure only
// when the description states one plainly, and says nothing otherwise. A
// numeric discount column on the feed is the upgrade path.
function estimateSaving(description: string, price: number): string | null {
  const percent = description.match(/(\d{1,2})\s*%/);
  if (percent) {
    const off = (price * Number(percent[1])) / 100;
    return `about $${off.toFixed(2)} off this item`;
  }
  const flat = description.match(/\$\s*(\d+(?:\.\d{2})?)/);
  if (flat && Number(flat[1]) < price) {
    return `$${Number(flat[1]).toFixed(2)} off this item`;
  }
  return null;
}

const KICKER = {
  fontSize: "11px",
  letterSpacing: "0.08em",
  margin: "0 0 var(--space-2)",
} as const;

export default function CouponPanel({ product }: Props) {
  const [state, setState] = useState<State>({ status: "idle" });
  const [copied, setCopied] = useState(false);

  const retailer = product?.retailer ?? "";

  useEffect(() => {
    if (!retailer) {
      setState({ status: "idle" });
      return;
    }
    setState({ status: "loading" });
    setCopied(false);
    // Clicking through several cards quickly can land responses out of order;
    // only the newest effect is allowed to write state.
    let current = true;
    fetchCoupon(retailer)
      .then((offer) => current && setState({ status: "done", offer }))
      .catch(() => current && setState({ status: "error" }));
    return () => {
      current = false;
    };
  }, [retailer]);

  async function copyCode(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
    } catch {
      // Clipboard access is denied outside a secure context. The code is on
      // screen either way, so this is a lost convenience, not a lost feature.
    }
  }

  const offer = state.status === "done" ? state.offer : null;
  const saving =
    offer && product ? estimateSaving(offer.discount_description, product.price) : null;

  return (
    <div
      className="bg-neutral-100 border border-divider rounded-lg"
      style={{ padding: "var(--space-6)" }}
    >
      <p className="uppercase text-neutral-700 font-bold flex items-center gap-2" style={KICKER}>
        <Ticket size={13} strokeWidth={2.75} />
        Coupons
      </p>

      {state.status === "idle" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Pick any result to check for an active code at that retailer.
        </p>
      )}

      {state.status === "loading" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Checking {retailer}…
        </p>
      )}

      {state.status === "error" && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          Couldn't reach the coupon feed. The price above is unaffected.
        </p>
      )}

      {state.status === "done" && !offer && (
        <p className="text-neutral-700" style={{ fontSize: "13.5px", margin: 0 }}>
          No active codes for {retailer} right now. The saving above already stands on
          its own.
        </p>
      )}

      {offer && (
        <>
          <p style={{ fontSize: "13.5px", fontWeight: 700, lineHeight: 1.35, margin: 0 }}>
            {offer.discount_description}
          </p>
          {saving && (
            <p
              className="text-accent-2-700 font-bold"
              style={{ fontSize: "13px", margin: "var(--space-1) 0 0" }}
            >
              {saving}
            </p>
          )}

          {offer.code ? (
            <button
              onClick={() => copyCode(offer.code as string)}
              className="w-full inline-flex items-center justify-center gap-2 rounded-full border border-accent-300 bg-accent-100 text-accent-800 hover:bg-accent-200 transition-colors cursor-pointer"
              style={{
                marginTop: "var(--space-3)",
                padding: "var(--space-2) var(--space-3)",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                fontSize: "14px",
                letterSpacing: "0.06em",
              }}
            >
              {offer.code}
              {copied ? (
                <Check size={13} strokeWidth={2.75} />
              ) : (
                <Copy size={13} strokeWidth={2.75} />
              )}
            </button>
          ) : (
            <p
              className="text-neutral-700"
              style={{ fontSize: "12.5px", margin: "var(--space-2) 0 0" }}
            >
              No code needed — the discount applies at checkout.
            </p>
          )}

          {offer.expires_at && (
            <p
              className="text-neutral-700"
              style={{ fontSize: "12px", margin: "var(--space-2) 0 0" }}
            >
              Expires {new Date(offer.expires_at).toLocaleDateString()}
            </p>
          )}
        </>
      )}
    </div>
  );
}

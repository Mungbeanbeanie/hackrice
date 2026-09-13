import { extractProduct, isCheckoutTrigger } from "./detect";
import { renderError, renderLoading, renderResults } from "./popup";
import type { PopupProduct } from "./popup";

// WEBAPP_URL comes from build.mjs's esbuild `define` (see src/global.d.ts).

interface SearchApiProduct {
  short: string;
  price: number;
  matchScore: number;
  rating: number;
  image: string;
}

interface SearchApiResponse {
  targetProduct: SearchApiProduct | null;
  groups: {
    same_spec: SearchApiProduct[];
    same_job: SearchApiProduct[];
    clears_floor: SearchApiProduct[];
  };
}

interface SearchMessageResponse {
  ok: boolean;
  data?: SearchApiResponse;
  error?: string;
}

function toPopupProduct(p: SearchApiProduct): PopupProduct {
  return { short: p.short, price: p.price, matchScore: p.matchScore, rating: p.rating, image: p.image };
}

document.addEventListener(
  "click",
  (event) => {
    if (!isCheckoutTrigger(event.target as Element | null)) return;

    const { title } = extractProduct(document);
    if (!title) return;

    renderLoading();
    chrome.runtime.sendMessage(
      { type: "search", title },
      (response: SearchMessageResponse | undefined) => {
        if (chrome.runtime.lastError || !response?.ok || !response.data) {
          renderError("Couldn't reach nectarly right now.");
          return;
        }

        const { targetProduct, groups } = response.data;
        const products = [...groups.same_spec, ...groups.same_job, ...groups.clears_floor].map(
          toPopupProduct,
        );

        renderResults({ targetPrice: targetProduct?.price ?? null, products }, () => {
          window.open(`${WEBAPP_URL}/?q=${encodeURIComponent(title)}`, "_blank");
        });
      },
    );
  },
  // Capture phase: a page's own handler calling stopPropagation on the button
  // must not hide the click from us.
  true,
);

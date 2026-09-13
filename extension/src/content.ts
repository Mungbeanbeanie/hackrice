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

// Same value/rationale as frontend/src/api/client.ts's SEARCH_TIMEOUT_MS —
// same backend endpoint, cold search measured at 38-71s.
const SEARCH_TIMEOUT_MS = 130_000;

// Guards two failure modes: (1) two overlapping clicks resolving out of
// order — extractProduct(document) is page-level, so this mostly shows up as
// a redundant duplicate search rather than a wrong product, except on an SPA
// storefront that rewrites title/meta between clicks without a full
// navigation, where it can genuinely be a different product; (2)
// background.ts's fetch never responding at all. The timeout lives here,
// not in background.ts, because a killed/idle-terminated MV3 service worker
// would take a timer inside itself down too — content.ts is the side whose
// UI is actually stuck, so it can't depend on background.ts always getting
// to run.
let latestRequestId = 0;

document.addEventListener(
  "click",
  (event) => {
    if (!isCheckoutTrigger(event.target as Element | null)) return;

    const { title } = extractProduct(document);
    if (!title) return;

    const requestId = ++latestRequestId;
    renderLoading();

    const timer = window.setTimeout(() => {
      if (requestId !== latestRequestId) return;
      renderError("Search timed out. Try again.");
    }, SEARCH_TIMEOUT_MS);

    chrome.runtime.sendMessage(
      { type: "search", title },
      (response: SearchMessageResponse | undefined) => {
        window.clearTimeout(timer);
        if (requestId !== latestRequestId) return;

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

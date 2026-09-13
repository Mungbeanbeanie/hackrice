import { extractProduct, isCheckoutTrigger } from "./detect";
import { close, renderError, renderLoading, renderResults } from "./popup";
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

// Some sites (e.g. Amazon's desktop "Add to Cart") do a full page navigation
// to a cart page rather than updating in place — that tears down this whole
// script, including any in-flight search, before the popup ever shows.
// sessionStorage survives a same-origin navigation within the same tab, so a
// click stashes {title, ts} here and the freshly-injected script on whatever
// page loads next picks it up and re-runs the search there. Known limits,
// accepted rather than hidden: only survives same-origin navigation (a
// cross-origin checkout handoff, e.g. PayPal-hosted, won't carry it over),
// and sessionStorage is shared with the destination page's own JS — if that
// page clears its own sessionStorage before this script reads it, the stash
// is silently lost with no way to detect it happened.
const PENDING_KEY = "nectarly-pending-search";
// Comfortably covers a real add-to-cart redirect (typically sub-few-seconds)
// while keeping short the window during which a manually-navigated-away,
// still-in-flight, non-navigating search could wrongly resurrect on an
// unrelated later page.
const PENDING_EXPIRY_MS = 20_000;

function stashPendingSearch(title: string): void {
  try {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify({ title, ts: Date.now() }));
  } catch {
    // Storage can throw under some privacy/quota restrictions — losing the
    // handoff just means the popup won't survive navigation on this page,
    // not a crash.
  }
}

function clearPendingSearch(): void {
  try {
    sessionStorage.removeItem(PENDING_KEY);
  } catch {
    // Same as above — non-fatal.
  }
}

function takePendingSearch(): string | null {
  let raw: string | null;
  try {
    raw = sessionStorage.getItem(PENDING_KEY);
    sessionStorage.removeItem(PENDING_KEY);
  } catch {
    return null;
  }
  if (!raw) return null;
  try {
    const { title, ts } = JSON.parse(raw) as { title: string; ts: number };
    if (!title || Date.now() - ts > PENDING_EXPIRY_MS) return null;
    return title;
  } catch {
    return null;
  }
}

function runSearch(title: string): void {
  const requestId = ++latestRequestId;
  renderLoading();

  const timer = window.setTimeout(() => {
    if (requestId !== latestRequestId) return;
    clearPendingSearch();
    renderError("Search timed out. Try again.");
  }, SEARCH_TIMEOUT_MS);

  chrome.runtime.sendMessage(
    { type: "search", title },
    (response: SearchMessageResponse | undefined) => {
      window.clearTimeout(timer);
      if (requestId !== latestRequestId) return;
      clearPendingSearch();

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
}

document.addEventListener(
  "click",
  (event) => {
    if (!isCheckoutTrigger(event.target as Element | null)) return;

    const { title } = extractProduct(document);
    if (!title) return;

    stashPendingSearch(title);
    runSearch(title);
  },
  // Capture phase: a page's own handler calling stopPropagation on the button
  // must not hide the click from us.
  true,
);

// Picks up a search abandoned by a full-page navigation (see the sessionStorage
// comment above) — runs once per fresh content-script injection, a no-op the
// overwhelming majority of the time since there's usually nothing pending.
const pending = takePendingSearch();
if (pending) runSearch(pending);

// bfcache restores a frozen snapshot of whatever the popup looked like at the
// moment the page was suspended (mid-search, or an old result) — never
// accurate to what the user is doing now, so just dismiss it. This does not
// try to re-trigger anything; the sessionStorage handoff above is what
// ensures the popup gets shown productively on a forward navigation.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) close();
});

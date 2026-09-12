// Mirrors the response models in backend/app/routes/search.py.
//
// One search box: the backend infers url / exact_product / description from the
// raw string, so no mode is sent.
export interface SearchRequest {
  query: string;
}

export type Verdict = "same" | "better" | "close" | "different" | "lower";
export type Group = "same_spec" | "same_job" | "clears_floor";
export type SearchMode = "url" | "exact_product" | "description";

export interface ProductSpec {
  key: string;
  value: string;
  // null when the target carries no such spec to compare against — and for
  // every spec in description mode, where no target is resolved at all.
  verdict: Verdict | null;
}

export interface Product {
  id: string;
  name: string;
  short: string;
  brand: string;
  price: number;
  originalPrice?: number;
  image: string;
  retailer: string;
  retailerLogo?: string;
  url: string;
  rating: number;
  reviewCount: number;
  specs: ProductSpec[];
  matchScore: number;
  // Absent when no target was resolved, or when this candidate costs more than
  // the target. Never negative.
  savings?: number;
  savingsPercent?: number;
  // Absent on the target product: it is the reference, not a candidate being
  // argued for.
  rationale?: string;
}

export interface SearchResponse {
  query: string;
  // null when the backend read the query as a description rather than a
  // specific product — there is no single target to anchor against.
  targetProduct: Product | null;
  groups: Record<Group, Product[]>;
  mode: SearchMode;
  // What every savings figure and share bar is measured against. In description
  // mode this is the median of the candidate set, so it is set even though
  // targetProduct is null — it is a price, not a product anyone can buy.
  baselinePrice: number | null;
}

const BASE_URL = "/api";

// A cold search is a live scrape upstream, measured at 38-71s. The ceiling sits
// above the backend's own read timeout so the server's error message wins the
// race and the user learns what broke; this only catches a connection that
// stopped answering entirely, which otherwise hangs the UI forever.
const SEARCH_TIMEOUT_MS = 130_000;

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function searchProducts(req: SearchRequest): Promise<SearchResponse> {
  try {
    return await apiFetch<SearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify(req),
      signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS),
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") {
      throw new Error("Search timed out. The retailer index is slow right now.");
    }
    throw e;
  }
}

// Mirrors backend/app/coupons/models.py.
export interface CouponOffer {
  // null for "Deal" offers — a discount that needs no code at checkout.
  code: string | null;
  discount_description: string;
  store: string;
  expires_at: string | null;
  start_date: string | null;
  rating: number;
}

// Resolves to null, not an error, when the store has no active offer — the
// endpoint answers 200 with a literal `null` body.
export async function fetchCoupon(store: string): Promise<CouponOffer | null> {
  return apiFetch<CouponOffer | null>(`/coupons?store=${encodeURIComponent(store)}`);
}

export interface Account {
  id: string;
  email: string;
  created_at: string;
}

export async function requestSignInCode(email: string): Promise<void> {
  await apiFetch<{ status: string }>("/auth/request-code", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function verifySignInCode(email: string, code: string): Promise<Account> {
  return apiFetch<Account>("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

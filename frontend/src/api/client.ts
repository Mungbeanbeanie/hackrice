// Mirrors the response models in backend/app/routes/search.py. Keep the two in
// step: the backend serializes these field names directly, with no adapter.
//
// One search box: the backend infers url / exact_product / description from the
// raw string, so no mode is sent.
export interface SearchRequest {
  query: string;
}

export interface ProductSpec {
  key: string;
  value: string;
}

export interface Product {
  id: string;
  name: string;
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
  tier: 1 | 2 | 3;
  badge?: string;
}

export interface SearchResponse {
  query: string;
  // null when the backend read the query as a description rather than a
  // specific product — there is no single target to anchor against.
  targetProduct: Product | null;
  tiers: {
    tier1: Product[];
    tier2: Product[];
    tier3: Product[];
  };
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

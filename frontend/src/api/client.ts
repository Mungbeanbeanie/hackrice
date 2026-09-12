// The response types below are provisional and shaped for the UI. The backend
// pipeline (plan.md Phase 5) has not defined /api/search or /api/compare/{id}
// yet — when it does, either it matches these or the mapping lands here.
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
  savings?: number;
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

export interface CompareResponse {
  product: Product;
  targetProduct: Product | null;
  specComparison: {
    spec: string;
    target: string;
    alternative: string;
    winner: "target" | "alternative" | "tie";
  }[];
}

const BASE_URL = "/api";

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
  return apiFetch<SearchResponse>("/search", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function compareProduct(id: string): Promise<CompareResponse> {
  return apiFetch<CompareResponse>(`/compare/${id}`);
}

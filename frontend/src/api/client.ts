// Mirrors the response models in backend/app/routes/search.py — EXCEPT for the
// `groups`/`verdict`/`rationale`/`short` fields below, which the backend does not
// send yet. Those are stubbed client-side in `adaptSearchResponse` so the Organic
// redesign (frontend/design_handoff_nectarly_production/) can ship ahead of the
// backend data-contract change described there. Replace the stub with a real
// `groups` field on `LegacySearchResponse`/`WireProduct` once that phase lands,
// and delete `adaptSearchResponse`.
//
// One search box: the backend infers url / exact_product / description from the
// raw string, so no mode is sent.
export interface SearchRequest {
  query: string;
}

export type Verdict = "same" | "better" | "equivalent" | "close" | "different" | "lower";
export type Group = "same_spec" | "same_job" | "clears_floor";

export interface ProductSpec {
  key: string;
  value: string;
  verdict: Verdict;
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
  group: Group;
  rationale: string;
}

export interface SearchResponse {
  query: string;
  // null when the backend read the query as a description rather than a
  // specific product — there is no single target to anchor against.
  targetProduct: Product | null;
  groups: Record<Group, Product[]>;
}

// --- Legacy wire shape (what /api/search actually returns today) ---

interface LegacyProductSpec {
  key: string;
  value: string;
}

interface LegacyProduct {
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
  specs: LegacyProductSpec[];
  matchScore: number;
  savings?: number;
  savingsPercent?: number;
  tier: 1 | 2 | 3;
}

interface LegacySearchResponse {
  query: string;
  targetProduct: LegacyProduct | null;
  tiers: {
    tier1: LegacyProduct[];
    tier2: LegacyProduct[];
    tier3: LegacyProduct[];
  };
}

const TIER_TO_GROUP: Record<1 | 2 | 3, Group> = {
  1: "same_spec",
  2: "same_job",
  3: "clears_floor",
};

// ponytail: no `direction` metadata on specs yet (backend still ships bare
// key/value pairs), so this can only compare values, not judge which side is
// "better". Same-value and same-magnitude reads are trustworthy; everything
// else collapses to "different" rather than guessing a direction. Replace with
// a real verdict once SpecAttribute carries higher/lower/neutral direction.
function stubVerdict(targetValue: string | undefined, value: string): Verdict {
  if (targetValue === undefined) return "different";
  const a = targetValue.trim().toLowerCase();
  const b = value.trim().toLowerCase();
  if (a === b) return "same";
  const numA = parseFloat(a);
  const numB = parseFloat(b);
  if (!Number.isNaN(numA) && !Number.isNaN(numB) && numA !== 0) {
    const ratio = numB / numA;
    if (ratio >= 0.95 && ratio <= 1.05) return "close";
  }
  return "different";
}

// ponytail: template stand-in for the rationale sentence a real explanation
// pipeline would write. Built entirely from numbers already on the wire.
function stubRationale(p: LegacyProduct): string {
  const bits = [`${Math.round(p.matchScore)}% spec match`];
  if (p.savingsPercent != null) {
    bits.push(`saves ${Math.round(p.savingsPercent)}% versus the reference product`);
  }
  bits.push(`rated ${p.rating.toFixed(1)} across ${p.reviewCount.toLocaleString()} reviews`);
  return bits.join(", ") + ".";
}

function stubShort(name: string): string {
  return name.split(" ").slice(0, 3).join(" ");
}

function adaptProduct(p: LegacyProduct, target: LegacyProduct | null): Product {
  return {
    id: p.id,
    name: p.name,
    short: stubShort(p.name),
    brand: p.brand,
    price: p.price,
    originalPrice: p.originalPrice,
    image: p.image,
    retailer: p.retailer,
    retailerLogo: p.retailerLogo,
    url: p.url,
    rating: p.rating,
    reviewCount: p.reviewCount,
    specs: p.specs.map((s) => ({
      ...s,
      verdict: stubVerdict(target?.specs.find((t) => t.key === s.key)?.value, s.value),
    })),
    matchScore: p.matchScore,
    savings: p.savings,
    savingsPercent: p.savingsPercent,
    group: TIER_TO_GROUP[p.tier],
    rationale: stubRationale(p),
  };
}

function adaptTargetProduct(p: LegacyProduct): Product {
  return adaptProduct(p, null);
}

function adaptSearchResponse(res: LegacySearchResponse): SearchResponse {
  const target = res.targetProduct;
  return {
    query: res.query,
    targetProduct: target ? adaptTargetProduct(target) : null,
    groups: {
      same_spec: res.tiers.tier1.map((p) => adaptProduct(p, target)),
      same_job: res.tiers.tier2.map((p) => adaptProduct(p, target)),
      clears_floor: res.tiers.tier3.map((p) => adaptProduct(p, target)),
    },
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
    const legacy = await apiFetch<LegacySearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify(req),
      signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS),
    });
    return adaptSearchResponse(legacy);
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") {
      throw new Error("Search timed out. The retailer index is slow right now.");
    }
    throw e;
  }
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

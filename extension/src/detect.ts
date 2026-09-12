const TRIGGER_TEXT = /add to (cart|bag)|buy now|checkout|place order/i;
const MAX_ANCESTOR_DEPTH = 3;
const MAX_TRIGGER_TEXT_LENGTH = 60;

// Button text often lives on a child <span>/<svg> sibling rather than the
// element that actually received the click, so this walks a few ancestor
// levels up rather than checking `target` alone.
export function isCheckoutTrigger(target: Element | null): boolean {
  let el: Element | null = target;
  for (let depth = 0; el && depth <= MAX_ANCESTOR_DEPTH; depth++, el = el.parentElement) {
    const text = el.textContent?.trim();
    if (text && text.length <= MAX_TRIGGER_TEXT_LENGTH && TRIGGER_TEXT.test(text)) {
      return true;
    }
  }
  return false;
}

export interface DetectedProduct {
  title: string;
  price: number | null;
  image: string | null;
}

function parsePrice(value: unknown): number | null {
  const num =
    typeof value === "string" ? parseFloat(value) : typeof value === "number" ? value : NaN;
  return Number.isFinite(num) ? num : null;
}

interface ProductNode {
  name?: unknown;
  offers?: { price?: unknown } | Array<{ price?: unknown }>;
  image?: unknown;
}

function findProductNode(data: unknown): ProductNode | null {
  const nodes = Array.isArray(data) ? data : [data];
  for (const node of nodes) {
    if (!node || typeof node !== "object") continue;
    const record = node as Record<string, unknown>;
    if (record["@type"] === "Product") return record as ProductNode;
    if (Array.isArray(record["@graph"])) {
      const found = record["@graph"].find(
        (n) => n && typeof n === "object" && (n as Record<string, unknown>)["@type"] === "Product",
      );
      if (found) return found as ProductNode;
    }
  }
  return null;
}

function fromJsonLd(doc: Document): DetectedProduct | null {
  const scripts = doc.querySelectorAll('script[type="application/ld+json"]');
  for (const script of scripts) {
    let data: unknown;
    try {
      data = JSON.parse(script.textContent || "");
    } catch {
      continue;
    }
    const product = findProductNode(data);
    if (!product) continue;

    const offers = Array.isArray(product.offers) ? product.offers[0] : product.offers;
    const image = Array.isArray(product.image) ? product.image[0] : product.image;

    return {
      title: String(product.name ?? ""),
      price: parsePrice(offers?.price),
      image: typeof image === "string" ? image : null,
    };
  }
  return null;
}

function fromOpenGraph(doc: Document): DetectedProduct | null {
  const title = doc.querySelector('meta[property="og:title"]')?.getAttribute("content");
  if (!title) return null;
  const priceRaw = doc
    .querySelector('meta[property="product:price:amount"]')
    ?.getAttribute("content");
  const image = doc.querySelector('meta[property="og:image"]')?.getAttribute("content") ?? null;
  return { title, price: parsePrice(priceRaw), image };
}

// Never returns null — mirrors serpapi_client._parse_price_string's
// always-returns-something pattern, so a caller never has to branch on "no
// product detected at all", only on a possibly-empty title/price/image.
export function extractProduct(doc: Document): DetectedProduct {
  return fromJsonLd(doc) ?? fromOpenGraph(doc) ?? { title: doc.title, price: null, image: null };
}

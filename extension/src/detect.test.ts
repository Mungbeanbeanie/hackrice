import { describe, expect, it } from "vitest";

import { extractProduct, isCheckoutTrigger } from "./detect";

function docFrom(html: string): Document {
  return new DOMParser().parseFromString(html, "text/html");
}

describe("extractProduct", () => {
  it("reads a JSON-LD Product node", () => {
    const doc = docFrom(`
      <script type="application/ld+json">
        {"@type": "Product", "name": "Ergo Pillow", "offers": {"price": "29.99"}, "image": "a.jpg"}
      </script>
    `);
    expect(extractProduct(doc)).toEqual({ title: "Ergo Pillow", price: 29.99, image: "a.jpg" });
  });

  it("finds a Product inside an @graph array", () => {
    const doc = docFrom(`
      <script type="application/ld+json">
        {"@graph": [{"@type": "WebPage"}, {"@type": "Product", "name": "Graph Pillow", "offers": [{"price": 15}], "image": ["b.jpg", "c.jpg"]}]}
      </script>
    `);
    expect(extractProduct(doc)).toEqual({ title: "Graph Pillow", price: 15, image: "b.jpg" });
  });

  it("falls back to OpenGraph when JSON-LD is malformed", () => {
    const doc = docFrom(`
      <script type="application/ld+json">not json</script>
      <meta property="og:title" content="OG Pillow">
      <meta property="product:price:amount" content="19.5">
      <meta property="og:image" content="og.jpg">
    `);
    expect(extractProduct(doc)).toEqual({ title: "OG Pillow", price: 19.5, image: "og.jpg" });
  });

  it("falls back to OpenGraph when there is no JSON-LD at all", () => {
    const doc = docFrom(`<meta property="og:title" content="Plain OG">`);
    expect(extractProduct(doc)).toEqual({ title: "Plain OG", price: null, image: null });
  });

  it("falls back to the document title when nothing else is present", () => {
    const doc = docFrom(`<title>Bare Title</title>`);
    expect(extractProduct(doc)).toEqual({ title: "Bare Title", price: null, image: null });
  });
});

describe("isCheckoutTrigger", () => {
  it("matches when the clicked element's own text matches", () => {
    const doc = docFrom(`<button>Add to Cart</button>`);
    expect(isCheckoutTrigger(doc.querySelector("button"))).toBe(true);
  });

  it("matches when a matching ancestor wraps the actual click target", () => {
    const doc = docFrom(`<button><span><svg></svg>Buy Now</span></button>`);
    expect(isCheckoutTrigger(doc.querySelector("svg"))).toBe(true);
  });

  it("does not match unrelated text", () => {
    const doc = docFrom(`<button>Learn more</button>`);
    expect(isCheckoutTrigger(doc.querySelector("button"))).toBe(false);
  });

  it("does not match past the ancestor depth limit", () => {
    const doc = docFrom(`<button>Add to Cart<span><span><span><span>x</span></span></span></span></button>`);
    const deepest = doc.querySelector("span > span > span > span");
    expect(isCheckoutTrigger(deepest)).toBe(false);
  });

  it("returns false for a null target", () => {
    expect(isCheckoutTrigger(null)).toBe(false);
  });
});

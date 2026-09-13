import { describe, expect, it, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import CouponPanel from "@/components/CouponPanel";
import type { CouponOffer, Product } from "@/api/client";

vi.mock("@/api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/api/client")>()),
  fetchCoupon: vi.fn(),
  viewPriceHistory: vi.fn(),
}));

const { fetchCoupon, viewPriceHistory } = await import("@/api/client");

const product = (price: number): Product => ({
  id: "c1",
  name: "Contour Pillow",
  short: "Contour Pillow",
  brand: "Generic",
  price,
  image: "",
  retailer: "Dick's Sporting Goods",
  url: "https://example.com",
  rating: 4.2,
  reviewCount: 100,
  specs: [],
  matchScore: 90,
});

const offer = (description: string, code: string | null = "SAVE35"): CouponOffer => ({
  code,
  discount_description: description,
  store: "dickssportinggoods.com",
  expires_at: null,
  start_date: null,
  rating: 2,
});

beforeEach(() => {
  vi.mocked(fetchCoupon).mockReset();
  // The folded history section fires its own fetch on selection; without a
  // stub it would hit a real relative URL under jsdom.
  vi.mocked(viewPriceHistory)
    .mockReset()
    .mockResolvedValue({
      sufficient: false,
      current: null,
      low: null,
      high: null,
      pct_above_low: null,
      trend: null,
    });
});
// vite.config.ts sets no `globals: true` and no setup file, so Testing
// Library's auto-cleanup never registers and renders stack up across tests.
afterEach(cleanup);

describe("CouponPanel", () => {
  it("turns a percentage in the offer text into a dollar figure", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(offer("Save 35% off with Autoship"));
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText("about $28.00 off this item")).toBeTruthy();
  });

  it("reads a flat dollar discount", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(offer("$15 off orders over $50"));
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText("$15.00 off this item")).toBeTruthy();
  });

  it("says nothing about savings when the text states no figure", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(offer("Free shipping sitewide"));
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText("Free shipping sitewide")).toBeTruthy();
    expect(screen.queryByText(/off this item/)).toBeNull();
  });

  it("does not claim a discount larger than the item itself", async () => {
    // "$50 off orders over $500" against a $20 item would otherwise read as
    // saving more than the product costs.
    vi.mocked(fetchCoupon).mockResolvedValue(offer("$50 off orders over $500"));
    render(<CouponPanel product={product(20)} />);
    expect(await screen.findByText("$50 off orders over $500")).toBeTruthy();
    expect(screen.queryByText(/off this item/)).toBeNull();
  });

  it("explains that a code-less deal needs no code", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(offer("20% off sitewide", null));
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText(/No code needed/)).toBeTruthy();
  });

  it("prompts for a selection before anything is picked", () => {
    render(<CouponPanel product={null} />);
    expect(screen.getByText(/Pick any result/)).toBeTruthy();
    expect(fetchCoupon).not.toHaveBeenCalled();
    expect(viewPriceHistory).not.toHaveBeenCalled();
  });

  it("reports an empty result without implying an error", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(null);
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText(/No active codes/)).toBeTruthy();
  });

  it("folds the selected result's price history in under the coupon", async () => {
    vi.mocked(fetchCoupon).mockResolvedValue(null);
    render(<CouponPanel product={product(80)} />);
    expect(await screen.findByText(/Not enough history yet/)).toBeTruthy();
    expect(viewPriceHistory).toHaveBeenCalledTimes(1);
  });
});

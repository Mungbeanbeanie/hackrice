import { describe, expect, it, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import PriceHistoryPanel from "@/components/PriceHistoryPanel";
import type { PriceHistorySummary, Product } from "@/api/client";

vi.mock("@/api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/api/client")>()),
  viewPriceHistory: vi.fn(),
}));

const { viewPriceHistory } = await import("@/api/client");

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

const summary = (overrides: Partial<PriceHistorySummary> = {}): PriceHistorySummary => ({
  sufficient: true,
  current: 42,
  low: 38,
  high: 50,
  pct_above_low: 10.5,
  trend: "flat",
  ...overrides,
});

beforeEach(() => vi.mocked(viewPriceHistory).mockReset());
// vite.config.ts sets no `globals: true` and no setup file, so Testing
// Library's auto-cleanup never registers and renders stack up across tests.
afterEach(cleanup);

describe("PriceHistoryPanel", () => {
  it("prompts for a selection before anything is picked", () => {
    render(<PriceHistoryPanel product={null} />);
    expect(screen.getByText(/Pick any result/)).toBeTruthy();
    expect(viewPriceHistory).not.toHaveBeenCalled();
  });

  it("says there isn't enough history yet, below the 3-snapshot threshold", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue({ sufficient: false } as PriceHistorySummary);
    render(<PriceHistoryPanel product={product(42)} />);
    expect(await screen.findByText(/Not enough history yet/)).toBeTruthy();
  });

  it("shows the recorded-low positioning once there's enough history", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue(summary({ pct_above_low: 10, low: 38 }));
    render(<PriceHistoryPanel product={product(42)} />);
    expect(await screen.findByText(/10% above its recorded low of \$38\.00/)).toBeTruthy();
  });

  it("says 'at its recorded low' rather than '0% above'", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue(summary({ pct_above_low: 0, current: 38, low: 38 }));
    render(<PriceHistoryPanel product={product(38)} />);
    expect(await screen.findByText("At its recorded low")).toBeTruthy();
  });

  it("never claims a trend when the direction is flat", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue(summary({ trend: "flat" }));
    render(<PriceHistoryPanel product={product(42)} />);
    await screen.findByText(/recorded low/);
    expect(screen.queryByText(/Trending/)).toBeNull();
  });

  it("shows a trend direction when one exists", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue(summary({ trend: "down" }));
    render(<PriceHistoryPanel product={product(42)} />);
    expect(await screen.findByText(/Trending down/)).toBeTruthy();
  });

  it("records a view once per selected product, not on every render", async () => {
    vi.mocked(viewPriceHistory).mockResolvedValue(summary());
    render(<PriceHistoryPanel product={product(42)} />);
    await screen.findByText(/recorded low/);
    expect(viewPriceHistory).toHaveBeenCalledTimes(1);
    expect(viewPriceHistory).toHaveBeenCalledWith(
      "Contour Pillow",
      "Generic",
      "Dick's Sporting Goods",
      42,
    );
  });
});

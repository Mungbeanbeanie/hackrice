import { expect, test, vi, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import App from "@/App";
import { searchProducts, type Product, type SearchResponse } from "@/api/client";

// Every network call App makes on mount or navigation. getCurrentAccount
// resolving null is the signed-out visitor, which is the path under test.
vi.mock("@/api/client", () => ({
  getCurrentAccount: vi.fn(() => Promise.resolve(null)),
  searchProducts: vi.fn(() => Promise.resolve(null)),
  signOut: vi.fn(() => Promise.resolve()),
}));

const candidate: Product = {
  id: "c1",
  name: "Generic Contour Pillow",
  short: "Generic Contour",
  brand: "Unbranded",
  price: 48,
  image: "",
  retailer: "example.com",
  url: "https://example.com/c1",
  rating: 4.3,
  reviewCount: 120,
  specs: [],
  matchScore: 91,
  savings: 30,
};

const describedResponse: SearchResponse = {
  query: "ergonomic pillow",
  // Description mode: no target resolved, baseline is the candidate median.
  targetProduct: null,
  groups: { same_spec: [candidate], same_job: [], clears_floor: [] },
  mode: "description",
  baselinePrice: 78,
};

// jsdom has no HTMLDialogElement — same stub as AccountMenu.test.tsx.
Object.defineProperty(HTMLElement.prototype, "showModal", { value: vi.fn(), writable: true });
Object.defineProperty(HTMLElement.prototype, "close", { value: vi.fn(), writable: true });

beforeEach(() => {
  vi.clearAllMocks();
  cleanup();
  history.replaceState(null, "");
});

// The bug this guards: the app was a pure in-memory state machine, so the URL
// never moved and Back left the site entirely instead of stepping back a
// screen. Both halves have to hold — the push on navigate, and the restore on
// pop — and neither shows up in a typecheck.
test("navigating pushes a history entry and Back restores the previous screen", async () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: /pay for the product/i })).toBeTruthy();

  screen.getByRole("button", { name: /sign in/i }).click();

  expect(history.state?.screen).toBe("signin");
  await vi.waitFor(() => expect(screen.getByText(/keep what you found/i)).toBeTruthy());

  // What the browser dispatches on Back to the very first entry, whose state
  // this app never set.
  dispatchEvent(new PopStateEvent("popstate", { state: null }));

  await vi.waitFor(() =>
    expect(screen.getByRole("heading", { name: /pay for the product/i })).toBeTruthy(),
  );
});

test("navigating to the screen already showing does not stack a dead entry", () => {
  render(<App />);
  const before = history.length;

  // The landing hero's example chips run a search, which routes through goTo.
  screen.getByRole("button", { name: "purple harmony pillow" }).click();
  screen.getByRole("button", { name: "sony wh-1000xm5" }).click();

  expect(history.state?.screen).toBe("app");
  expect(history.length).toBe(before + 1);
});

// The bug this guards: the sidebar re-derived the figure client-side, so with
// no target resolved it printed the candidate's own price under the heading
// "Possible Savings" — a $48 pillow claiming to save you $48.
test("the savings box shows the backend's savings figure, not the price", async () => {
  vi.mocked(searchProducts).mockResolvedValue(describedResponse);
  render(<App />);

  screen.getByRole("button", { name: "purple harmony pillow" }).click();

  // Exact match, so the card's own "saves $30.00" line does not count — only
  // the box's bare figure does. The card's "$48.00" price is legitimate.
  await vi.waitFor(() => expect(screen.getByText("$30.00")).toBeTruthy());
});

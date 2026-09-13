import { expect, test, vi, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import App from "@/App";

// Every network call App makes on mount or navigation. getCurrentAccount
// resolving null is the signed-out visitor, which is the path under test.
vi.mock("@/api/client", () => ({
  getCurrentAccount: vi.fn(() => Promise.resolve(null)),
  searchProducts: vi.fn(() => Promise.resolve(null)),
  signOut: vi.fn(() => Promise.resolve()),
}));

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

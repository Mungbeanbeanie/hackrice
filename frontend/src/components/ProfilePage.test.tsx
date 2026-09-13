import { expect, test, vi, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import ProfilePage from "@/components/ProfilePage";
import type { Account, SearchHistoryItem } from "@/api/client";

vi.mock("@/api/client", () => ({
  fetchSearchHistory: vi.fn(),
  clearSearchHistory: vi.fn(() => Promise.resolve(1)),
}));
const { fetchSearchHistory, clearSearchHistory } = await import("@/api/client");

const account: Account = {
  id: "acc-1",
  email: "a@b.com",
  created_at: new Date().toISOString(),
  display_name: null,
  avatar: null,
  share_data: true,
};

const row: SearchHistoryItem = {
  id: 1,
  query: "memory foam pillow",
  mode: "exact_product",
  result_count: 12,
  created_at: new Date().toISOString(),
};

beforeEach(() => {
  vi.clearAllMocks();
  cleanup();
  vi.mocked(fetchSearchHistory).mockResolvedValue([row]);
});

const noop = { onBack: () => {}, onRerun: () => {} };

test("clicking a row asks to re-run that query", async () => {
  const onRerun = vi.fn();
  render(<ProfilePage {...noop} account={account} onRerun={onRerun} />);

  const again = await screen.findByRole("button", { name: /again/i });
  again.click();

  expect(onRerun).toHaveBeenCalledWith("memory foam pillow");
});

// The data-loss guard: declining the confirm must not delete anything.
test("declining the confirmation leaves the history alone", async () => {
  vi.stubGlobal("confirm", () => false);
  render(<ProfilePage {...noop} account={account} />);

  (await screen.findByRole("button", { name: /clear history/i })).click();

  expect(clearSearchHistory).not.toHaveBeenCalled();
  vi.unstubAllGlobals();
});

test("accepting the confirmation clears it and empties the table", async () => {
  vi.stubGlobal("confirm", () => true);
  render(<ProfilePage {...noop} account={account} />);

  (await screen.findByRole("button", { name: /clear history/i })).click();

  await vi.waitFor(() => expect(clearSearchHistory).toHaveBeenCalled());
  await screen.findByText(/no searches yet/i);
  vi.unstubAllGlobals();
});

// Sharing off still keeps personal history, so the page has to say so rather
// than look broken.
test("explains itself when data sharing is off", async () => {
  render(<ProfilePage {...noop} account={{ ...account, share_data: false }} />);
  expect(await screen.findByText(/data sharing is off/i)).toBeTruthy();
});

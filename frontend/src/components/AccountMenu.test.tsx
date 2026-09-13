import { expect, test, vi, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import AccountMenu from "@/components/AccountMenu";
import type { Account } from "@/api/client";

vi.mock("@/api/client", () => ({ signOut: vi.fn(() => Promise.resolve()) }));
const { signOut } = await import("@/api/client");

// jsdom has no HTMLDialogElement — same stub as TermsLink.test.tsx.
const showModal = vi.fn();
const close = vi.fn();
Object.defineProperty(HTMLElement.prototype, "showModal", { value: showModal, writable: true });
Object.defineProperty(HTMLElement.prototype, "close", { value: close, writable: true });

const account: Account = {
  id: "acc-1",
  email: "a@b.com",
  created_at: new Date().toISOString(),
  display_name: null,
  avatar: null,
  share_data: true,
};

beforeEach(() => {
  vi.clearAllMocks();
  cleanup();
});

const noop = { onSignIn: () => {}, onProfile: () => {}, onSettings: () => {}, onSignedOut: () => {} };

test("signed out, the pill goes straight to sign-in and opens no menu", () => {
  const onSignIn = vi.fn();
  render(<AccountMenu {...noop} account={null} onSignIn={onSignIn} />);

  screen.getByRole("button", { name: /sign in/i }).click();

  expect(onSignIn).toHaveBeenCalled();
  expect(showModal).not.toHaveBeenCalled();
});

// The regression guard on the bug this component exists to fix: a signed-in
// user used to be sent back to the sign-in form by this very button.
test("signed in, the pill opens the menu instead of the sign-in form", () => {
  const onSignIn = vi.fn();
  render(<AccountMenu {...noop} account={account} onSignIn={onSignIn} />);

  screen.getByRole("button", { name: /a@b\.com/ }).click();

  expect(showModal).toHaveBeenCalled();
  expect(onSignIn).not.toHaveBeenCalled();
});

test("log out calls the API and then reports it upward", async () => {
  const onSignedOut = vi.fn();
  render(<AccountMenu {...noop} account={account} onSignedOut={onSignedOut} />);

  // showModal is stubbed, so the <dialog> never really opens and its contents
  // stay inaccessible to role queries — hence hidden: true.
  screen.getByRole("menuitem", { name: /log out/i, hidden: true }).click();
  await vi.waitFor(() => expect(onSignedOut).toHaveBeenCalled());

  expect(signOut).toHaveBeenCalled();
});

test("a display name is shown in place of the email", () => {
  render(<AccountMenu {...noop} account={{ ...account, display_name: "Mica" }} />);
  expect(screen.getByRole("button", { name: /Mica/ })).toBeTruthy();
});

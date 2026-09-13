import { expect, test, vi, beforeEach } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import SettingsPage from "@/components/SettingsPage";
import type { Account } from "@/api/client";

vi.mock("@/api/client", () => ({ updateProfile: vi.fn() }));
const { updateProfile } = await import("@/api/client");

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
  vi.mocked(updateProfile).mockResolvedValue(account);
});

const noop = { onBack: () => {}, onSaved: () => {} };

test("turning off sharing sends share_data false", async () => {
  render(<SettingsPage {...noop} account={account} />);

  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

  await vi.waitFor(() => expect(updateProfile).toHaveBeenCalled());
  expect(updateProfile).toHaveBeenCalledWith(
    expect.objectContaining({ share_data: false }),
  );
});

test("a display name is trimmed before it is sent", async () => {
  render(<SettingsPage {...noop} account={account} />);

  fireEvent.change(screen.getByPlaceholderText("a@b.com"), { target: { value: "  Mica  " } });
  fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

  await vi.waitFor(() => expect(updateProfile).toHaveBeenCalled());
  expect(updateProfile).toHaveBeenCalledWith(
    expect.objectContaining({ display_name: "Mica" }),
  );
});

// createImageBitmap rejects on anything that is not a decodable image; that is
// the client-side type check, so it has to surface rather than throw.
test("an undecodable file reports an error instead of throwing", async () => {
  vi.stubGlobal("createImageBitmap", () => Promise.reject(new Error("bad image")));
  const { container } = render(<SettingsPage {...noop} account={account} />);

  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  fireEvent.change(input, {
    target: { files: [new File(["nope"], "x.txt", { type: "text/plain" })] },
  });

  expect(await screen.findByText(/didn't look like an image/i)).toBeTruthy();
  vi.unstubAllGlobals();
});

test("an existing avatar can be removed, which saves an empty string", async () => {
  render(<SettingsPage {...noop} account={{ ...account, avatar: "data:image/jpeg;base64,AAA" }} />);

  fireEvent.click(screen.getByRole("button", { name: /remove/i }));
  fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

  await vi.waitFor(() => expect(updateProfile).toHaveBeenCalled());
  // "" is the clear signal — the backend lets it past the data:image/ guard.
  expect(updateProfile).toHaveBeenCalledWith(expect.objectContaining({ avatar: "" }));
});

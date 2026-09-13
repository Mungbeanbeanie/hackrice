import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./popup", () => ({
  renderLoading: vi.fn(),
  renderError: vi.fn(),
  renderResults: vi.fn(),
  close: vi.fn(),
}));

import { close, renderLoading } from "./popup";

// content.ts's module top level touches both `chrome` and sessionStorage
// synchronously during import, so both must be ready BEFORE the dynamic
// import fires, not after.
const PENDING_KEY = "nectarly-pending-search";

function stubChrome(sendMessage: ReturnType<typeof vi.fn> = vi.fn()): void {
  vi.stubGlobal("chrome", { runtime: { sendMessage, lastError: undefined } });
}

beforeEach(() => {
  sessionStorage.clear();
  vi.mocked(renderLoading).mockClear();
  vi.mocked(close).mockClear();
});

afterEach(() => {
  sessionStorage.clear();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("content.ts pending-search handoff (module load)", () => {
  it("auto-resumes a valid pending search on a fresh page load, no click needed", async () => {
    const sendMessage = vi.fn();
    stubChrome(sendMessage);
    sessionStorage.setItem(
      PENDING_KEY,
      JSON.stringify({ title: "Stashed Product", ts: Date.now() }),
    );

    await import("./content");

    expect(sendMessage).toHaveBeenCalledWith(
      { type: "search", title: "Stashed Product" },
      expect.anything(),
    );
    expect(renderLoading).toHaveBeenCalled();
  });

  it("does not resume an expired pending search", async () => {
    const sendMessage = vi.fn();
    stubChrome(sendMessage);
    sessionStorage.setItem(
      PENDING_KEY,
      JSON.stringify({ title: "Stale Product", ts: Date.now() - 21_000 }),
    );

    await import("./content");

    expect(sendMessage).not.toHaveBeenCalled();
    expect(renderLoading).not.toHaveBeenCalled();
  });

  it("does nothing when there is no pending search (normal-case regression guard)", async () => {
    const sendMessage = vi.fn();
    stubChrome(sendMessage);

    await import("./content");

    expect(sendMessage).not.toHaveBeenCalled();
    expect(renderLoading).not.toHaveBeenCalled();
  });
});

// Each test below imports content.ts fresh, which stacks another pair of
// listeners on window/document alongside any from earlier tests in this
// file (there's no handle to remove the old ones). Harmless for the
// assertions here (presence/absence of a call, not an exact count) since
// every stacked pageshow listener independently checks the same
// event.persisted condition and agrees on the answer.
describe("content.ts bfcache handling", () => {
  it("dismisses the panel when a page is restored from bfcache", async () => {
    stubChrome();
    await import("./content");

    // jsdom may not reliably construct a real PageTransitionEvent, so a
    // plain Event with `persisted` assigned afterward is the safe approach.
    const event = new Event("pageshow");
    Object.defineProperty(event, "persisted", { value: true });
    window.dispatchEvent(event);

    expect(close).toHaveBeenCalled();
  });

  it("does not dismiss the panel on a normal (non-bfcache) page show", async () => {
    stubChrome();
    await import("./content");

    const event = new Event("pageshow");
    Object.defineProperty(event, "persisted", { value: false });
    window.dispatchEvent(event);

    expect(close).not.toHaveBeenCalled();
  });
});

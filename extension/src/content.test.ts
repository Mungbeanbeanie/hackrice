import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./popup", () => ({
  renderLoading: vi.fn(),
  renderError: vi.fn(),
  renderResults: vi.fn(),
}));

import { renderError, renderLoading, renderResults } from "./popup";
// Registers the real capturing click listener once, for the whole file —
// content.ts has no exports and side-effects on import, so a single static
// import (one persistent listener) is used rather than a fresh dynamic
// import per test, which would stack duplicate listeners on `document`.
import "./content";

type SendMessageCallback = (response: unknown) => void;

const EMPTY_GROUPS = { same_spec: [], same_job: [], clears_floor: [] };

let pendingCallbacks: SendMessageCallback[];
let sendMessage: ReturnType<typeof vi.fn>;

function clickAddToCart(): void {
  document
    .querySelector("button")!
    .dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
}

beforeEach(() => {
  document.body.innerHTML = "<button>Add to Cart</button>";
  document.title = "Original Product";
  pendingCallbacks = [];
  sendMessage = vi.fn((_message: unknown, callback: SendMessageCallback) => {
    pendingCallbacks.push(callback);
  });
  vi.stubGlobal("chrome", { runtime: { sendMessage, lastError: undefined } });
  vi.mocked(renderLoading).mockClear();
  vi.mocked(renderError).mockClear();
  vi.mocked(renderResults).mockClear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("content.ts click handler", () => {
  it("ignores a stale response from an earlier click once a newer click has fired", () => {
    clickAddToCart();
    // Simulate an SPA quick-view swap before the first click's response
    // arrives — extraction (falls back to doc.title here) now genuinely
    // differs between the two clicks, not just a duplicate of the same query.
    document.title = "Different Product";
    clickAddToCart();

    expect(sendMessage).toHaveBeenCalledTimes(2);

    // Second (current) click resolves first...
    pendingCallbacks[1]({ ok: true, data: { targetProduct: null, groups: EMPTY_GROUPS } });
    // ...then the first (stale) click's response arrives late and must be ignored.
    pendingCallbacks[0]({ ok: true, data: { targetProduct: null, groups: EMPTY_GROUPS } });

    expect(renderResults).toHaveBeenCalledTimes(1);
  });

  it("shows a timeout error if no response ever arrives", () => {
    vi.useFakeTimers();
    clickAddToCart();
    expect(sendMessage).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(130_000);

    expect(renderError).toHaveBeenCalledWith(expect.stringContaining("timed out"));
  });

  it("does not fire a stale timeout error after a successful response", () => {
    vi.useFakeTimers();
    clickAddToCart();
    pendingCallbacks[0]({ ok: true, data: { targetProduct: null, groups: EMPTY_GROUPS } });

    vi.advanceTimersByTime(130_000);

    expect(renderError).not.toHaveBeenCalled();
  });
});

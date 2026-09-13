import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";

import SearchBar from "@/components/SearchBar";

vi.mock("@/api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/api/client")>()),
  getAutocomplete: vi.fn(),
}));

const { getAutocomplete } = await import("@/api/client");

// SearchBar is controlled — a thin stateful wrapper so typing actually
// updates the `value` prop the way App.tsx/LandingPage.tsx drive it.
function Harness({ onSearch }: { onSearch: (query: string) => void }) {
  const [value, setValue] = useState("");
  return <SearchBar value={value} onChange={setValue} loading={false} onSearch={onSearch} />;
}

// Wrapped in act() because the debounced getAutocomplete().then(...) resolves
// outside any React event handler — without it, the state update from the
// resolved promise applies but React (and Testing Library's queries right
// after) may run before it's flushed.
async function runDebounce(ms = 200) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  vi.mocked(getAutocomplete).mockReset();
  vi.useFakeTimers();
});

// vite.config.ts sets no `globals: true` and no setup file, so Testing
// Library's auto-cleanup never registers and renders stack up across tests
// (same note as PriceHistoryPanel.test.tsx).
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("SearchBar dropdown (additive alongside the ghost suggestion)", () => {
  it("fetches and renders ranked suggestions after the debounce window", async () => {
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Force 1", "Nike Air Max 270"]);
    render(<Harness onSearch={vi.fn()} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "nike" } });

    await runDebounce();

    expect(getAutocomplete).toHaveBeenCalledWith("nike");
    expect(screen.getByText("Nike Air Force 1")).toBeTruthy();
    expect(screen.getByText("Nike Air Max 270")).toBeTruthy();
  });

  it("collapses rapid keystrokes into a single request", async () => {
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Force 1"]);
    render(<Harness onSearch={vi.fn()} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.change(input, { target: { value: "n" } });
    await runDebounce(50);
    fireEvent.change(input, { target: { value: "ni" } });
    await runDebounce(50);
    fireEvent.change(input, { target: { value: "nik" } });
    await runDebounce(200);

    expect(getAutocomplete).toHaveBeenCalledTimes(1);
    expect(getAutocomplete).toHaveBeenCalledWith("nik");
  });

  it("ArrowDown highlights a row and Enter selects it, calling onSearch", async () => {
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Force 1", "Nike Air Max 270"]);
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "nike" } });
    await runDebounce();
    expect(screen.getByText("Nike Air Force 1")).toBeTruthy();

    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSearch).toHaveBeenCalledWith("Nike Air Force 1");
  });

  it("clicking a suggestion fills the input and searches immediately", async () => {
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Force 1"]);
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "nike" } });
    await runDebounce();
    const row = screen.getByText("Nike Air Force 1");

    fireEvent.click(row);

    expect(onSearch).toHaveBeenCalledWith("Nike Air Force 1");
  });

  it("Enter with no row highlighted still falls through to a normal search", async () => {
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Force 1"]);
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "nike" } });
    await runDebounce();
    expect(screen.getByText("Nike Air Force 1")).toBeTruthy();

    fireEvent.submit(input.closest("form")!);

    expect(onSearch).toHaveBeenCalledWith("nike");
  });

  it("the existing ghost suggestion still renders unaffected, alongside the dropdown", async () => {
    // "Nike Air Z" -> "Nike Air Zoom Pegasus" is lib/autocomplete.ts's own
    // curated match — real, not mocked. Regression guard that adding the
    // dropdown didn't touch it.
    vi.mocked(getAutocomplete).mockResolvedValue(["Nike Air Zoom Pegasus"]);
    render(<Harness onSearch={vi.fn()} />);

    const input = screen.getByPlaceholderText(/Paste a link/);
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "Nike Air Z" } });

    expect(screen.getByText("oom Pegasus")).toBeTruthy();

    await runDebounce();
    expect(getAutocomplete).toHaveBeenCalledWith("Nike Air Z");
  });
});

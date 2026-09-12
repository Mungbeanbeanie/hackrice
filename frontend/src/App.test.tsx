import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

test("renders the api status once health resolves", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ status: "ok" })),
  );

  render(<App />);

  await waitFor(() => {
    expect(screen.getByText("api: ok")).toBeDefined();
  });
});

test("shows unreachable when health fails", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("boom"));

  render(<App />);

  await waitFor(() => {
    expect(screen.getByText("api: unreachable")).toBeDefined();
  });
});

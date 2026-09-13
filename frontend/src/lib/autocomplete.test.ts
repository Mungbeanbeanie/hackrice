import { expect, test } from "vitest";

import { getSuggestion } from "./autocomplete";

test("suggests a curated product once the typed prefix matches one", () => {
  expect(getSuggestion("Nike Air Z")).toBe("Nike Air Zoom Pegasus");
});

test("returns null for empty or whitespace-only input", () => {
  expect(getSuggestion("")).toBeNull();
  expect(getSuggestion("   ")).toBeNull();
});

test("returns null when nothing curated matches the prefix", () => {
  expect(getSuggestion("ergonomic pillow")).toBeNull();
});

test("switches to a different product as the input diverges", () => {
  expect(getSuggestion("Nike Air F")).toBe("Nike Air Force 1");
  expect(getSuggestion("Nike Air Z")).toBe("Nike Air Zoom Pegasus");
});

test("matching is case-insensitive", () => {
  expect(getSuggestion("nike air z")).toBe("Nike Air Zoom Pegasus");
});

test("leading whitespace matches nothing rather than misaligning", () => {
  // Regression guard: no curated name starts with a space, so this must
  // stay null — not a suggestion sliced at the wrong offset by SearchBar.
  expect(getSuggestion(" Nike")).toBeNull();
});

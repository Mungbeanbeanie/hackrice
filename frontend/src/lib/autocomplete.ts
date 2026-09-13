import { BRAND_SUGGESTIONS } from "@/data/brandSuggestions";

// The first curated product name (across all brands, in list order) that
// starts with the given input, case-insensitively — the ghost completion
// shown in SearchBar. Re-running this on every keystroke is what makes the
// suggestion narrow or switch products as the input diverges; there's no
// separate "which brand did they mean" step.
//
// Matches against the raw input, not a trimmed copy — SearchBar slices the
// returned suggestion using the raw input's own length to build the ghost
// suffix, so trimming here first would desync that offset whenever the raw
// input has leading whitespace. A leading-space input simply matches nothing
// (no curated name starts with a space), which correctly suppresses the
// suggestion instead of misaligning it.
export function getSuggestion(input: string): string | null {
  if (!input.trim()) return null;
  const lower = input.toLowerCase();
  for (const products of Object.values(BRAND_SUGGESTIONS)) {
    const match = products.find((p) => p.toLowerCase().startsWith(lower));
    if (match) return match;
  }
  return null;
}

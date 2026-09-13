// Cheap, frontend-only autocomplete data for SearchBar's ghost-suggestion
// feature (see src/lib/autocomplete.ts). Starter list — expand this file
// directly, nothing else needs touching. Matching is a case-insensitive
// prefix check against these product name strings; first entry (object key
// order, then array order) whose name starts with what's typed wins — no
// ranking beyond that.
export const BRAND_SUGGESTIONS: Record<string, string[]> = {
  nike: ["Nike Air Zoom Pegasus", "Nike Air Force 1", "Nike Air Max 270"],
  apple: ["Apple iPhone 15 Pro", "Apple MacBook Air", "Apple AirPods Pro"],
  samsung: ["Samsung Galaxy S24", "Samsung Galaxy Buds 2"],
  purple: ["Purple Harmony Pillow", "Purple Hybrid Premier Mattress"],
  sony: ["Sony WH-1000XM5 Headphones", "Sony PlayStation 5"],
  dyson: ["Dyson V15 Detect Vacuum", "Dyson Airwrap Styler"],
};

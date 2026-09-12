## Status: Active — Phase 14, extension/ package (7 files + branchDep.md row)

### extension/manifest.json (new)
- Manifest V3
- `content_scripts`: one entry, `matches: ["<all_urls>"]`, `js: ["content.js"]`, `run_at: "document_idle"`
- `host_permissions`: `["http://localhost:8000/*"]` — dev default only; real deploy IP/domain unknown (no domain yet per deploy/README), NOT fabricated — flag as todo before shipping
- `background.service_worker: "background.js"`
- `icons`: 16/48/128 paths into `extension/icons/` — files don't exist yet (known gap, not fabricated)
- no `webNavigation` permission (click-only detection, decided last turn)

### extension/src/detect.ts (new)
- `TRIGGER_TEXT` regex: `/add to (cart|bag)|buy now|checkout|place order/i`
- `isCheckoutTrigger(target: Element | null): boolean` — walk up to 3 ancestor levels from `target`, test `el.textContent.trim()` (only if `<= 60` chars, avoids matching a whole page's text) against `TRIGGER_TEXT`, return true on first hit
- `extractProduct(doc: Document): {title: string; price: number|null; image: string|null}`:
  - `fromJsonLd(doc)`: query `script[type="application/ld+json"]`, `JSON.parse` each (skip on parse error), find a node where `@type === "Product"` or inside `@graph` array; pull `name`, `offers.price` (or `offers[0].price`), `image` (string or first array element)
  - `fromOpenGraph(doc)`: `meta[property="og:title"]` required or return null; `meta[property="product:price:amount"]`, `meta[property="og:image"]`
  - fallback: `{title: doc.title, price: null, image: null}` — never returns null, mirrors `serpapi_client._parse_price_string`'s always-returns-something pattern
  - order: JSON-LD → OpenGraph → title fallback
  - `parsePrice(value: unknown): number | null` helper — `parseFloat` string or pass-through number, `Number.isFinite` guard
- no `url` param anywhere (no path-based detection per locked decision)

### extension/src/detect.test.ts (new)
- vitest, using `jsdom` (already a frontend devDependency; extension gets its own copy)
- cases: JSON-LD `Product` node → correct title/price/image; `@graph`-wrapped Product → found; JSON-LD present but malformed (invalid JSON) → falls through to OG; OG meta present, no JSON-LD → used; neither present → `doc.title` fallback with null price/image; `isCheckoutTrigger` true on direct match, true on 2-level-up ancestor match, false on unrelated text, false past `MAX_ANCESTOR_DEPTH`

### extension/src/popup.ts (new)
- module-level `host: HTMLDivElement | null`, `shadow: ShadowRoot | null`
- `ensureHost()`: creates fixed-position (`top:16px; right:16px; z-index:2147483647`) host div appended to `document.body`, `attachShadow({mode:"closed"})`, memoized
- inline `<style>` string mirroring `ExtensionPanel.tsx`'s visual structure (brand line, "You could keep $X" block, equivalents list, close + "Open full comparison" buttons) — plain CSS, no Tailwind/CSS-var dependency on host page
- `renderLoading()`, `renderError(message: string)`, `renderResults(state: {targetPrice: number|null; products: PopupProduct[]}, onOpenComparison: () => void)` — `renderResults` computes `best = products[0] ?? null`, `savings = best && targetPrice != null ? targetPrice - best.price : null`, renders up to 4 products
- `close()`: removes host, resets both module vars to null
- every render wires the close button's click to `close()`; `renderResults` also wires "Open full comparison" to the passed callback

### extension/src/content.ts (new)
- `WEBAPP_URL = "http://localhost:5173"` — dev default (Vite's own port), deploy URL unknown, same flag as manifest's host_permissions
- one `document.addEventListener("click", handler, true)` — capture phase, so a page's `stopPropagation` on the button doesn't hide the click from us
- handler: `isCheckoutTrigger(event.target)` guard → `extractProduct(document)` → guard on empty title → `renderLoading()` → `chrome.runtime.sendMessage({type:"search", title}, callback)`
- callback: `chrome.runtime.lastError` or `!response.ok` → `renderError(...)`; else `renderResults({targetPrice: response.data.targetProduct?.price ?? null, products: flattened same_spec+same_job+clears_floor}, () => window.open(\`${WEBAPP_URL}/?q=${encodeURIComponent(title)}\`, "_blank"))`

### extension/src/background.ts (new)
- `API_BASE_URL = "http://localhost:8000"` — dev default, same flag as above
- `chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {...})`
- ignore messages where `message.type !== "search"` (return false/undefined)
- on `"search"`: `fetch(\`${API_BASE_URL}/api/search\`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({query: message.title})})`
- `.then` non-ok status → throw; else `sendResponse({ok:true, data: await res.json()})`
- `.catch` → `sendResponse({ok:false, error: String(err)})`
- `return true` — keeps the message channel open for the async `sendResponse`

### extension/package.json (new) + extension/tsconfig.json (new, companion — not on original checklist, needed for `typecheck` script to run at all)
- package.json: `esbuild` (bundles `content.ts`+`background.ts` → plain JS IIFE, no framework), `typescript`, `vitest` as devDependencies; scripts `build` (esbuild bundle), `test` (vitest run --passWithNoTests), `typecheck` (tsc --noEmit)
- tsconfig.json: `target: "ES2020"`, `lib: ["ES2020", "DOM"]`, `module: "ESNext"`, `moduleResolution: "bundler"`, `strict: true`, `types: ["chrome"]` — needs `@types/chrome` as a 4th devDependency for `chrome.*` APIs to typecheck
- NEW dependency-rule question: `extension/package.json` isn't named in `instructions.md`'s Dependency Rule (only backend/frontend files are). Adding a `branchDep.md` row for these anyway (spirit of the rule), and asking user whether to formally extend the rule's file list in `instructions.md` — not editing that file without approval.

### .claude/branchDep.md (edit, same stage)
- new row: `extension/package.json` | `+ esbuild, typescript, vitest, @types/chrome (new file/package)` | `Phase 14 browser extension — build/typecheck/test tooling for the new extension/ package`

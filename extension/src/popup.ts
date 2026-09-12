export interface PopupProduct {
  short: string;
  price: number;
  matchScore: number;
  rating: number;
  image: string;
}

export interface PopupState {
  targetPrice: number | null;
  products: PopupProduct[];
}

// Mirrors frontend/src/components/ExtensionPanel.tsx's structure, hand-written
// rather than a React port — bundling React into a content script injected on
// arbitrary third-party pages is real bundle-size/CSP/perf cost for this scope.
const STYLES = `
  :host { all: initial; }
  .panel {
    position: fixed; top: 16px; right: 16px; z-index: 2147483647;
    width: 320px; max-width: calc(100vw - 32px);
    font-family: system-ui, sans-serif; font-size: 13px; color: #2b2b28;
    background: #f7f5f1; border: 1px solid #ddd8cf; border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18); padding: 16px;
  }
  .header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
  .brand { font-weight: 700; color: #a15c2f; margin-right: auto; }
  .close { border: none; background: transparent; cursor: pointer; font-size: 16px; line-height: 1; color: #6b6b63; }
  .savings { background: #eef3e6; border: 1px solid #cdddb8; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
  .savings-label { text-transform: uppercase; font-size: 10px; letter-spacing: 0.08em; color: #4c6b2f; margin: 0 0 4px; }
  .savings-amount { font-size: 32px; font-weight: 700; color: #4c6b2f; margin: 0; line-height: 1; }
  .list-label { text-transform: uppercase; font-size: 10px; letter-spacing: 0.08em; color: #6b6b63; margin: 12px 0 8px; font-weight: 700; }
  .item { display: flex; align-items: center; gap: 10px; border: 1px solid #ddd8cf; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
  .item img { width: 32px; height: 32px; object-fit: contain; border-radius: 4px; flex-shrink: 0; }
  .item-title { font-weight: 700; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .item-meta { color: #6b6b63; font-size: 11px; margin: 2px 0 0; }
  .item-price { margin-left: auto; font-weight: 700; flex-shrink: 0; }
  .open-comparison { width: 100%; border: none; border-radius: 999px; background: #a15c2f; color: #fff; padding: 10px; font-weight: 700; cursor: pointer; margin-top: 8px; }
  .status { padding: 24px 4px; text-align: center; color: #6b6b63; }
`;

let host: HTMLDivElement | null = null;
let shadow: ShadowRoot | null = null;

// p.short/message ultimately come from the backend's SerpAPI-sourced product
// data — untrusted text rendered via innerHTML. Escape it, same practice as
// backend/app/routes/admin.py's _cell for the same reason (stored-XSS risk).
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function ensureHost(): ShadowRoot {
  if (shadow) return shadow;
  host = document.createElement("div");
  document.body.appendChild(host);
  shadow = host.attachShadow({ mode: "closed" });
  return shadow;
}

function wireClose(root: ShadowRoot): void {
  root.querySelector(".close")?.addEventListener("click", close);
}

export function renderLoading(): void {
  const root = ensureHost();
  root.innerHTML = `
    <style>${STYLES}</style>
    <div class="panel">
      <div class="header"><span class="brand">nectarly</span><button class="close">&times;</button></div>
      <div class="status">Searching for equivalents…</div>
    </div>
  `;
  wireClose(root);
}

export function renderError(message: string): void {
  const root = ensureHost();
  root.innerHTML = `
    <style>${STYLES}</style>
    <div class="panel">
      <div class="header"><span class="brand">nectarly</span><button class="close">&times;</button></div>
      <div class="status">${escapeHtml(message)}</div>
    </div>
  `;
  wireClose(root);
}

export function renderResults(state: PopupState, onOpenComparison: () => void): void {
  const root = ensureHost();
  const best = state.products[0] ?? null;
  const savings = best && state.targetPrice != null ? state.targetPrice - best.price : null;

  const savingsBlock =
    best && savings != null && savings > 0
      ? `<div class="savings">
           <p class="savings-label">You could keep</p>
           <p class="savings-amount">$${savings.toFixed(0)}</p>
         </div>`
      : "";

  const items = state.products
    .slice(0, 4)
    .map(
      (p) => `
        <div class="item">
          ${p.image && /^https?:\/\//.test(p.image) ? `<img src="${escapeHtml(p.image)}" alt="">` : ""}
          <div>
            <p class="item-title">${escapeHtml(p.short)}</p>
            <p class="item-meta">${Math.round(p.matchScore)}% match · ${p.rating.toFixed(1)}★</p>
          </div>
          <span class="item-price">$${p.price.toFixed(0)}</span>
        </div>`,
    )
    .join("");

  root.innerHTML = `
    <style>${STYLES}</style>
    <div class="panel">
      <div class="header"><span class="brand">nectarly</span><button class="close">&times;</button></div>
      ${savingsBlock}
      <p class="list-label">Equivalents found</p>
      ${items || `<div class="status">No equivalents found.</div>`}
      <button class="open-comparison">Open full comparison</button>
    </div>
  `;
  wireClose(root);
  root.querySelector(".open-comparison")?.addEventListener("click", onOpenComparison);
}

export function close(): void {
  host?.remove();
  host = null;
  shadow = null;
}

# Handoff: Nectarly production UI

## Overview

A production-grade redesign of the nectarly web app — the tool that takes a product
you're about to buy and finds functional equivalents at a lower price. It replaces the
honey-gradient placeholder UI currently in `frontend/src/` with the **Organic** design
system (cream ground, terracotta + sage accents, Caprasimo over Figtree), and covers
five surfaces instead of one: marketing landing, search + results, spec comparison,
sign-in, and the browser-extension panel.

Two product changes are baked into this design and are **not** purely cosmetic — read
"Data contract changes" before you start:

1. **Tier 1/2/3 should still be present, with the reasoning for ranking (only reason is included in this design)
2. **The scoring math is no longer displayed.** No `cos θ`, no Bayesian `Q`, no value
   multiplier `V`. Only plain comparison numbers reach the UI.

## About the design files

The files in this bundle are **design references authored as HTML** — streaming
prototypes that show intended look and behaviour. They are **not production code to
copy**. Your job is to recreate them in the existing `frontend/` environment (React 19 +
Vite + TypeScript + Tailwind v4) using its established patterns.

Concretely: the prototypes use inline `style` objects because the authoring environment
requires it. **Do not port inline styles.** Convert them to Tailwind utilities and the
`@theme` tokens below, matching your current codebase convention in
`frontend/src/components/`.

| File | What it is |
| --- | --- |
| `Nectarly.dc.html` | The new design. All five surfaces + all states. |
| `Nectarly Current.dc.html` | Faithful recreation of the **existing** UI, for diffing. |
| `HoneyDrop.dc.html` | The mascot, extracted. Your `HoneyDrop.tsx` already matches — **do not change it**. |

Open them in a browser directly. Bottom-right of `Nectarly.dc.html` is a prototype-only
nav (Landing · Empty · Results · Error · Sign in · Extension) — **do not build that**;
it exists so a reviewer can reach every state.

## Fidelity

**High-fidelity.** Final colors, type, spacing and interaction states. Every value below
is exact and traceable to the Organic token sheet. Recreate pixel-perfectly using
Tailwind utilities bound to the tokens — do not re-derive spacing or colors by eye.

The only placeholders are **imagery**: every product shot is a striped
`repeating-linear-gradient` box. Those need real retailer images (see "Assets").

---

## Design tokens

Source of truth: `_ds/organic-deea9dec-e635-4437-babb-25fbd97592a0/styles.css`.
Drop this into `frontend/src/index.css`, replacing the current honey `@theme inline`
block. Tailwind v4 generates utilities from it (`bg-bg`, `text-accent-700`, `p-4`, …).

```css
@import url('https://fonts.googleapis.com/css2?family=Caprasimo:wght@400&family=Figtree:wght@400;600;700&display=swap');
@import 'tailwindcss';

@theme inline {
  /* roles */
  --color-bg: #f5ead8;
  --color-surface: #ebddc5;
  --color-text: #201e1d;
  --color-accent: #c67139;
  --color-accent-2: #7a8a5e;
  --color-divider: rgba(32, 30, 29, 0.16);

  /* neutral ramp */
  --color-neutral-100: #f9f4ed;  --color-neutral-200: #eee7db;
  --color-neutral-300: #dcd3c4;  --color-neutral-400: #c0b6a5;
  --color-neutral-500: #a19786;  --color-neutral-600: #82796a;
  --color-neutral-700: #645c50;  --color-neutral-800: #474238;
  --color-neutral-900: #2e2b25;

  /* terracotta ramp */
  --color-accent-100: #fff2eb;   --color-accent-200: #ffe1d0;
  --color-accent-300: #ffc6a5;   --color-accent-400: #f6a06b;
  --color-accent-500: #d67f48;   --color-accent-600: #b2622d;
  --color-accent-700: #8c491a;   --color-accent-800: #643312;
  --color-accent-900: #402310;

  /* sage ramp */
  --color-accent-2-100: #f0fae1; --color-accent-2-200: #e1eecc;
  --color-accent-2-300: #ccdbb2; --color-accent-2-400: #aebf92;
  --color-accent-2-500: #8fa073; --color-accent-2-600: #728157;
  --color-accent-2-700: #56633f; --color-accent-2-800: #3d472b;
  --color-accent-2-900: #272e1b;

  /* type */
  --font-heading: "Caprasimo", system-ui, sans-serif;
  --font-body: "Figtree", system-ui, sans-serif;

  /* 1.10x density scale — use these, never raw px */
  --space-1: 4.4px;  --space-2: 8.8px;  --space-3: 13.2px;
  --space-4: 17.6px; --space-6: 26.4px; --space-8: 35.2px;

  --radius-sm: 8px; --radius-md: 16px; --radius-lg: 28px;

  --shadow-sm: 0 1px 2px rgba(46, 43, 37, 0.14);
  --shadow-md: 0 3px 10px rgba(46, 43, 37, 0.16);
  --shadow-lg: 0 12px 32px rgba(46, 43, 37, 0.22);
}

body {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: 400;
  letter-spacing: -0.015em;
}
:focus { outline: none; }
:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
::selection { background: var(--color-accent-200); }
input::placeholder { color: var(--color-neutral-600); }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--color-neutral-300); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-neutral-400); }
```

### Colour rules (from the Organic guide — these are binding)

- The accent-to-ground pair is tuned to **3:1** — enough for icons, large text and
  chrome, **not body copy**. For paragraph-size text in the accent use
  `--color-accent-700`, never `--color-accent`.
- Muted body text uses **ramp steps, not opacity**: `--color-neutral-800` for secondary
  paragraphs, `--color-neutral-700` for meta and kickers. Do not reintroduce
  `color-mix()` or alpha-faded ink — several of these were contrast failures at
  `neutral-600` and were deliberately moved to `700`.
- Sage (`--color-accent-2-*`) is the **savings / positive** voice. It replaces the
  generic `text-green-600` in the current build.
- Elevation is `--shadow-sm/md/lg` only. No ad-hoc box-shadows. The old
  `.tier-N-glow` ring shadows are deleted.

### Keyframes

```css
@keyframes riseIn   { from { opacity: 0; transform: translateY(14px) } to { opacity: 1; transform: none } }
@keyframes softIn   { from { opacity: 0 } to { opacity: 1 } }
@keyframes bob      { 0%, 100% { transform: translateY(0) } 50% { transform: translateY(-7px) } }
@keyframes sweep    { 0% { background-position: -200% 0 } 100% { background-position: 200% 0 } }

/* Loading mascot. MUST run on `linear` — the uneven keyframe spacing IS the easing.
   Angular velocity ramps 10deg/8% -> ~4.7deg/% mid-flight -> 10deg/8%, i.e. accelerate
   then decelerate. A timing function here fights the curve and flattens it. */
@keyframes hopSpin {
  0%   { transform: translateY(0)     rotate(0deg)   scale(1, 1) }
  8%   { transform: translateY(-10px) rotate(10deg)  scale(0.94, 1.07) }
  20%  { transform: translateY(-22px) rotate(45deg)  scale(1, 1) }
  35%  { transform: translateY(-29px) rotate(110deg) }
  50%  { transform: translateY(-31px) rotate(180deg) }
  65%  { transform: translateY(-29px) rotate(250deg) }
  80%  { transform: translateY(-22px) rotate(315deg) scale(1, 1) }
  92%  { transform: translateY(-10px) rotate(350deg) scale(1.06, 0.93) }
  100% { transform: translateY(0)     rotate(360deg) scale(1, 1) }
}
@keyframes hopShadow {
  0%, 100% { transform: scaleX(1);    opacity: 0.22 }
  50%      { transform: scaleX(0.55); opacity: 0.07 }
}
```

Delete from `index.css`: `--color-honey-*`, `--color-nectar`, `--color-pollen`,
`--color-hive`, `--color-wax`, `.glass-card`, `.honey-shadow`, `.honey-shadow-lg`,
`.tier-1-glow`, `.tier-2-glow`, `.tier-3-glow`, `.skeleton`, `@keyframes fadeInUp`,
`fadeIn`, `dropBounce`, `shimmer`, `spin`, and the Outfit + JetBrains Mono imports.

### Type scale as used

| Role | Font | Size | Line-height | Weight |
| --- | --- | --- | --- | --- |
| Landing h1 | Caprasimo | `clamp(36px, 4.6vw, 62px)` | 1.05 | 400 (`ls -0.02em`) |
| Section h2 | Caprasimo | `clamp(28px, 3.6vw, 40px)` | 1.1 | 400 |
| Results h2 | Caprasimo | `clamp(22px, 2.4vw, 27px)` | 1.15 | 400 |
| Card h3 (landing step) | Caprasimo | 21px | 1.2 | 400 |
| Group title h3 | Caprasimo | 17px | 1.25 | 400 |
| Product name | Figtree | 15.5px | 1.3 | 700 |
| Body | Figtree | 15px | 1.55 | 400 |
| Hero sub | Figtree | `clamp(16px, 1.6vw, 19px)` | 1.55 | 400 |
| Meta / secondary | Figtree | 13–13.5px | 1.4 | 400 |
| Kicker | Figtree | 11px | — | 700, `ls 0.08em`, uppercase |
| Chip value / label | Figtree | 13px / 11.5px | — | 700 / 400 |
| Price — result card | Caprasimo | 25px | 1 | 400 |
| Price — target card | Caprasimo | 28px | 1 | 400 |
| Savings hero | Caprasimo | `clamp(36px, 4vw, 44px)` | 1 | 400 |
| Extension savings | Caprasimo | 40px | 1 | 400 |
| Buttons | Caprasimo | 13.5–15px | 1.2 | 400 |

Note buttons and prices use the **display** face. That is intentional and is a large part
of the character — do not swap them to Figtree.

---

## Data contract changes

These require backend work. `frontend/src/api/client.ts` and
`backend/app/models.py` both change.

### 1. `tiers` → `groups`

The response currently returns `tiers: { tier1, tier2, tier3 }`. The UI must keep these tiers. Add three semantic groups:

| id | UI title | Meaning (was) |
| --- | --- | --- |
| `same_spec` | Same spec, no logo | Tier 1 — direct factory/generic equivalent |
| `same_job` | Different build, same job | Tier 2 — cross-category functional alternative |
| `clears_floor` | Cheapest that clears quality | Tier 3 — budget benchmark above the Q floor |

Group descriptions rendered in the UI (exact copy):

- **Same spec, no logo** — "Matches the original's materials and construction. Different label, different price."
- **Different build, same job** — "Another way of reaching the same outcome — worth it when the alternative route is better."
- **Cheapest that clears quality** — "Lowest price still above the quality floor. Spec match drops; we say so rather than hide it."

Ordering rule the design depends on: **groups are ordered by equivalence, and products
are ranked by value *within* a group.** This is why the $22 two-pack — which has the
highest raw `V` — sits in the third group rather than at the top. If you rank globally by
`V`, the design's story breaks.

Since this implementation is not the original design, ask questions as necessary. Do not make assumptions

### 2. Per-spec verdicts

`SpecAttribute` needs a verdict so the comparison overlay can label each row. Six values,
each with a fixed chip style:

| verdict | Chip label | Background | Text |
| --- | --- | --- | --- |
| `same` | Same | `--color-accent-2-100` | `--color-accent-2-700` |
| `better` | Better | `--color-accent-2-200` | `--color-accent-2-800` |
| `equivalent` | Equivalent | `--color-accent-2-100` | `--color-accent-2-700` |
| `close` | Close | `--color-surface` | `--color-neutral-700` |
| `different` | Different | `--color-accent-100` | `--color-accent-800` |
| `lower` | Lower | `--color-accent-200` | `--color-accent-800` |

Chip: `3px var(--space-2)` padding, `999px` radius, 11.5px / 700.

The current `SpecBreakdownModal.tsx` has dead logic for this — `buildSpecComparison`
computes `winner` but every branch returns `"tie"`, and `winnerColors.target` /
`.alternative` are never reachable. Delete it and drive the chip off the API verdict.

### 3. New fields

```ts
export interface Product {
  id: string;
  name: string;
  short: string;          // NEW — 2-3 words, for the side-by-side table header
  brand: string;
  price: number;
  originalPrice?: number;
  image: string;
  retailer: string;
  url: string;
  rating: number;
  reviewCount: number;
  specs: ProductSpec[];   // ProductSpec gains `verdict`
  matchScore: number;
  savings?: number;
  group: 'same_spec' | 'same_job' | 'clears_floor';   // replaces `tier: 1 | 2 | 3`
  rationale: string;      // NEW — 1-2 sentences, shown in the comparison overlay
}

export interface ProductSpec {
  key: string;
  value: string;
  verdict: 'same' | 'better' | 'equivalent' | 'close' | 'different' | 'lower';
}

export interface SearchResponse {
  query: string;
  targetProduct: Product | null;
  groups: Record<'same_spec' | 'same_job' | 'clears_floor', Product[]>;
}
```

### 4. Fields to stop sending to the client

`value` / `V` and the Bayesian `Q` are no longer displayed. Keep computing them —
they drive ordering and the quality floor — but the UI reads only `rating`,
`reviewCount` and `matchScore`. `rationale` is the human-readable stand-in for the
explanation the formulas used to carry.

---

## Screens / views

### 1. Landing (`LandingPage.tsx` — new)

**Purpose:** explain the thesis and get a query typed. Judges land here.

**Layout** — max-width `1160px`, centred, horizontal padding `clamp(20px, 4vw, 48px)`.

- **Header** — sticky, `z-20`, `var(--color-bg)` with `backdrop-filter: blur(14px)`,
  `border-bottom: 1px solid var(--color-divider)`. Padding `14px clamp(20px, 4vw, 48px)`.
  Left: mascot 30×35 with `bob 3.4s ease-in-out infinite` + "nectarly" in Caprasimo 23px
  `--color-accent-700`. Right: "How it works" / "Extension" text links (pill hover,
  `--color-neutral-200`), then a "Sign in" outlined pill.

- **Hero** — `display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
  gap: clamp(36px, 5vw, 64px); align-items: start`. Padding
  `clamp(40px, 7vw, 88px) … clamp(32px, 5vw, 64px)`.
  Collapses to one column below ~944px. **`align-items: start`, not `center`** — the two
  halves are meant to read as one horizontal band.

  - *Left:* sage kicker pill "Not another coupon extension" (Lucide `check` 13px,
    `--color-accent-2-100` on `--color-accent-2-200` border, text `--color-accent-2-700`);
    h1 "Pay for the product,&lt;br&gt;not the brand."; sub paragraph (`max-width: 30em`,
    `--color-neutral-800`); the search pill; then a "Try" row of three example chips.
  - *Right:* the before/after card stack, `padding-top: 48.5px` so the first card's top
    sits level with the h1 — this offset clears the kicker pill and is deliberate.
    Two decorative circles behind it: a `min(400px, 92%)` square-aspect
    `--color-accent-200` circle centred via `top/left 50% + translate(-50%,-50%)`, and a
    120px `--color-accent-2-200` circle at `top 4% / right 6%`.

  **Card stack** (`max-width: 392px`, gap `var(--space-3)`):
  1. "What you were buying" — `--color-neutral-100`, `--radius-lg`, `--shadow-md`,
     `rotate(-1.4deg)`. Kicker, 52px thumb, name + specs, price `$159` Caprasimo 24px.
  2. Connector row — Lucide `arrow-down` in `--color-accent`, "96% spec match found"
     13px/700 `--color-accent-700`, indented `22px`.
  3. "What you'll buy instead" — `--color-accent-2-100` on `--color-accent-2-300`,
     `--shadow-lg`, `rotate(1.1deg)`. Same anatomy, sage text, then a divider and
     "You keep" / **$117.00** at Caprasimo 27px.

- **"Three things every other shopping tool skips."** — h2, a sub paragraph, then
  `grid; repeat(auto-fit, minmax(280px, 1fr)); gap: clamp(16px, 2vw, 26px)`. Each card:
  `--color-neutral-100`, `--radius-lg`, `padding: clamp(20px, 2.4vw, 28px)`, a 38px
  `--color-accent-200` numbered circle, h3, body.

  Exact copy — **do not reintroduce the formula line that used to sit under each**:
  1. *Match on specs, not names* — "Two products doing the same job rarely list the same attributes. We line them up spec by spec so they can be compared at all."
  2. *Filter out the junk* — "A 5.0 from two reviews is not a 5.0. Ratings only count once there are enough of them to mean something."
  3. *Rank by value, not discount* — "What you get weighed against what you pay. The cheapest thing rarely wins. The overpriced brand never does."

- **"It comes with you."** — two-column `minmax(300px, 1fr)`. Left: h2, paragraph, three
  Lucide-`check` bullets, a primary "See the panel" pill. Right: a miniature browser
  frame containing the extension panel (see surface 5).

- **Footer** — `border-top: 1px solid var(--color-divider)`, mascot 20×23, wordmark,
  "find sweeter deals", and the existing Google-Form feedback link pushed right. Keep
  the `FEEDBACK_FORM_URL` constant and its comment from `App.tsx` as-is.

### 2. Search + results (`App.tsx` + components)

**App header** — max-width `1240px`, padding `12px clamp(16px, 3vw, 36px)`. Mascot 24×28
+ wordmark (click → landing), the search pill `flex: 1 1 280px`, then a "Sign in" pill
with a 26px `--color-accent-200` avatar circle (Lucide `user` 14px).

**Body** — max-width `1240px`, padding `clamp(20px, 3vw, 36px) clamp(16px, 3vw, 36px) 80px`.
Two columns: `display: flex; flex-wrap: wrap; gap: clamp(20px, 2.6vw, 34px);
align-items: flex-start`. Results `flex: 1 1 460px`; sidebar `flex: 1 1 285px;
max-width: 360px; position: sticky; top: 88px` (clears the 71px sticky header).

**Reference product card** (`TargetProductCard.tsx`, rewritten) — `--color-neutral-100`,
`--radius-lg`, `padding: clamp(16px, 2vw, 22px)`, flex row, wraps. 62px `--radius-md`
thumb. Kicker "Your reference product". h2 Caprasimo 20px. Meta line
`brand · retailer · 4.5★ (1,243)` at 13.5px `--color-neutral-700`. Right: price Caprasimo
28px, struck-through original 13px **`--color-neutral-700`** (not `600` — contrast).

**Results header** — h2 "{n} alternatives worth your attention" + a segmented
Ranked / Side-by-side toggle on the right (`--color-surface` track, 3px padding,
`999px`; active = `--color-neutral-100` + `--shadow-sm`).

**Ranked view** (`AlternativeGroups.tsx`, replacing `AlternativeTierList.tsx`) — groups
stacked with `gap: 30px`. Group header: 9px `--color-accent` dot, h3 title, a count pill
(`--color-surface`), then the description indented `18px` at 13.5px.

**Result card** (`ResultCard.tsx` — new) — `--color-neutral-100`, `1px
var(--color-divider)`, `--radius-lg`, `padding: clamp(14px, 1.8vw, 20px)`, `--shadow-sm`.
Hover: `--shadow-md` + `translateY(-2px)`, `transition: box-shadow .18s ease, transform .18s ease`.

Row: 68px thumb; then a column containing
1. name (15.5px/700) + meta, and right-aligned price (Caprasimo 25px) with
   "saves $117.00" beneath at 13px/700 `--color-accent-2-700`;
2. **the savings bar** — 9px-tall `999px` track in `--color-accent-2-200`; the filled
   portion is `--color-accent` at `width: price / targetPrice`; label to its right reads
   "26% of original" at 12px/700. The sage remainder is the saving. This is the primary
   savings visualisation — keep it;
3. a chip row: `96%` + "match" (`--color-accent-100` on `--color-accent-200`),
   `4.4` + "8,912 reviews" (`--color-surface`), then right-aligned "Compare" (outlined)
   and "Buy" (solid accent, Lucide `external-link` 13px) pills.

**Side-by-side view** (`ComparisonTable.tsx` — new) — one card wrapper, `overflow: hidden`,
inner `overflow-x: auto`, table `min-width: 660px`. Header row `--color-surface`: first
cell "Spec" (150px, 11px kicker), then one column per product with `short` name, price
(Caprasimo 20px) and `−$117.00` in sage. Body rows are the six spec keys plus two
appended rows, "Spec match" and "Rating". Rows separated by
`border-top: 1px solid var(--color-divider)`; columns by `border-left`.

**Sidebar**
- *Best equivalent* card — `--color-accent-2-100` on `--color-accent-2-300`,
  `--radius-lg`, `padding: var(--space-6)`. Kicker, then the savings figure at
  `clamp(36px, 4vw, 44px)` Caprasimo, "kept, at 96% of the product you asked for", a
  divider, then the winning product's name and `brand · retailer · 4.4★ (8,912)`.
- **The "How this ranked" explainer panel was removed.** Do not build it.

### 3. Comparison overlay (`SpecBreakdownModal.tsx`, rewritten)

Backdrop `rgba(46, 43, 37, 0.55)` + `blur(5px)`, `z-60`, closes on backdrop click and on
`Escape` (keep the existing `useEffect` keydown listener). Dialog `--color-bg`,
`--radius-lg`, `--shadow-lg`, `max-width: 760px`, `max-height: 88vh`, column flex.

1. **Header** — kicker "Spec by spec", h2 product name (`clamp(21px, 2.4vw, 26px)`),
   36px circular close button (`--color-surface`, hover `--color-neutral-300`).
2. **Price band** — `grid; repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-3)`.
   Three tiles: "Original" (`--color-surface`), "This one" and "You keep" (both
   `--color-accent-2-100` on `--color-accent-2-300`). Figures Caprasimo 26px; the third
   adds "74% less" beneath.
3. **Body** — the `rationale` paragraph at 14px `--color-neutral-800`, then one row per
   spec: label (118px, 12.5px/700), original value (`--color-neutral-700`), a Lucide
   `arrow-right` in `--color-neutral-400`, the alternative value (14px/600), and the
   verdict chip. `border-top` per row.
4. **Footer** — "96% spec match · 4.4★ from 8,912 reviews" left, "Buy this instead"
   accent pill right.

### 4. Sign-in (`SignInPage.tsx` — new)

`min-height: 100vh`, `grid; repeat(auto-fit, minmax(320px, 1fr))`.

*Left* (`padding: clamp(32px, 6vw, 72px)`, inner `max-width: 380px`): mascot + wordmark
button → landing; h1 "Keep what you found." (`clamp(30px, 3.6vw, 38px)`); paragraph;
an email field (label 12.5px `--color-neutral-700`, input `999px` radius,
`--color-neutral-100`, `13px 18px`); a full-width accent pill "Email me a sign-in link";
the reassurance line "No password. We send a link that signs you in for 30 days."; an
"or" divider; an outlined "Continue without an account".

This matches the magic-link decision in `.claude/overview.md` §6.1 — no password field,
so no hashing or reset flow.

*Right* (`--color-surface`, `overflow: hidden`): a 430px `--color-accent-200` circle at
`top -90px / right -120px`, a 220px `--color-accent-2-200` circle at
`bottom -60px / left -50px`, and a blockquote in Caprasimo `clamp(24px, 2.8vw, 31px)`.

> ⚠️ The pull-quote and the "Saved $412 across 4 searches — average nectarly user, first
> month" line are **invented placeholder copy**. Replace with something real or cut it
> before anyone sees this publicly.

### 5. Extension panel (`ExtensionPanel.tsx` — new)

Shown standalone on a mock retailer page, and again shrunk inside the landing page.
Panel is `386px` wide, `--color-neutral-100`, `--radius-lg`, `--shadow-lg`,
`padding: var(--space-4)`, entering with `riseIn 0.5s ease both`.

Mascot 22×26 (bobbing) + wordmark + a 28px circular close. Then a sage
`--radius-md` block: kicker "You could keep", **$117** at Caprasimo 40px, and "on a 96%
spec match, rated 4.4 across 8,912 reviews". Then kicker "Equivalents found" and four
compact rows (36px thumb, `short` name, "96% match · 4.4★", price Caprasimo 17px). Then a
full-width accent pill "Open full comparison".

The surrounding page mock (browser chrome, greyed 50%-opacity retailer content) is
**prototype scaffolding** — build only the panel.

### 6. Empty / loading / error

All three live inside the results area.

**Empty** — centred, `max-width: 620px`. Mascot 76×88 bobbing; h2 "Show us what you were
about to buy." (`clamp(26px, 3.4vw, 34px)`); paragraph "A link, a product name, or a
plain description of the job it has to do. All three work — we figure out which one you
gave us."; then three mode cards (`minmax(170px, 1fr)`): *Paste a link* / "Any retailer
product page", *Name a product* / "Brand and model, as you'd say it", *Describe the job* /
"No target — we rank against the description".

**Loading** — the spinner ring is **replaced** by the mascot animation. A 92px-tall
column, content bottom-aligned: a 46×54 mascot with
`animation: hopSpin 1.15s linear infinite; transform-origin: 50% 50%`, and beneath it a
34×5 `999px` contact shadow in `--color-accent-800` running
`hopShadow 1.15s linear infinite`. Label below at 14.5px/600 `--color-accent-700`.
Then three 104px skeleton bars, `--radius-lg`, at opacity 1 / .75 / .5 with
`sweep 1.5s ease infinite` staggered 0 / .15s / .3s, gradient
`--color-neutral-200 → --color-neutral-100 → --color-neutral-200` at
`background-size: 200% 100%`.

**Error** — centred card `max-width: 520px`, `--color-neutral-100`, `--radius-lg`,
`padding: 36px`. A 46px `--color-accent-200` circle with Lucide `alert-circle` 22px;
h2 "We couldn't reach the catalogue."; "Nothing's wrong with your search — the product
feed timed out. Try again in a moment."; the raw error in monospace 12.5px
`--color-neutral-600`; a "Try again" accent pill that re-runs the search.

---

## Interactions & behaviour

### Navigation

| From | Trigger | To |
| --- | --- | --- |
| Landing | submit search / example chip | Results (via loading) |
| Landing | "Sign in" | Sign-in |
| Landing | "See the panel" | Extension |
| App header | wordmark | Landing |
| Sign-in | either button | Results |
| Extension | "Open full comparison" | Results |
| Result card | "Compare" | Comparison overlay |

Currently a single `screen` state variable. If you'd rather have real URLs, this maps
cleanly onto routes — `/`, `/search`, `/signin` — and the extension panel is not a route
at all in production.

### Search pill

One input for all three modes; the backend infers url / exact_product / description, so
**any non-empty string is valid** and no mode selector exists. Keep that.

Geometry (this was tuned — the numbers matter):
`display: flex; align-items: center; gap: var(--space-3);
padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
border-radius: 999px; background: var(--color-neutral-100);
border: 1px solid var(--color-divider); box-shadow: var(--shadow-md)`.

- **No `flex-wrap`.** It's a single-line control; wrapping drops the button onto a second
  line and the pill visibly breaks.
- Input is `flex: 1 1 0%; min-width: 0; text-overflow: ellipsis` so it *shrinks* instead
  of pushing the button out.
- Button `padding: var(--space-3) var(--space-4)`, `font-size: 14.5px`, `line-height: 1.2`,
  `flex-shrink: 0`, `white-space: nowrap`. This yields an even `9.8px` ring on the
  button's top, right and bottom.
- Lucide `search` 19px in `--color-accent`, `flex-shrink: 0`.

### State machine

```ts
type Screen   = 'landing' | 'app' | 'signin' | 'extension';
type AppState = 'idle' | 'loading' | 'results' | 'error';
type View     = 'ranked' | 'table';
```

```
submit('')            -> app / idle      // nothing to resolve a target from
submit(q)             -> app / loading -> results
                                       -> error   (on API failure)
retry()               -> re-run submit(q)
compare(id)           -> overlay open; Escape or backdrop closes
```

In the prototype, a query containing `fail` or `timeout` forces the error branch — that's
a **demo affordance**, not product behaviour. Drop it and wire the real `catch` in
`searchProducts()`; the existing `apiFetch` already throws `API {status}: {text}`, which
is what the monospace line renders.

Also: clear the open comparison when the screen changes, or the overlay survives
navigation. That was a real bug in the prototype.

### Hover / focus states

Every interactive element needs a themed hover and a pressed state one ramp step past
the base, per the Organic guide. Do not leave browser defaults.

| Element | Hover | Active |
| --- | --- | --- |
| Primary pill | `--color-accent-600` | `--color-accent-700` |
| Outlined / ghost pill | `--color-neutral-200` | `--color-neutral-300` |
| Example chip | `--color-accent-100`, border `--color-accent-300` | — |
| Result card | `--shadow-md` + `translateY(-2px)` | — |
| Close button | `--color-neutral-300` | — |

Focus is global: `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px }`.

### Responsive

Responsive at every width — there are **no media queries**. Reflow comes from
`clamp()` type, `flex-wrap`, and `repeat(auto-fit, minmax(Npx, 1fr))`. Breakpoints
emerge from the `minmax` floors:

| Region | Collapses below |
| --- | --- |
| Hero | ~944px (`minmax(440px, 1fr)` + 64px gap) |
| Results / sidebar | ~800px (`flex: 1 1 460px` + `1 1 285px`) |
| Explainer cards | ~600px (3-up → 2-up → 1-up) |
| Sign-in split | ~700px |
| Side-by-side table | never — scrolls horizontally at `min-width: 660px` |

If you add Tailwind breakpoints, keep the `minmax` behaviour as the fallback; it is what
makes the sidebar reflow under the results rather than squeezing.

---

## Assets

| Asset | Status |
| --- | --- |
| `HoneyDrop` mascot | **Done.** `frontend/src/components/HoneyDrop.tsx` is already correct — 17 `<rect>`s, `imageRendering: pixelated`, viewBox `0 0 11 13`. Reuse unchanged. It is the only surviving piece of the old visual identity and it carries the brand. |
| Icons | **Lucide**, `stroke-width: 2.75` (the Organic guide mandates this weight). Used: `search`, `arrow-right`, `arrow-left`, `arrow-down`, `check`, `x`, `chevron-down`, `external-link`, `user`, `alert-circle`. Install `lucide-react` rather than inlining the paths I used. |
| Product images | **Placeholders.** Every thumb is a striped `repeating-linear-gradient`. Wire to `product.image` from SerpAPI; keep a striped box as the fallback for a missing or broken URL. |
| Landing photography | **Missing.** The Organic guide wants photographs wrapped in `.washed` (`filter: saturate(0.6) contrast(0.85) brightness(1.1) opacity(0.94)`) with rounded edges. There is currently no photography anywhere — worth adding one washed hero image. |
| Fonts | Caprasimo 400 + Figtree 400/600/700 via Google Fonts. Self-host if you care about the render-blocking request. |

## Files in this bundle

| File | Notes |
| --- | --- |
| `Nectarly.dc.html` | The design. Open in a browser; use the bottom-right nav to reach each state. |
| `Nectarly Current.dc.html` | The existing UI, recreated from your source for diffing. |
| `HoneyDrop.dc.html` | Mascot in isolation. |
| `organic-tokens/styles.css` | The full Organic token sheet + component classes. |
| `organic-tokens/readme.md` | The Organic guide — read "Direction", "Color" and "Interaction states". |

## Suggested order of work

1. `index.css` — swap the `@theme` block and keyframes. Everything else depends on it.
2. `api/client.ts` — new types. Stub `groups` locally so the frontend can be built before
   the backend catches up.
3. `SearchBar.tsx` — smallest component, and it validates the token setup.
4. `TargetProductCard.tsx`, then `ResultCard.tsx` + `AlternativeGroups.tsx`.
5. `App.tsx` — screen + state machine, empty / loading / error.
6. `SpecBreakdownModal.tsx` and `ComparisonTable.tsx`.
7. `LandingPage.tsx`, `SignInPage.tsx`, `ExtensionPanel.tsx`.
8. Backend: `models.py` group enum + spec verdicts, `scoring/value.py` group assignment,
   `routes/search.py` response shape.

CI gate is unchanged — `npm run lint && npm run typecheck && npm run test && npm run build`.

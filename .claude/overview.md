# Technical Specification & System Architecture: Financial Optimization Product Comparison SaaS

---

## 1. Executive Summary & Core Thesis

### 1.1 Core Thesis
Existing e-commerce shopping assistants (e.g., Honey, Capital One Shopping) operate primarily as affiliate conversion engines. Their business models incentivize steering users toward high-margin brand-name products while optimizing only for minor coupon-code discounts at checkout. 

This SaaS platform shifts the paradigm from **discount acquisition** to **capital allocation optimization**. Instead of assisting users in buying an overpriced item for 5% less, the system identifies **functional equivalents**, **white-label/factory generics**, and **cross-category alternatives** that fulfill the user's core functional utility requirement at a significantly lower price point.

### 1.2 Value Proposition
* **Functional Equivalence Engine:** Identifies products with matching physical specifications, material compositions, or functional performance metrics regardless of brand tier.
* **Non-Scam Quality Verification:** Uses statistical filtering to eliminate low-cost, low-quality "junk" generic products.
* **Cross-Category Alternatives:** Bridges non-overlapping feature spaces (e.g., matching a high-end down pillow to a high-density latex ergonomic pillow) by evaluating latent functional utility rather than rigid attribute name matching.

### 1.3 Search Input Modes
The system accepts three distinct input modes, each resolving differently before entering the shared scoring pipeline (Section 3). Description Mode is the safe default for any non-URL input; Exact Product Mode is an escalation out of that default, decided *after* a search already ran — not a peer classification chosen up front from the raw string.

* **URL Mode:** User pastes a link to a specific product page. The linked product is scraped/parsed and used directly as the **target reference product**.
* **Exact Product Mode:** User enters free text that *appears* to name a specific product. The backend does not classify this from the raw string alone: it runs one SerpAPI search first, and only escalates to Exact Product Mode if all three hold — (a) a brand or product-line name from a curated list (`backend/app/brand_names.json`) is detected in the query, (b) that brand is confirmed present in the top SerpAPI hit's own title (not merely detected in the query), and (c) the query is semantically close to that hit's title (`text-embedding-3-small` cosine similarity ≥ `config.EXACT_PRODUCT_MATCH_THRESHOLD`, default 0.5). If any check fails, the request falls through to Description Mode on the same result set — no second upstream call. When escalation succeeds, the confirmed hit becomes the **target reference product**, functionally identical to URL Mode downstream.
* **Description Mode:** User enters a general functional description (e.g., "ergonomic memory foam pillow") rather than a specific product — or a query that named a brand but failed the Exact Product gate above. There is **no target reference product** in this mode — the query itself is embedded and used as the reference vector for Layer 1 similarity (Section 3.1). The UI's Target Reference Product header (Section 5.1) is omitted, and candidates are ranked directly by $Q \cdot \text{Similarity}(\mathbf{u}_{\text{query}}, \mathbf{v}) / \text{Cost}$.

---

## 2. High-Level System Workflow

```
[ User Search Input: URL | Exact Product | Description ]
                   │
                   ▼
   [ Target Resolution (URL/Exact Product only) ]
   (skipped in Description Mode — query embeds directly)
                   │
                   ▼
       [ Data Ingestion Engine ]
   (SerpAPI / Structured Retail Ingestion)
                   │
                   ▼
  [ Layer 1: Latent Space Mapping (SVD) ]
 (Cross-category utility projection & alignment)
                   │
                   ▼
 [ Layer 2: Category Standardization & Weighting ]
     (Z-score scaling + Category Matrix W)
                   │
                   ▼
    [ Layer 3: Bayesian Quality Estimation ]
    (Confidence-adjusted rating baseline Q)
                   │
                   ▼
   [ Layer 4: Value Optimization Ranking ]
     (Score calculation V = (Q * Sim) / Cost)
                   │
                   ▼
     [ Interactive Web Application UI ]
```

---

## 3. Mathematical & Algorithmic Framework

The core engine evaluates candidates across four mathematical layers to produce a deterministic, unbiased ranking of alternative products.

### 3.1 Layer 1: Latent Relationship Mapping (Heterogeneous Feature Spaces)
Products within the same functional domain often have non-overlapping raw attribute schemas (e.g., $700\text{ fill-power down}$ vs. $45\text{ kg/m}^3\text{ memory foam}$). To compare disparate feature spaces without treating them as completely orthogonal, the system projects sparse spec matrices into a shared **Latent Concept Space** using Singular Value Decomposition (SVD).

Given an $m \times n$ product-attribute matrix $A$:

$$A = U \Sigma V^T$$

Where:
* $U \in \mathbb{R}^{m \times r}$ maps each product to $r$ latent functional concepts (e.g., support level, thermal retention, durability).
* $\Sigma \in \mathbb{R}^{r \times r}$ is a diagonal matrix containing singular values scaling the importance of each latent concept.
* $V^T \in \mathbb{R}^{r \times n}$ maps raw technical specifications to the latent concept space.

Similarity between the target product vector $\mathbf{u}_{\text{latent}}$ and an alternative candidate vector $\mathbf{v}_{\text{latent}}$ within the latent subspace is calculated using Cosine Similarity:

$$\text{Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u}_{\text{latent}} \cdot \mathbf{v}_{\text{latent}}}{\|\mathbf{u}_{\text{latent}}\| \|\mathbf{v}_{\text{latent}}\|}$$

**Reference vector by search mode (Section 1.3):** In URL Mode and Exact Product Mode, $\mathbf{u}_{\text{latent}}$ is the resolved target product's projection into latent space. In Description Mode, there is no target product — $\mathbf{u}_{\text{latent}}$ is instead the projection of the embedded query text itself, placed into the same latent space via $V^T$.

---

### 3.2 Layer 2: Category Standardization & Diagonal Weight Matrix

To avoid feature scale distortion across numerical specs (e.g., price in dollars vs. thread count vs. weight in grams), attributes are normalized using Z-score standardization based on category sample distributions.

For a specific feature $k$ with sample mean $\mu_k$ and standard deviation $\sigma_k$:

$$z_k = \frac{x_k - \mu_k}{\sigma_k}$$

To enforce domain-specific importance without relying purely on statistical variance, a category diagonal weight matrix $\mathbf{W} = \text{diag}(w_1, w_2, \dots, w_d)$ is applied to the standardized vector $\mathbf{z}$:

$$\mathbf{v}_{\text{scaled}} = \mathbf{W} \mathbf{z} = \begin{bmatrix} 
w_1 \cdot \left(\frac{x_1 - \mu_1}{\sigma_1}\right) \\ 
w_2 \cdot \left(\frac{x_2 - \mu_2}{\sigma_2}\right) \\ 
\vdots \\ 
w_d \cdot \left(\frac{x_d - \mu_d}{\sigma_d}\right) 
\end{bmatrix}$$

* **Hard Specs (e.g., core material, power output, key dimensions):** $w_k \ge 2.0$
* **Secondary Specs (e.g., color, included accessories):** $w_k = 1.0$
* **Soft Metadata (e.g., title text, seller tags):** $w_k = 0.5$

---

### 3.3 Layer 3: Bayesian Quality Estimator ($Q$)

Raw average star ratings are susceptible to extreme bias when review volume is small (e.g., a product with 2 reviews of 5.0 stars outranking a product with 4,000 reviews of 4.7 stars). The system calculates a Bayesian Weighted Rating $Q$ to establish a statistical confidence threshold:

$$Q = \left( \frac{v}{v + m} \right) R + \left( \frac{m}{v + m} \right) C$$

Where:
* $R$: Observed arithmetic average rating of the candidate product.
* $v$: Total number of user reviews for the candidate product.
* $m$: Minimum review count parameter required to establish statistical confidence (default: $m = 25$).
* $C$: Mean baseline review score across the entire product category (default: $C = 4.0$).

---

### 3.4 Layer 4: Value Optimization Score ($V$)

The final ranking metric combines latent utility similarity, verified quality, and total purchase cost into a unified **Value Optimization Score ($V$)**:

$$V = \frac{Q \cdot \text{Similarity}(\mathbf{u}, \mathbf{v})}{\text{Cost}}$$

* If an alternative product provides $95\%$ functional similarity and equivalent Bayesian quality at $50\%$ of the price, its $V$-score doubles relative to the target item.
* Low-quality generics or cheap items that fail spec similarity criteria suffer heavy penalties in $Q$ or $\text{Similarity}(\mathbf{u}, \mathbf{v})$, filtering out low-utility noise.
* As of the Organic design pass (Section 5, `plan.md` Phase 10), $Q$/$V$/$\cos\theta$ are computed here as before but are **no longer shown in the UI** — only `rating`, `reviewCount`, and a plain `matchScore` percentage reach the client, alongside a human-readable `rationale` sentence per candidate.

---

## 4. Technical Architecture & Data Pipeline

### 4.1 Technology Stack

| Layer | Component / Technology | Justification |
| :--- | :--- | :--- |
| **Frontend UI** | Vite, React | Fast dev server + build tooling for a client-rendered SPA — no server-side rendering; every screen is a client-rendered React tree gated behind `App.tsx`'s state machine (Section 5). |
| **Backend API** | FastAPI (Python 3.11+) | Native support for async processing, asynchronous network execution, and vector math libraries. |
| **Vector & Math Ops** | NumPy, SciPy, PyTorch / `text-embedding-3-small` | Fast matrix transformations, SVD decomposition, vector normalization, and text embedding processing. |
| **Data Ingestion** | SerpAPI (Google Shopping Engine Endpoint) | Avoids local headless browser scraping overhead, bypasses anti-bot blocks, and yields pre-parsed JSON data. |
| **Data Cache** | Redis/Valkey (`cache.py`), on Vultr | Caches search responses and calculated vector embeddings to prevent redundant downstream API calls and minimize latency. |
| **Relational Data** | Vultr Managed Postgres | Accounts, search history, and the coupon feed (`db.py`'s connection pool + schema bootstrap) — separate service from the Redis/Valkey cache above. |

---

### 4.2 Pipeline Execution Flow

1. **Query Processing:**
   * User submits raw text (a URL, a product name, or a description) via the web application — there is no mode selector; `/api/search` infers the mode server-side (Section 1.3).
   * FastAPI checks the cache layer for the resolved query/target key.
   * Exactly one SerpAPI call is made regardless of mode. **URL Mode** parses the pasted link into search text first (no direct scrape yet — `plan.md` Phase 2). **Exact Product Mode** is only confirmed after that call returns, via the brand-detection + brand-confirmation + semantic-similarity gate in Section 1.3; if the gate fails, the request proceeds as **Description Mode** on the same result set — no second upstream call.
   * **Description Mode** (including the fallback above): no target product is resolved from the results; a synthetic baseline (the median-priced candidate — `plan.md` Phase 11's `_median_product`) stands in for savings and spec-comparison math, while the raw query text is what is actually embedded as the reference vector.

2. **Data Aggregation & Ingestion:**
   * On a cache miss, the backend dispatches parallel API requests to structured shopping endpoints (SerpAPI Google Shopping) to gather candidate products.
   * Aggregated payload extracts product title, price, brand, raw rating, review volume, vendor details, image URLs, and technical spec text.

3. **Vector Vectorization & Matrix Processing:**
   * Text descriptions and technical specs (and, in Description Mode, the query text itself) pass into an embedding pipeline to form dense representation vectors.
   * Numerical features (price, physical dimensions, material weight) are standardized via category Z-scores ($z_k$) and transformed via weight matrix $\mathbf{W}$.
   * Latent concept alignment is computed using SVD / dense cosine distance against the reference vector — the target reference product (URL/Exact Product Mode) or the embedded query (Description Mode).

4. **Quality & Value Computation:**
   * Bayesian quality score $Q$ is computed per candidate item.
   * Value Optimization Score $V$ is evaluated, and candidates are sorted into distinct output tiers.

---

## 5. Web Application UI/UX Design Breakdown

As of the Organic design system pass (`plan.md` Phase 10) and the account/coupon
work that followed it (undocumented in `plan.md` — see the closing note at the
end of Section 6), the product has five top-level screens — a marketing
landing page, the search + results flow below, sign-in, profile, and settings —
plus one modal overlay, the spec comparison view, layered over the search +
results screen. (A sixth screen, an in-app mock of the browser extension's
panel, was deleted in Phase 16; the real extension lives in `extension/` and
the landing page links its packaged `.zip` — the one live connection back to
the app is a `?q=<title>` deep-link that `App.tsx` reads once on mount and
uses to auto-run that search.) The Organic design reference bundle that held
the full visual spec was deleted in the same pass — `frontend/src/index.css`'s
`@theme` block is now the only definition of the design tokens.

Two things changed from the original design that are **not** purely cosmetic:

1. **Tiers are now presented as three named equivalence groups** — the
   underlying ranking logic is unchanged (Section 3.4), only relabeled for the
   UI: `same_spec` (was Tier 1), `same_job` (was Tier 2), `clears_floor` (was
   Tier 3). Groups are ordered by equivalence, and products are ranked by $V$
   *within* a group — so the single cheapest item in the whole result set does
   not necessarily lead.
2. **Raw scoring math is no longer shown in the UI.** No $\cos\theta$, no
   Bayesian $Q$, no value multiplier $V$ on screen — the backend still
   computes all three to drive ordering and the quality floor (Section 3.4),
   but the UI surfaces only `rating`, `reviewCount`, a plain `matchScore`
   percentage, and a human-readable `rationale` sentence per candidate.

The search + results surface:

```
+-----------------------------------------------------------------------------------+
|  [ Search Bar: Paste Product Link or Type Search Query... ]        [ Search ]     |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  YOUR REFERENCE PRODUCT                                                          |
|  [Image]  Brand-Name Ergonomic Pillow - $120.00                                   |
|           Specs: Memory Foam, Cooling Gel, Contour Design | Rating: 4.5 (1,200)    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  {n} ALTERNATIVES WORTH YOUR ATTENTION                                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  ● SAME SPEC, NO LOGO   [n results]                                               |
|    matches the original's materials and construction                              |
|    +----------+ +----------+ +----------+ +--                                     |
|    | [Image]  | | [Image]  | | [Image]  | | [                                     |
|    | Unbranded| | Generic  | | Contour  | | S    ← horizontal scroll / snap        |
|    | Contour  | | Memory   | | Foam Pil | | t                                     |
|    | $42.00   | | $48.00   | | $51.00   | | $                                     |
|    | saves $78| | saves $72| | saves $69| | s                                     |
|    | ▓▓▓▓░░░░ | | ▓▓▓▓▓░░░ | | ▓▓▓▓▓░░░ | | ▓                                     |
|    | 96% 4.4★ | | 91% 4.3★ | | 89% 4.5★ | | 8                                     |
|    |[Cmp][Buy]| |[Cmp][Buy]| |[Cmp][Buy]| | [                                     |
|    +----------+ +----------+ +----------+ +--                                     |
|                                                                                   |
|  ● DIFFERENT BUILD, SAME JOB   [n results]                                        |
|    another way of reaching the same outcome                                       |
|    +----------+ +----------+ +----------+ +--   (same rail, scrolls sideways)      |
|                                                                                   |
|  ● CHEAPEST THAT CLEARS QUALITY   [n results]                                     |
|    lowest price still above the quality floor                                     |
|    +----------+ +----------+ +----------+ +--   (same rail, scrolls sideways)      |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

Each group is a horizontally-scrolling snap rail of fixed-width portrait cards
(`plan.md` Phase 17), not a vertical list. Nothing upstream caps candidate
count, so a group can hold 20+ cards; the rail keeps the page's vertical height
fixed at roughly three rails regardless, which is what makes all three groups
visible at once. The earlier Ranked / Side-by-side toggle and the
all-candidates spec table behind it are gone — per-candidate spec comparison
still lives in the Compare overlay.

Alongside this column sits a sticky sidebar (not shown in the sketch above,
which stays single-column for readability), rendered whenever the search
returns at least one result. Top to bottom: a **Possible Savings** card (the
top-ranked candidate's savings against the target's price — or its own price
alone in Description Mode — plus its match score, name, brand/retailer, and
rating); a **Cheapest option** card (the lowest price among all returned
results, since everything shown has already cleared the Bayesian quality
floor); and a **Coupons & history** card (Section 7) that stays idle until the
user picks a candidate from the rails above, then looks up an active code for
that candidate's retailer and, beneath it in the same card, that listing's
recorded price history (lowest observed price, and whether it is trending
down — an observed direction, never a forecast).

### 5.1 Component Breakdown
* **Search Bar:** One input for all three modes (Section 1.3) — no mode selector. The backend infers url / exact_product / description from the raw string; any non-empty string is valid input. Also runs a frontend-only ghost-suggestion autocomplete (`frontend/src/lib/autocomplete.ts` against a curated `frontend/src/data/brandSuggestions.ts` list) — Tab accepts the suggestion; purely client-side prefix matching, no backend involvement.
* **Reference Product Card:** Displays the resolved target product to serve as the reference anchor for price, specs, and rating benchmarks. **Rendered only in URL and Exact Product modes** — omitted entirely in Description Mode, since no single target product is resolved.
* **Same spec, no logo** (was Tier 1): Products with matching materials and structural specifications produced without brand markups.
* **Different build, same job** (was Tier 2): Products from different material domains that achieve equivalent functional utility mapped through the latent SVD matrix layer.
* **Cheapest that clears quality** (was Tier 3): The lowest absolute price point that successfully passes the Bayesian Quality ($Q$) safety threshold, catering to maximum cost reduction.
* **Comparison overlay:** Per-candidate spec breakdown against the reference product, with a five-value verdict chip per spec (`same`/`better`/`close`/`different`/`lower`) and a one-to-two sentence `rationale`.
* **Landing, sign-in, profile, and settings surfaces:** Marketing/account surfaces outside the search+results flow — see `plan.md` Phase 10. The landing page's extension section hands over the real packaged extension as a download (`plan.md` Phase 16); the in-app mock panel that used to stand in for it is gone. Profile lists a signed-in user's past searches (re-runnable via `GET /api/auth/history`, clearable via `DELETE`); Settings edits display name, avatar (client-side cropped/resized before upload), and the `share_data` privacy toggle (Section 6.3). Both fall back to the sign-in screen when signed out, and neither is in `plan.md`'s phase checklist (see the closing note at the end of Section 6).
* **Account menu:** Header pill — a sign-in button when signed out, or a menu (Profile / Settings / Log out) when signed in.
* **Coupon panel:** Sidebar card titled "Coupons & history" (see the sidebar description above and Section 7) — looks up a candidate's retailer via `GET /api/coupons?store=` once the user selects it from the rails, shows the best active code/discount description/expiry when one exists, and estimates a savings figure with a text heuristic since the underlying feed carries no numeric discount field. Beneath the coupon result, the same card folds in `PriceHistoryPanel.tsx`: one `POST /api/price-history/view` per selection records the view as a price snapshot and returns the listing's lowest recorded price and observed trend, shown as two plain rows ("Lowest recorded", "Likely to drop" — Yes/No/Unclear from the trend). Below three snapshots it says there isn't enough history yet. No forecast, no projected date, no buy/wait verdict — by design.

---

## 6. User Accounts & Shopping History

### 6.1 Account Creation
* Email-based accounts — user signs up/logs in with an email address (mechanism: magic-link or verification-code email, no password storage for MVP — avoids password hashing/reset flows; revisit if a password flow is explicitly wanted).
* Backed by the Vultr Managed Postgres cluster referenced in `deploy/README.md` §1. `db.py` bootstraps the schema on startup and `accounts/store.py` reads/writes it, so `DATABASE_URL` is live rather than the dead config it originally was.
* Core account fields: `id`, `email` (unique), `created_at`, `display_name` (nullable), `avatar` (nullable `data:image/...` URL, ~100KB cap, client-side cropped/resized to a 128px JPEG before upload — see Section 5.1's Settings surface), `share_data` (boolean, default `true` — see Section 6.3 for what it gates).
* Sign-up is gated on a required terms checkbox disclosing that we store the user's email and their searches (`plan.md` Phase 12). The gate is **UI-only** — the browser's native `required` validation blocks the form, but acceptance is never sent to or stored by the backend, so there is no per-account consent record to audit. Add `accepted_terms_at` if that ever needs proving.
* `routes/auth.py` grew from the 3 routes Phase 8 shipped to 7: `request-code`/`verify`/`me` (GET) originally, plus `logout`, `me` (PATCH, profile update), and `history` (GET and DELETE — Section 6.2).

### 6.2 Search History (implemented)
* Every signed-in search is persisted against the account (`searches` table, `account_id` non-null) and surfaced back to that user via `GET /api/auth/history` — rendered by `ProfilePage.tsx` as a list of past queries, each re-runnable (`rerun` re-executes the query through the normal search flow, not a cached replay) and clearable (`DELETE /api/auth/history`, backed by `accounts/store.py`'s `delete_search_history`).
* Stores only `query`, `mode`, `result_count`, `created_at` (`SearchHistoryItem` in `models.py`) — **not** the resolved target or returned groups from that search. A "revisit this exact comparison" feature (as opposed to re-running the same query fresh) would still need a schema change.
* Does not drive personalization or re-weight $V$ by past category preferences — it is a plain log surfaced back to its owner, nothing more.
* Not in `plan.md`'s phase checklist — see the closing note at the end of this section.

### 6.3 Search Log & Admin Dashboard (implemented — `plan.md` Phase 13)
* Every `/api/search` call is logged to a `searches` table (`query`, `mode`, `result_count`, `created_at`, nullable `account_id`). Search requires no sign-in, so most rows are anonymous — that is deliberate, not a gap.
* Recorded by `analytics.py`, which **never raises**: a broken or unreachable database degrades tracking, never a user's search.
* Each account's `share_data` preference (default `true`, edited via the Settings surface — Section 5.1) stamps `searches.private = NOT share_data` at **insert time**, evaluated from the account's setting as it stands at that moment — not retroactive. Toggling `share_data` off only makes searches recorded from that point forward private; earlier searches keep whichever value they were already stamped with. Anonymous searches (`account_id` null) are always non-private. `admin_stats()`'s every query (totals, 24h counts, top queries, recent-searches list) filters `WHERE NOT private`, so opting out removes an account's future searches from the internal dashboard entirely — the account's own history view (Section 6.2) is unaffected either way, and `ProfilePage.tsx` shows a notice when the user's own `share_data` is currently off.
* `GET /api/admin` renders signups and search activity as server-rendered HTML behind HTTP Basic (`ADMIN_PASSWORD`), and 503s while that is unset. Deliberately not part of the React app — no new frontend surface, no routing change.
* This is the **log** half of §6.2. It is internal-facing only: nothing about it is exposed to the user whose searches it records.

**Note on `plan.md` coverage:** the account fields/routes above (display name, avatar, `share_data`, logout, profile update), all of Section 6.2, and the Section 5.1 surfaces they feed (`AccountMenu.tsx`, `ProfilePage.tsx`, `SettingsPage.tsx`, `CouponPanel.tsx`) exist in the shipped app but have no corresponding entry in `plan.md`'s phase checklist — they were built and merged outside the phase-based workflow. Flagged here rather than backfilled into `plan.md`, per instruction to only touch what's explicitly asked.

---

## 7. Coupon Lookup & Best-Offer Selection

Best-active-coupon lookup by retailer, layered on top of the core comparison pipeline rather than integrated into its scoring (Section 3) — a coupon changes what a listing effectively costs at checkout, not its functional-similarity score.

* **Data source:** CouponAPI.org's periodic full CSV feed, loaded via `backend/app/coupons/loader.py`'s `load_feed(csv_path)` into a local `coupon_offers` Postgres table — upserted, keyed by `offer_id`, so re-running against a newer feed is idempotent. Automated feed retrieval is unconfirmed; the loader is invoked manually (`python -m app.coupons.loader <path>`).
* **Selection:** `coupons/selector.py`'s `best_offer(store)` normalizes the retailer name to the feed's bare-domain form, filters out expired offers, and ranks by `rating` desc then `start_date` desc (`NULLS LAST`) as a recency tiebreak — returns the single best `CouponOffer` (`code`, `discount_description`, `store`, `expires_at`, `start_date`, `rating`) or `None`.
* **API:** `GET /api/coupons?store={name}` (`routes/coupons.py`) — checks `cache.py`'s `get_cached_coupon` first, calls `best_offer` on a miss, caches a hit for 3600s (`set_cached_coupon`; a miss is never cached, since the underlying query is cheap and a coupon can appear between calls).
* **UI:** `CouponPanel.tsx`, a sidebar card alongside the results (Section 5.1) — driven by whichever candidate the user selects from the rails, not automatically the target reference product; idle until one is chosen. The feed carries no numeric discount field, so the panel estimates a savings figure from the offer's text (a regex heuristic against strings like "15% off" or "$10 off") rather than computing one — an approximation, shown only when the pattern matches. The same card also hosts the price-history section (`PriceHistoryPanel.tsx`, Section 5.1) under a divider; the two lookups fetch independently off the same selection.
* Same `plan.md` coverage gap as the closing note at the end of Section 6: the backend (loader/selector/route) is Phase 9; the panel that surfaces it in the UI shipped later with no phase entry.
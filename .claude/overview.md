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

---

## 2. High-Level System Workflow

```
[ User Search Input / Target Product URL ]
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

---

## 4. Technical Architecture & Data Pipeline

### 4.1 Technology Stack

| Layer | Component / Technology | Justification |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js, React | High-performance server-side rendering and quick DOM updates for complex comparison matrices. |
| **Backend API** | FastAPI (Python 3.11+) | Native support for async processing, asynchronous network execution, and vector math libraries. |
| **Vector & Math Ops** | NumPy, SciPy, PyTorch / `text-embedding-3-small` | Fast matrix transformations, SVD decomposition, vector normalization, and text embedding processing. |
| **Data Ingestion** | SerpAPI (Google Shopping Engine Endpoint) | Avoids local headless browser scraping overhead, bypasses anti-bot blocks, and yields pre-parsed JSON data. |
| **Data Cache** | vultr | Caches search responses and calculated vector embeddings to prevent redundant downstream API calls and minimize latency. |

---

### 4.2 Pipeline Execution Flow

1. **Query Processing:**
   * User inputs a search query (e.g., "ergonomic memory foam pillow") or pastes a target product URL into the web application.
   * FastAPI parses the query, extracts core category bounds, and checks the Redis cache layer.

2. **Data Aggregation & Ingestion:**
   * On a cache miss, the backend dispatches parallel API requests to structured shopping endpoints (SerpAPI Google Shopping).
   * Aggregated payload extracts product title, price, brand, raw rating, review volume, vendor details, image URLs, and technical spec text.

3. **Vector Vectorization & Matrix Processing:**
   * Text descriptions and technical specs pass into an embedding pipeline to form dense representation vectors.
   * Numerical features (price, physical dimensions, material weight) are standardized via category Z-scores ($z_k$) and transformed via weight matrix $\mathbf{W}$.
   * Latent concept alignment is computed using SVD / dense cosine distance against the target reference product.

4. **Quality & Value Computation:**
   * Bayesian quality score $Q$ is computed per candidate item.
   * Value Optimization Score $V$ is evaluated, and candidates are sorted into distinct output tiers.

---

## 5. Web Application UI/UX Design Breakdown

The web application layout centers on immediate visual clarity, contrasting the targeted brand item directly against optimized financial alternatives.

```
+-----------------------------------------------------------------------------------+
|  [ Search Bar: Paste Product Link or Type Search Query... ]        [ Search ]     |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  TARGET REFERENCE PRODUCT                                                         |
|  [Image]  Brand-Name Ergonomic Pillow - $120.00                                   |
|           Specs: Memory Foam, Cooling Gel, Contour Design | Rating: 4.5 (1,200)    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  FINANCIAL ALTERNATIVES & SPEC-MATCHED RANKINGS                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  TIER 1: DIRECT FACTORY / GENERIC EQUIVALENT (Highest Value Score)                |
|  [Image]  Unbranded Contour Memory Foam Pillow                                        |
|           Price: $42.00 (Savings: $78.00 / 65%)                                   |
|           Spec Match: 96%  |  Quality Score (Q): 4.4/5.0  |  Value Score (V): High  |
|           [ Compare Spec Breakdown ]                       [ Direct Purchase Link ]|
|                                                                                   |
|-----------------------------------------------------------------------------------|
|                                                                                   |
|  TIER 2: CROSS-CATEGORY FUNCTIONAL ALTERNATIVE                                    |
|  [Image]  High-Density Natural Latex Support Pillow                               |
|           Price: $55.00 (Savings: $65.00 / 54%)                                   |
|           Spec Match: 88% (Latex vs. Memory Foam - Equal Ergonomic Support)       |
|           Quality Score (Q): 4.6/5.0                      |  Value Score (V): Med-High|
|           [ Compare Spec Breakdown ]                       [ Direct Purchase Link ]|
|                                                                                   |
|-----------------------------------------------------------------------------------|
|                                                                                   |
|  TIER 3: BUDGET BENCHMARK EQUIVALENT                                              |
|  [Image]  Standard High-Density Foam Pillow                                       |
|           Price: $22.00 (Savings: $98.00 / 81%)                                   |
|           Spec Match: 74%  |  Quality Score (Q): 4.1/5.0  |  Value Score (V): Moderate|
|           [ Compare Spec Breakdown ]                       [ Direct Purchase Link ]|
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### 5.1 Component Breakdown
* **Target Baseline Header:** Displays the user's initial selection to serve as the reference anchor for price, specs, and rating benchmarks.
* **Tier 1 (Direct Factory/Generic Equivalent):** Displays products with matching materials and structural specifications produced without brand markups.
* **Tier 2 (Cross-Category Functional Alternative):** Displays products from different material domains that achieve equivalent functional utility mapped through the latent SVD matrix layer.
* **Tier 3 (Budget Benchmark):** Displays the lowest absolute price point that successfully passes the Bayesian Quality ($Q$) safety threshold, catering to maximum cost reduction.
## Status: Staged
Task: Phase 11 — Backend Data Contract Catch-up (parsed from partner's Q&A plan; will move to plan.md next)

Housekeeping first (git, not code):
- Commit current uncommitted work (coupons `__init__.py`/`models.py`, Phase 9 `plan.md` edit)
- `git pull` to sync local `mvp` with `origin/mvp` (has Phase 10 redesign + a draft Phase 11 stub in plan.md that this corrects)

1. `backend/app/ingestion/serpapi_client.py`
- Add `_MATERIAL` regex, same shape as `_SIZE` (line 40)
- Vocab: memory foam|foam|latex|down|feather|microfiber|fleece|cotton|linen|bamboo|wool|silk|polyester|nylon|denim|leather|suede|stainless steel|aluminum|titanium|ceramic|silicone|rubber|glass|plastic|wood
- `memory foam` MUST precede `foam` (first-match alternation)
- Ship `material` spec only, `weight_tier="hard"` — no `feature_*` booleans

2. `backend/app/models.py`
- `Tier` → `Group` StrEnum: `SAME_SPEC` / `SAME_JOB` / `CLEARS_FLOOR`
- `ComparisonResult.tier` → `.group`
- No `direction` field on `SpecAttribute` (corrects draft plan.md stub — cache-safety trap, cache.py:69-73 has no try/except on `Product.model_validate`, TTL 3600)

3. `backend/app/scoring/value.py`
- `_assign_tier` → `_assign_group`, same thresholds/logic
- Add `_GROUP_RANK = {SAME_SPEC: 0, SAME_JOB: 1, CLEARS_FLOOR: 2}`
- Fix sort key (line 86): `key=lambda r: (_GROUP_RANK[r.group], -r.value_score)` — verified bug: new names sort `clears_floor < same_job < same_spec` lexicographically, exact reversal

4. `backend/app/config.py`
- Rename `SPEC_MATCH_TIER1` → `SPEC_MATCH_SAME_SPEC`, `SPEC_MATCH_TIER2` → `SPEC_MATCH_SAME_JOB`
- Verified no compose/CI/.env override exists (grepped, confirmed empty)

5. `backend/app/scoring/explain.py` (new file)
- `Verdict = Literal["same", "better", "close", "different", "lower"]` (5 values, no `equivalent`)
- `COMMERCE_SPECS = {"price", "discount_pct", "rating", "review_count"}`
- `_SIGN: dict[str, int]` keyed on unit suffix: `{"gb": 1, "tb": 1, "mah": 1, "lb": -1, "kg": -1}`, everything else neutral (deliberately no g/oz)
- `verdict(name, target_value, value) -> Verdict | None` — None when target lacks the spec; strings: casefold-equal→same else different; numerics: equal→same, ratio in [0.95,1.05]→close, else sign 0→different / ±1→better/lower
- `rationale(result, verdicts) -> str` — group-keyed opening clause, "N of M listed specs match" (omit if all verdicts None), savings clause (omit if savings_percent None), rating/reviews. Never emits quality_score/value_score.

6. `backend/app/routes/search.py`
- `Tiers` → `Groups` (explicit 3-field BaseModel: same_spec/same_job/clears_floor, not a dict)
- `WireProductSpec` gains `verdict: Verdict | None = None`
- `WireProduct` gains `short: str`, `rationale: str | None = None`; loses `tier`; gains NO `group` (corrects draft plan.md stub — nothing reads it, dead field)
- `_to_wire_product` takes `target: Product | None`, filters `COMMERCE_SPECS` from emitted specs, calls `explain.verdict`/`explain.rationale`
- Add `_short(title)`: strip leading "The", first 3 words, strip trailing punctuation
- Delete `_tier_to_int` — bucket on enum member directly
- snake_case group keys intentional (comment why — design-system ids, not wire-field casing)
- Target product: reuse existing `comparison is None` branch precedent for savings=None; `short` stays non-optional

7. `frontend/src/api/client.ts`
- Delete legacy stub block wholesale: LegacyProductSpec, LegacyProduct, LegacySearchResponse, TIER_TO_GROUP, stubVerdict, stubRationale, stubShort, adaptProduct, adaptTargetProduct, adaptSearchResponse
- `searchProducts` becomes direct `apiFetch<SearchResponse>`, keep timeout try/catch
- Rewrite header comment: "Mirrors the response models in backend/app/routes/search.py"
- `Verdict` drops `equivalent`; `ProductSpec.verdict` optional; `Product` drops `group`, gains `rationale?: string`

8. `frontend/src/components/SpecBreakdownModal.tsx`
- Remove `equivalent` entry from `VERDICT_STYLE`
- `SpecRow.verdict` → `Verdict | null`; `s.verdict ?? null`; `match?.verdict ?? null`
- Render verdict chip only when non-null; guard optional `{product.rationale}`

Tests:
- `backend/tests/test_explain.py` (new): same/close/better/lower/different cases, None-when-no-counterpart, union-coverage test (all 5 values reachable), rationale savings-clause present/absent, assert no Q/V figures
- `backend/tests/test_scoring.py`: fix stale `Tier` import + 3 assert sites; convert `test_tiers_spread_across_a_realistic_similarity_range` (line 107) from set-assert to ordered-list assert + rename — THIS is the sort-bug regression guard
- `backend/tests/test_ingestion.py`: add `specs["material"] == "memory foam"` case (proves alternation order) + two-materials-one-title case
- `backend/tests/test_pipeline.py`: `body["tiers"]` → `body["groups"]`; empty case → `{"same_spec": [], "same_job": [], "clears_floor": []}`; give `_product` a `specs` param; add commerce-specs-absent, target has short/no rationale, description-mode-all-None-verdicts cases
- Optional hardening: wrap `cache.get_cached_search` in `except ValidationError: return None` + one `test_cache.py` case (not required by this phase, but cheap and closes the "next model change 500s prod for an hour" risk)

Docs:
- `.claude/plan.md` Phase 11 needs full rewrite (next step after this) — existing draft stub on origin/mvp is wrong on `direction` and `group`; check off items as they land
- Leave other doc staleness alone (architecture.md's phantom routes/compare.py, stale test list) — out of scope per locked decision

Verification (run after implementation, not part of staging):
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest`
- `cd frontend && npm run lint && npm run typecheck && npm run build`
- Manual: real backend + frontend, search "purple harmony pillow" — groups render same_spec→same_job→clears_floor order, Compare overlay shows material/size/measure_* rows only (no commerce rows), rationale has no Q/V figures
- Manual: description-mode search (>4 words) — no target card, all verdicts absent, rationale renders without savings clause

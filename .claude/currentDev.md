## Status: Staged
Target: `.claude/plan.md` — add new `## Phase 9: Coupons` section (plan-only, no code yet)

- Best-active-coupon lookup by retailer, via CouponAPI.org — confirmed no retailer status required (verified directly against couponapi.org), $49–66/mo depending on tier, 7-day free trial
- Frontend display trigger/UI is explicitly out of scope for this phase (user: "the display will be handled at frontend so don't plan display logic yet") — backend only
- **Blocked, flagged to user:** CouponAPI.org's real technical docs (endpoint URL, auth header, response field names) are behind their customer knowledgebase — checked directly, not publicly viewable. `coupons/client.py` cannot be implemented for real until the user signs up for the trial and shares the actual spec (endpoint/auth/sample response) or the relevant knowledgebase article content
- New section text to append after `## Phase 8: Accounts`:

  ```
  ## Phase 9: Coupons
  Best-active-coupon lookup by retailer, via CouponAPI.org (no retailer status required — confirmed directly against their site; $49-66/mo, 7-day free trial). Frontend display trigger/UI is out of scope for this phase (handled separately later) — backend lookup capability only.
  - [ ] `backend/app/config.py` — add `COUPON_API_KEY` (exact env var name pending real docs)
  - [ ] `backend/app/coupons/models.py` — normalized internal `CouponOffer` model (code, discount description, store, expires_at, verified_at) — insulates the rest of the app from CouponAPI.org's actual raw schema
  - [ ] `backend/app/coupons/client.py` — CouponAPI.org wrapper, fetches raw coupons for a store, maps to `CouponOffer`. **Blocked** — endpoint URL/auth/response field names are not publicly documented (checked; behind a signed-in knowledgebase); cannot be implemented until the user has real API access and shares the actual spec
  - [ ] `backend/app/coupons/selector.py` — given a list of `CouponOffer`s for one store, return the single best currently-active one: filter out anything with `expires_at` in the past, rank the rest by discount magnitude, tiebreak by most-recently-verified — depends only on the normalized model, buildable now regardless of the `client.py` blocker
  - [ ] `backend/app/routes/coupons.py` — `GET /api/coupons?store={name}`, looks up the best active coupon for a retailer on demand — lazy/on-click, not embedded into every `/api/search` response (avoids one extra paid API call per candidate on every search)
  - [ ] `backend/app/main.py` — wire `coupons.router` in (extends Phase 0 file)
  ```
- Not in scope for this stage: no code changes, no `overview.md` edit yet (would need a new section similar to accounts' §6, but not added here — ask user first, same as accounts was)

import os

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set from the Vultr Managed Postgres connection string in the deploy env.
# Nothing reads it yet — there is no data model. When one lands, this is where
# the engine gets built, and deploy/README.md covers wiring migrations in.
DATABASE_URL = os.getenv("DATABASE_URL")

# Phase 8 accounts: transactional email (Resend) + session-cookie signing.
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# Resend's own sandbox sender — works without a verified domain. Override once
# a verified @nectarly.us sender exists in the Resend account.
MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS", "onboarding@resend.dev")
SESSION_SECRET = os.getenv("SESSION_SECRET")
VERIFICATION_CODE_TTL_MINUTES = int(os.getenv("VERIFICATION_CODE_TTL_MINUTES", "10"))
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))
# Defaults false: both deploy boxes currently serve plain HTTP on a bare IP (no
# domain/TLS yet — deploy/README.md §1). secure=True would stop the browser
# from ever sending the cookie back over HTTP. Flip once a domain + TLS exist.
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Layer 1 SVD default latent concept count (overview.md §3.1).
SVD_RANK = int(os.getenv("SVD_RANK", "10"))

# Layer 4 quality safety filter + tier thresholds (overview.md §1.2, §5.1).
MIN_QUALITY_THRESHOLD = float(os.getenv("MIN_QUALITY_THRESHOLD", "3.5"))
SPEC_MATCH_TIER1 = float(os.getenv("SPEC_MATCH_TIER1", "0.85"))
SPEC_MATCH_TIER2 = float(os.getenv("SPEC_MATCH_TIER2", "0.6"))

# Vultr-managed cache connection string.
CACHE_URL = os.getenv("CACHE_URL")

# Layer 3 Bayesian quality estimator defaults (overview.md §3.3).
BAYESIAN_M = float(os.getenv("BAYESIAN_M", "25"))
BAYESIAN_C = float(os.getenv("BAYESIAN_C", "4.0"))

# Layer 2 category weight tiers (overview.md §3.2). Not env-overridable —
# per-category weights will be data-driven later, not per-deploy config.
CATEGORY_WEIGHTS: dict[str, float] = {
    "hard": 2.0,
    "secondary": 1.0,
    "soft": 0.5,
}

# Phase 9 coupons: CouponAPI.org lookup key. Env var name is a placeholder —
# their real auth scheme (and whether a second credential like a
# publisher/affiliate ID is also required) isn't confirmed yet; see plan.md
# Phase 9's blocker note. Revisit once real docs are in hand.
COUPON_API_KEY = os.getenv("COUPON_API_KEY")

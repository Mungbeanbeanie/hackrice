import os

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

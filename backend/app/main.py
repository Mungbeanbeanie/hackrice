import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.routes import admin, auth, coupons, price_history, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        db.init_schema()
    except Exception:
        logger.exception(
            "Accounts DB schema bootstrap failed — /api/auth/* will 502 until fixed"
        )
    yield


app = FastAPI(title="hackrice", lifespan=lifespan)

# Phase 14 browser extension: the background service worker's fetch to
# /api/search is the first cross-origin caller this API has ever had (the
# deployed frontend and API sit behind the same Caddy front door). Scoped to
# exactly what the extension needs, not allow_origins=["*"] with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://.*",
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(search.router)
app.include_router(auth.router)
app.include_router(coupons.router)
app.include_router(price_history.router)
app.include_router(admin.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe. Used by the compose healthcheck and the deploy smoke test."""
    return {"status": "ok"}

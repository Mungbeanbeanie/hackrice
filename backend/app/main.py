import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.routes import auth, compare, search

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

app.include_router(search.router)
app.include_router(compare.router)
app.include_router(auth.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe. Used by the compose healthcheck and the deploy smoke test."""
    return {"status": "ok"}

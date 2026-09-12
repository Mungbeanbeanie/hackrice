from fastapi import FastAPI

from app.routes import search

app = FastAPI(title="hackrice")

app.include_router(search.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe. Used by the compose healthcheck and the deploy smoke test."""
    return {"status": "ok"}

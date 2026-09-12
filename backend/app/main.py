from fastapi import FastAPI

from app.routes import compare, search

app = FastAPI(title="hackrice")

app.include_router(search.router)
app.include_router(compare.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe. Used by the compose healthcheck and the deploy smoke test."""
    return {"status": "ok"}

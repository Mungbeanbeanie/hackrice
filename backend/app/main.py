import os

from fastapi import FastAPI

from app.routes import compare, search

app = FastAPI(title="hackrice")

app.include_router(search.router)
app.include_router(compare.router)

# Set from the Vultr Managed Postgres connection string in the deploy env.
# Nothing reads it yet — there is no data model. When one lands, this is where
# the engine gets built, and deploy/README.md covers wiring migrations in.
DATABASE_URL = os.getenv("DATABASE_URL")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe. Used by the compose healthcheck and the deploy smoke test."""
    return {"status": "ok"}

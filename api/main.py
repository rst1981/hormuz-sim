"""FastAPI application — war room dashboard backend."""

from __future__ import annotations

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure repo root is on path so `src` package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import simulation, parameters, monte_carlo, scenarios, comparison, export, updates, snapshots
from api.ws.handlers import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Hormuz Crisis Simulation — War Room API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routers
app.include_router(simulation.router)
app.include_router(parameters.router)
app.include_router(monte_carlo.router)
app.include_router(scenarios.router)
app.include_router(comparison.router)
app.include_router(export.router)
app.include_router(updates.router)
app.include_router(snapshots.router)

# WebSocket router
app.include_router(ws_router)


@app.get("/api/health")
def health():
    from api.config import settings
    import os
    return {
        "status": "ok",
        "anthropic_key_set": bool(settings.ANTHROPIC_API_KEY),
        "anthropic_key_prefix": settings.ANTHROPIC_API_KEY[:12] if settings.ANTHROPIC_API_KEY else "",
        "env_has_hormuz_key": bool(os.environ.get("HORMUZ_ANTHROPIC_API_KEY")),
        "env_has_plain_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }

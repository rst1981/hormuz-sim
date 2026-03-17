"""FastAPI application — war room dashboard backend."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure repo root is on path so `src` package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import simulation, parameters, monte_carlo, scenarios, comparison, export, updates, snapshots
from api.ws.handlers import router as ws_router

logger = logging.getLogger(__name__)


def _daily_baseline_snapshot() -> None:
    """Save an auto-snapshot of today's baseline (skips if one already exists)."""
    from datetime import date
    from api.services.snapshot_store import snapshot_store

    today = date.today().isoformat()
    name = f"Auto — {today}"

    # Skip if today's auto-snapshot already exists
    for s in snapshot_store.list_snapshots():
        if s["name"] == name:
            logger.info("Daily snapshot already exists for %s, skipping", today)
            return

    snapshot_store.save_snapshot(name)
    logger.info("Saved daily baseline snapshot: %s", name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the original baseline snapshot exists
    from api.services.snapshot_store import snapshot_store
    snapshot_store.ensure_original_baseline()
    logger.info("Original baseline snapshot ensured")

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _daily_baseline_snapshot,
        CronTrigger(hour=0, minute=1, timezone="America/Los_Angeles"),
        id="daily_baseline_snapshot",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduled daily baseline snapshot at 12:01 AM PST")

    yield

    scheduler.shutdown(wait=False)


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
        "anthropic_key_prefix": settings.ANTHROPIC_API_KEY[:20] if settings.ANTHROPIC_API_KEY else "",
        "anthropic_key_suffix": settings.ANTHROPIC_API_KEY[-6:] if settings.ANTHROPIC_API_KEY else "",
        "anthropic_key_len": len(settings.ANTHROPIC_API_KEY),
        "env_has_hormuz_key": bool(os.environ.get("HORMUZ_ANTHROPIC_API_KEY")),
        "env_has_plain_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }

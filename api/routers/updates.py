"""Situation updates — OSINT-driven baseline calibration endpoints."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.update_store import SituationUpdate, ParameterChange, update_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/updates", tags=["updates"])


# ── Request / Response models ────────────────────────────────────────────

class ManualUpdateRequest(BaseModel):
    date: str  # YYYY-MM-DD
    summary: str
    raw_text: str = ""
    source: str = "manual"
    parameter_changes: list[dict[str, Any]] = Field(default_factory=list)


class UpdateResponse(BaseModel):
    id: str
    date: str
    source: str
    source_url: Optional[str]
    raw_text: str
    summary: str
    category: str
    parameter_changes: list[dict[str, Any]]
    status: str
    reviewed_at: Optional[str]
    created_at: str


# ── Endpoints ────────────────────────────────────────────────────────────

@router.get("")
def list_updates(status: Optional[str] = None, date: Optional[str] = None):
    """List all situation updates, optionally filtered by status or date."""
    return update_store.get_all(status=status, date=date)


@router.get("/baseline")
def get_baseline(date: Optional[str] = None):
    """Get the computed baseline (Day 18 defaults + applied deltas).

    If `date` is provided, returns baseline as of that date.
    """
    if date:
        return update_store.get_baseline_for_date(date)
    return update_store.get_current_baseline()


@router.get("/baseline/projected")
def get_projected_baseline():
    """Get the projected baseline if all pending updates were approved."""
    return update_store.get_projected_baseline()


@router.get("/dates")
def get_available_dates():
    """Get list of dates that have applied updates (for historical sim date picker)."""
    return update_store.get_available_dates()


@router.get("/{update_id}")
def get_update(update_id: str):
    """Get a single update by ID."""
    entry = update_store.get_by_id(update_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Update not found")
    return entry


@router.post("/crawl")
async def trigger_crawl():
    """Scrape iranmonitor.org + news sources, analyze with Claude, return pending updates."""
    from api.config import settings

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured — cannot analyze events",
        )

    try:
        from api.services.scraper import scrape_iranmonitor
        from api.services.analyzer import analyze_events

        # Scrape
        events = await scrape_iranmonitor(
            seen_hashes=update_store.get_seen_hashes(),
        )

        if not events:
            return {"message": "No new events found", "updates": []}

        # Analyze with Claude
        baseline = update_store.get_current_baseline()
        changes_by_event = await analyze_events(events, baseline)

        # Create pending updates
        from datetime import date

        new_updates: list[SituationUpdate] = []
        new_hashes: set[str] = set()

        for event, changes in zip(events, changes_by_event):
            update = SituationUpdate(
                id=update_store.make_id(),
                date=event.event_date or date.today().isoformat(),
                source=event.source,
                source_url=event.url,
                raw_text=event.title,
                summary=event.title,
                category=event.category,
                parameter_changes=[
                    ParameterChange(
                        parameter=c["parameter"],
                        category=c["category"],
                        delta=c.get("delta"),
                        absolute=c.get("absolute"),
                        reasoning=c["reasoning"],
                    )
                    for c in changes
                ],
                status="pending",
            )
            new_updates.append(update)
            new_hashes.add(event.content_hash)

        update_store.add_updates(new_updates)
        update_store.add_seen_hashes(new_hashes)

        return {
            "message": f"Found {len(new_updates)} new events",
            "updates": update_store.get_all(status="pending"),
        }

    except Exception as e:
        logger.exception("Crawl failed")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {e}")


@router.post("/manual")
def create_manual_update(req: ManualUpdateRequest):
    """Manually create a situation update (no scraping/analysis needed)."""
    update = SituationUpdate(
        id=update_store.make_id(),
        date=req.date,
        source=req.source,
        source_url=None,
        raw_text=req.raw_text or req.summary,
        summary=req.summary,
        parameter_changes=[
            ParameterChange(
                parameter=c["parameter"],
                category=c["category"],
                delta=c.get("delta"),
                absolute=c.get("absolute"),
                reasoning=c.get("reasoning", "Manual entry"),
            )
            for c in req.parameter_changes
        ],
        status="pending",
    )
    update_store.add_update(update)
    return update_store.get_by_id(update.id)


@router.post("/{update_id}/approve")
def approve_update(update_id: str):
    """Approve a pending update — its parameter changes will affect the baseline."""
    entry = update_store.approve(update_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Update not found")
    return entry


@router.post("/{update_id}/reject")
def reject_update(update_id: str):
    """Reject a pending update — it won't affect the baseline."""
    entry = update_store.reject(update_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Update not found")
    return entry


@router.delete("/{update_id}")
def delete_update(update_id: str):
    """Delete an update entirely."""
    if not update_store.delete(update_id):
        raise HTTPException(status_code=404, detail="Update not found")
    return {"deleted": True}

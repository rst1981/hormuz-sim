"""Named baseline snapshot endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.services.snapshot_store import snapshot_store

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


class SnapshotCreateRequest(BaseModel):
    name: str


@router.get("")
def list_snapshots():
    """List all saved baseline snapshots."""
    return snapshot_store.list_snapshots()


@router.post("")
def save_snapshot(req: SnapshotCreateRequest):
    """Save the current computed baseline as a named snapshot."""
    return snapshot_store.save_snapshot(req.name)


@router.get("/{snapshot_id}")
def get_snapshot(snapshot_id: str):
    """Get a single snapshot by ID."""
    s = snapshot_store.get_snapshot(snapshot_id)
    if not s:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return s


@router.delete("/{snapshot_id}")
def delete_snapshot(snapshot_id: str):
    """Delete a snapshot."""
    if not snapshot_store.delete_snapshot(snapshot_id):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"deleted": True}

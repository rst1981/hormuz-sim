"""Baseline snapshot store — save and load named baseline snapshots."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from api.services.update_store import update_store

SNAPSHOTS_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots"
SNAPSHOTS_FILE = SNAPSHOTS_DIR / "snapshots.json"


@dataclass
class BaselineSnapshot:
    id: str
    name: str
    date: str  # YYYY-MM-DD when snapshot was taken
    baseline: dict[str, dict[str, Any]]  # { ground_truth, oil_market, escalation }
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SnapshotStore:
    """Manages named baseline snapshots on disk."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict]:
        if not SNAPSHOTS_FILE.exists():
            return []
        with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, entries: list[dict]) -> None:
        with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def save_snapshot(self, name: str) -> dict:
        """Compute the current baseline and save it as a named snapshot."""
        baseline = update_store.get_current_baseline()
        snapshot = BaselineSnapshot(
            id=uuid.uuid4().hex[:12],
            name=name,
            date=date.today().isoformat(),
            baseline=baseline,
        )
        with self._lock:
            entries = self._read()
            entries.append(asdict(snapshot))
            self._write(entries)
        return asdict(snapshot)

    def ensure_original_baseline(self) -> None:
        """Save the original Day-18 baseline if no 'Original' snapshot exists yet."""
        entries = self._read()
        if any(s["name"].startswith("Original") for s in entries):
            return
        baseline = update_store.get_current_baseline()
        today = date.today().isoformat()
        snapshot = BaselineSnapshot(
            id=uuid.uuid4().hex[:12],
            name=f"Original — {today}",
            date=today,
            baseline=baseline,
        )
        with self._lock:
            entries = self._read()
            entries.insert(0, asdict(snapshot))
            self._write(entries)

    def list_snapshots(self) -> list[dict]:
        return self._read()

    def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        for s in self._read():
            if s["id"] == snapshot_id:
                return s
        return None

    def delete_snapshot(self, snapshot_id: str) -> bool:
        with self._lock:
            entries = self._read()
            new_entries = [s for s in entries if s["id"] != snapshot_id]
            if len(new_entries) == len(entries):
                return False
            self._write(new_entries)
            return True


# Singleton
snapshot_store = SnapshotStore()

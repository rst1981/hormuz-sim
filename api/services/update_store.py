"""Situation update store — JSON log CRUD and cumulative baseline computation."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

UPDATES_DIR = Path(__file__).resolve().parents[2] / "data" / "updates"
LOG_FILE = UPDATES_DIR / "log.json"
SEEN_HASHES_FILE = UPDATES_DIR / "seen_hashes.json"


@dataclass
class ParameterChange:
    parameter: str
    category: str  # "ground_truth" | "oil_market" | "escalation"
    reasoning: str
    delta: Optional[float] = None
    absolute: Optional[float] = None
    new_value: Optional[float] = None


@dataclass
class SituationUpdate:
    id: str
    date: str  # YYYY-MM-DD — the real-world date this update covers
    source: str
    raw_text: str
    summary: str
    parameter_changes: list[ParameterChange]
    status: str = "pending"  # "pending" | "applied" | "rejected"
    source_url: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _param_defaults() -> dict[str, dict[str, dict[str, Any]]]:
    """Load parameter defaults and ranges from the canonical source."""
    from api.routers.parameters import (
        ESCALATION_PARAMS,
        GROUND_TRUTH_PARAMS,
        OIL_MARKET_PARAMS,
    )

    result: dict[str, dict[str, dict[str, Any]]] = {
        "ground_truth": {},
        "oil_market": {},
        "escalation": {},
    }
    for p in GROUND_TRUTH_PARAMS:
        result["ground_truth"][p["name"]] = {
            "default": p["default"],
            "min": p["min"],
            "max": p["max"],
        }
    for p in OIL_MARKET_PARAMS:
        result["oil_market"][p["name"]] = {
            "default": p["default"],
            "min": p["min"],
            "max": p["max"],
        }
    for p in ESCALATION_PARAMS:
        result["escalation"][p["name"]] = {
            "default": p["default"],
            "min": p["min"],
            "max": p["max"],
        }
    return result


class UpdateStore:
    """Manages the situation update log on disk and computes cumulative baselines."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    # ── Persistence ──────────────────────────────────────────────

    def _read_log(self) -> list[dict]:
        if not LOG_FILE.exists():
            return []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_log(self, entries: list[dict]) -> None:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def _read_seen_hashes(self) -> set[str]:
        if not SEEN_HASHES_FILE.exists():
            return set()
        with open(SEEN_HASHES_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))

    def _write_seen_hashes(self, hashes: set[str]) -> None:
        with open(SEEN_HASHES_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(hashes), f)

    # ── CRUD ─────────────────────────────────────────────────────

    def add_update(self, update: SituationUpdate) -> SituationUpdate:
        with self._lock:
            entries = self._read_log()
            entries.append(asdict(update))
            self._write_log(entries)
        return update

    def add_updates(self, updates: list[SituationUpdate]) -> list[SituationUpdate]:
        with self._lock:
            entries = self._read_log()
            for u in updates:
                entries.append(asdict(u))
            self._write_log(entries)
        return updates

    def get_all(self, status: Optional[str] = None, date: Optional[str] = None) -> list[dict]:
        entries = self._read_log()
        if status:
            entries = [e for e in entries if e["status"] == status]
        if date:
            entries = [e for e in entries if e["date"] == date]
        return entries

    def get_by_id(self, update_id: str) -> Optional[dict]:
        for e in self._read_log():
            if e["id"] == update_id:
                return e
        return None

    def approve(self, update_id: str) -> Optional[dict]:
        with self._lock:
            entries = self._read_log()
            for e in entries:
                if e["id"] == update_id:
                    e["status"] = "applied"
                    e["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                    self._write_log(entries)
                    return e
        return None

    def reject(self, update_id: str) -> Optional[dict]:
        with self._lock:
            entries = self._read_log()
            for e in entries:
                if e["id"] == update_id:
                    e["status"] = "rejected"
                    e["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                    self._write_log(entries)
                    return e
        return None

    def delete(self, update_id: str) -> bool:
        with self._lock:
            entries = self._read_log()
            new_entries = [e for e in entries if e["id"] != update_id]
            if len(new_entries) == len(entries):
                return False
            self._write_log(new_entries)
            return True

    # ── Deduplication ────────────────────────────────────────────

    def get_seen_hashes(self) -> set[str]:
        with self._lock:
            return self._read_seen_hashes()

    def add_seen_hashes(self, hashes: set[str]) -> None:
        with self._lock:
            existing = self._read_seen_hashes()
            existing.update(hashes)
            self._write_seen_hashes(existing)

    # ── Baseline computation ─────────────────────────────────────

    def get_baseline_for_date(self, date: str) -> dict[str, dict[str, float]]:
        """Compute Day 18 defaults + all applied deltas up to and including `date`."""
        defaults = _param_defaults()

        # Start from defaults
        baseline: dict[str, dict[str, float]] = {
            cat: {name: info["default"] for name, info in params.items()}
            for cat, params in defaults.items()
        }

        # Apply updates chronologically up to the given date
        entries = self._read_log()
        applied = sorted(
            [e for e in entries if e["status"] == "applied" and e["date"] <= date],
            key=lambda e: e["created_at"],
        )

        for entry in applied:
            for change in entry["parameter_changes"]:
                cat = change["category"]
                param = change["parameter"]
                if cat not in baseline or param not in baseline[cat]:
                    continue

                meta = defaults[cat][param]
                if change.get("absolute") is not None:
                    val = change["absolute"]
                elif change.get("delta") is not None:
                    val = baseline[cat][param] + change["delta"]
                else:
                    continue

                # Clamp to valid range
                baseline[cat][param] = max(meta["min"], min(meta["max"], val))

        return baseline

    def get_current_baseline(self) -> dict[str, dict[str, float]]:
        """Baseline as of today."""
        from datetime import date

        return self.get_baseline_for_date(date.today().isoformat())

    def get_available_dates(self) -> list[str]:
        """Return sorted list of dates that have at least one applied update."""
        entries = self._read_log()
        dates = sorted({e["date"] for e in entries if e["status"] == "applied"})
        return dates

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def make_id() -> str:
        return uuid.uuid4().hex[:12]


# Singleton
update_store = UpdateStore()

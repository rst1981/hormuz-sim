"""Simulation manager — create, step, query, and destroy simulations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.config import settings
from src.simulation import Simulation, GroundTruth
from src_fearon_dia.simulation_b import create_simulation_b
from api.services.update_store import update_store
from api.services.snapshot_store import snapshot_store


class SimCapacityError(Exception):
    """Raised when maximum simultaneous simulations are exceeded."""
    pass


class SimNotFoundError(Exception):
    """Raised when a simulation ID is not found."""
    pass


class SimManager:
    """Manages the lifecycle of simulation instances."""

    def __init__(self) -> None:
        self._sims: dict[str, Simulation] = {}

    @property
    def count(self) -> int:
        return len(self._sims)

    def create(
        self,
        variant: str = "baseline",
        branch: Optional[str] = None,
        overrides: Optional[dict[str, Any]] = None,
        start_date: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> str:
        """Create a new simulation and return its ID."""
        if self.count >= settings.MAX_SIMS:
            raise SimCapacityError(
                f"Maximum of {settings.MAX_SIMS} simultaneous simulations reached"
            )

        sim_id = uuid.uuid4().hex[:12]

        # Compute start day from calendar date
        sim_date = start_date or date.today().isoformat()
        war_start = date.fromisoformat(settings.WAR_START_DATE)
        start_day = (date.fromisoformat(sim_date) - war_start).days + 1

        if branch == "b" or branch == "fearon_dia":
            sim = create_simulation_b(variant=variant)
        else:
            sim = Simulation()
            sim.setup(
                variant=variant,
                start_day=start_day,
                start_date=sim_date,
            )

        # Load baseline: from snapshot if provided, otherwise from update log
        if snapshot_id:
            snap = snapshot_store.get_snapshot(snapshot_id)
            if not snap:
                raise ValueError(f"Snapshot {snapshot_id} not found")
            baseline = snap["baseline"]
        else:
            baseline = update_store.get_baseline_for_date(sim_date)
        gt = sim.ground_truth
        for key, value in baseline.get("ground_truth", {}).items():
            if hasattr(gt, key):
                setattr(gt, key, value)

        # Apply oil market baseline
        om = sim.oil_market
        for key, value in baseline.get("oil_market", {}).items():
            if hasattr(om, key):
                setattr(om, key, value)

        # Apply escalation baseline
        esc = sim.escalation
        for key, value in baseline.get("escalation", {}).items():
            if hasattr(esc, key):
                setattr(esc, key, value)

        # Apply user overrides on top (highest priority)
        if overrides:
            for key, value in overrides.items():
                if hasattr(gt, key):
                    setattr(gt, key, value)

        self._sims[sim_id] = sim
        return sim_id

    def _get(self, sim_id: str) -> Simulation:
        if sim_id not in self._sims:
            raise SimNotFoundError(f"Simulation {sim_id} not found")
        return self._sims[sim_id]

    def step(self, sim_id: str) -> dict:
        """Advance simulation by one turn. Returns TurnReport dict."""
        sim = self._get(sim_id)
        report = sim.step()
        return report.to_dict()

    def run_to_completion(self, sim_id: str) -> dict:
        """Run simulation to termination. Returns final state dict."""
        sim = self._get(sim_id)
        outcome = sim.run(max_turns=sim.termination.max_turns, verbose=False)
        return {
            "outcome": outcome.value,
            "turns": sim.turn,
            "day": sim.day,
            "final_state": sim.to_dict(),
        }

    def get_state(self, sim_id: str) -> dict:
        """Return full simulation state."""
        sim = self._get(sim_id)
        return sim.to_dict()

    def get_turns(self, sim_id: str) -> list[dict]:
        """Return all TurnReport dicts."""
        sim = self._get(sim_id)
        return [r.to_dict() for r in sim.reports]

    def get_agents(self, sim_id: str) -> dict:
        """Return all agents' state."""
        sim = self._get(sim_id)
        return {aid: a.to_dict() for aid, a in sim.agents.items()}

    def get_agent(self, sim_id: str, agent_id: str) -> dict:
        """Return a single agent's state."""
        sim = self._get(sim_id)
        if agent_id not in sim.agents:
            raise SimNotFoundError(f"Agent {agent_id} not found in sim {sim_id}")
        return sim.agents[agent_id].to_dict()

    def get_escalation(self, sim_id: str) -> dict:
        """Return escalation state."""
        sim = self._get(sim_id)
        return sim.escalation.to_dict()

    def get_oil(self, sim_id: str) -> dict:
        """Return oil market state."""
        sim = self._get(sim_id)
        return sim.oil_market.to_dict()

    def get_termination(self, sim_id: str) -> dict:
        """Return termination state."""
        sim = self._get(sim_id)
        return sim.termination.to_dict()

    def destroy(self, sim_id: str) -> None:
        """Destroy a simulation and free resources."""
        if sim_id not in self._sims:
            raise SimNotFoundError(f"Simulation {sim_id} not found")
        del self._sims[sim_id]


# Singleton instance
sim_manager = SimManager()

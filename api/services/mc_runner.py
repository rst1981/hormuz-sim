"""Monte Carlo runner with async execution and streaming support."""

from __future__ import annotations

import asyncio
import uuid
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.config import settings
from src.simulation import Simulation
from src.termination import TerminationOutcome


class JobStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class MCJob:
    job_id: str
    variant: str
    n_runs: int
    max_turns: int
    seed: Optional[int]
    status: JobStatus = JobStatus.RUNNING
    completed: int = 0
    results: list[dict] = field(default_factory=list)
    cancelled: bool = False


def _run_single(variant: str, run_id: int, max_turns: int, seed: int) -> dict:
    """Run a single simulation to completion. Called in thread pool."""
    random.seed(seed)
    sim = Simulation()
    sim.setup(variant=variant, max_turns=max_turns)
    outcome = sim.run(max_turns=max_turns, verbose=False)
    return {
        "run_id": run_id,
        "variant": variant,
        "outcome": outcome.value,
        "turns": sim.turn,
        "final_oil_price": sim.oil_market.price,
        "final_escalation": sim.escalation.level,
        "final_metrics": sim.reports[-1].key_metrics if sim.reports else {},
        "seed": seed,
    }


class MCRunner:
    """Manages Monte Carlo jobs with async execution."""

    def __init__(self) -> None:
        self._jobs: dict[str, MCJob] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._listeners: dict[str, list[Callable]] = {}

    async def launch(
        self,
        variant: str,
        n_runs: int = 100,
        max_turns: int = 120,
        seed: Optional[int] = None,
    ) -> str:
        if len([j for j in self._jobs.values() if j.status == JobStatus.RUNNING]) >= settings.MAX_MC_JOBS:
            raise RuntimeError(f"Maximum of {settings.MAX_MC_JOBS} concurrent MC jobs")

        n_runs = min(n_runs, settings.MC_MAX_RUNS)
        job_id = uuid.uuid4().hex[:12]
        job = MCJob(
            job_id=job_id,
            variant=variant,
            n_runs=n_runs,
            max_turns=max_turns,
            seed=seed,
        )
        self._jobs[job_id] = job

        # Launch runs in background
        asyncio.create_task(self._execute_job(job))
        return job_id

    async def _execute_job(self, job: MCJob) -> None:
        loop = asyncio.get_event_loop()
        base_seed = job.seed if job.seed is not None else random.randint(0, 999999)

        for i in range(job.n_runs):
            if job.cancelled:
                job.status = JobStatus.CANCELLED
                return

            try:
                result = await loop.run_in_executor(
                    self._executor,
                    _run_single,
                    job.variant, i, job.max_turns, base_seed + i,
                )
                job.results.append(result)
                job.completed += 1

                # Notify WebSocket listeners
                for cb in self._listeners.get(job.job_id, []):
                    try:
                        await cb("run_complete", result, job.completed, job.n_runs)
                    except Exception:
                        pass

            except Exception:
                job.completed += 1  # count as attempted

        job.status = JobStatus.COMPLETED
        # Notify completion
        for cb in self._listeners.get(job.job_id, []):
            try:
                await cb("job_complete", self.get_results(job.job_id), job.completed, job.n_runs)
            except Exception:
                pass

    def get_status(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if not job:
            raise KeyError(f"MC job {job_id} not found")
        return {
            "status": job.status.value,
            "completed": job.completed,
            "total": job.n_runs,
        }

    def get_results(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if not job:
            raise KeyError(f"MC job {job_id} not found")

        outcomes: dict[str, int] = {}
        durations = []
        oil_prices = []
        escalations = []

        for r in job.results:
            o = r["outcome"]
            outcomes[o] = outcomes.get(o, 0) + 1
            durations.append(r["turns"])
            oil_prices.append(r["final_oil_price"])
            escalations.append(r["final_escalation"])

        n = max(len(job.results), 1)
        return {
            "variant": job.variant,
            "n_runs": len(job.results),
            "outcome_distribution": {k: v / n for k, v in outcomes.items()},
            "duration_stats": _stats(durations),
            "oil_price_stats": _stats(oil_prices),
            "escalation_stats": _stats(escalations),
            "runs": job.results,
        }

    def cancel(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.cancelled = True

    def add_listener(self, job_id: str, callback: Callable) -> None:
        self._listeners.setdefault(job_id, []).append(callback)

    def remove_listener(self, job_id: str, callback: Callable) -> None:
        listeners = self._listeners.get(job_id, [])
        if callback in listeners:
            listeners.remove(callback)


def _stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0, "min": 0, "max": 0, "std": 0, "median": 0}
    s = sorted(values)
    n = len(s)
    mean = sum(s) / n
    variance = sum((x - mean) ** 2 for x in s) / max(n - 1, 1)
    return {
        "mean": mean,
        "min": s[0],
        "max": s[-1],
        "std": variance ** 0.5,
        "median": s[n // 2],
    }


# Singleton
mc_runner = MCRunner()

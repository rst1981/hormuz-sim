"""Multi-variant comparison endpoints."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from api.schemas import ComparisonLaunchRequest, ComparisonLaunchResponse
from api.services.mc_runner import mc_runner

router = APIRouter(prefix="/api/compare", tags=["comparison"])

_comparison_jobs: dict[str, dict] = {}


@router.post("/launch", response_model=ComparisonLaunchResponse)
async def launch_comparison(req: ComparisonLaunchRequest):
    comp_id = uuid.uuid4().hex[:12]
    mc_jobs = {}
    for variant in req.variants:
        job_id = await mc_runner.launch(
            variant=variant,
            n_runs=req.n_runs,
            max_turns=req.max_turns,
            seed=req.seed,
        )
        mc_jobs[variant] = job_id

    _comparison_jobs[comp_id] = {
        "variants": req.variants,
        "mc_jobs": mc_jobs,
    }
    return ComparisonLaunchResponse(job_id=comp_id)


@router.get("/{comp_id}/results")
def get_comparison_results(comp_id: str):
    if comp_id not in _comparison_jobs:
        raise HTTPException(404, f"Comparison job {comp_id} not found")

    comp = _comparison_jobs[comp_id]
    results = {}
    all_done = True

    for variant, job_id in comp["mc_jobs"].items():
        try:
            status = mc_runner.get_status(job_id)
            if status["status"] != "completed":
                all_done = False
            results[variant] = mc_runner.get_results(job_id)
        except KeyError:
            results[variant] = None

    return {
        "status": "completed" if all_done else "running",
        "variants": comp["variants"],
        "results": results,
    }

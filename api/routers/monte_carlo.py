"""Monte Carlo launch/status/results endpoints."""

from fastapi import APIRouter, HTTPException

from api.schemas import MCLaunchRequest, MCLaunchResponse, MCStatusResponse
from api.services.mc_runner import mc_runner

router = APIRouter(prefix="/api/mc", tags=["monte_carlo"])


@router.post("/launch", response_model=MCLaunchResponse)
async def launch_mc(req: MCLaunchRequest):
    try:
        job_id = await mc_runner.launch(
            variant=req.variant,
            n_runs=req.n_runs,
            max_turns=req.max_turns,
            seed=req.seed,
        )
        return MCLaunchResponse(job_id=job_id)
    except RuntimeError as e:
        raise HTTPException(429, str(e))


@router.get("/{job_id}/status", response_model=MCStatusResponse)
def get_mc_status(job_id: str):
    try:
        return mc_runner.get_status(job_id)
    except KeyError:
        raise HTTPException(404, f"MC job {job_id} not found")


@router.get("/{job_id}/results")
def get_mc_results(job_id: str):
    try:
        return mc_runner.get_results(job_id)
    except KeyError:
        raise HTTPException(404, f"MC job {job_id} not found")


@router.post("/{job_id}/cancel")
def cancel_mc(job_id: str):
    mc_runner.cancel(job_id)
    return {"status": "cancelled"}

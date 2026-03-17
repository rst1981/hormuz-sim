"""Simulation CRUD endpoints."""

from fastapi import APIRouter, HTTPException

from api.schemas import SimCreateRequest, SimCreateResponse
from api.services.sim_manager import sim_manager, SimCapacityError, SimNotFoundError

router = APIRouter(prefix="/api/sim", tags=["simulation"])


@router.post("/create", response_model=SimCreateResponse)
def create_sim(req: SimCreateRequest):
    try:
        sim_id = sim_manager.create(
            variant=req.variant,
            branch=req.branch,
            overrides=req.overrides,
            start_date=req.start_date,
            snapshot_id=req.snapshot_id,
        )
        return SimCreateResponse(sim_id=sim_id)
    except SimCapacityError as e:
        raise HTTPException(429, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{sim_id}/step")
def step_sim(sim_id: str):
    try:
        return sim_manager.step(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")
    except RuntimeError as e:
        raise HTTPException(409, str(e))


@router.post("/{sim_id}/run")
def run_sim(sim_id: str):
    try:
        return sim_manager.run_to_completion(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/state")
def get_state(sim_id: str):
    try:
        return sim_manager.get_state(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/turns")
def get_turns(sim_id: str):
    try:
        return sim_manager.get_turns(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/agents")
def get_agents(sim_id: str):
    try:
        return sim_manager.get_agents(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/agents/{agent_id}")
def get_agent(sim_id: str, agent_id: str):
    try:
        return sim_manager.get_agent(sim_id, agent_id)
    except SimNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/{sim_id}/escalation")
def get_escalation(sim_id: str):
    try:
        return sim_manager.get_escalation(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/oil")
def get_oil(sim_id: str):
    try:
        return sim_manager.get_oil(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.get("/{sim_id}/termination")
def get_termination(sim_id: str):
    try:
        return sim_manager.get_termination(sim_id)
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")


@router.delete("/{sim_id}")
def destroy_sim(sim_id: str):
    try:
        sim_manager.destroy(sim_id)
        return {"status": "destroyed"}
    except SimNotFoundError:
        raise HTTPException(404, f"Simulation {sim_id} not found")

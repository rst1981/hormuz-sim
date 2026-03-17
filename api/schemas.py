"""Pydantic models for request/response validation."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class SimCreateRequest(BaseModel):
    variant: str = "baseline"
    branch: Optional[str] = None
    overrides: Optional[dict[str, Any]] = None
    start_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    snapshot_id: Optional[str] = None  # use a named baseline snapshot


class SimCreateResponse(BaseModel):
    sim_id: str


class SimStepResponse(BaseModel):
    turn: int
    day: int
    actions: list[dict[str, Any]]
    random_events: list[dict[str, str]]
    oil_price: float
    escalation_level: float
    escalation_phase: str
    termination_status: str
    trump_mode: str
    iran_dominant_faction: str
    key_metrics: dict[str, Any]
    miscalculation_events: list[str]


class SimRunResponse(BaseModel):
    outcome: str
    turns: int
    day: int
    final_state: dict[str, Any]


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

class MCLaunchRequest(BaseModel):
    variant: str = "baseline"
    n_runs: int = Field(default=100, ge=1)
    max_turns: int = Field(default=120, ge=1)
    seed: Optional[int] = None
    branch: Optional[str] = None


class MCLaunchResponse(BaseModel):
    job_id: str


class MCStatusResponse(BaseModel):
    status: str  # "running", "completed", "cancelled", "failed"
    completed: int
    total: int


class MCResultsResponse(BaseModel):
    variant: str
    n_runs: int
    outcome_distribution: dict[str, float]
    duration_stats: dict[str, float]
    oil_price_stats: dict[str, float]
    escalation_stats: dict[str, float]
    runs: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

class ComparisonLaunchRequest(BaseModel):
    variants: list[str]
    n_runs: int = Field(default=50, ge=1)
    max_turns: int = Field(default=120, ge=1)
    seed: Optional[int] = None


class ComparisonLaunchResponse(BaseModel):
    job_id: str


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

class CustomScenarioCreate(BaseModel):
    name: str
    description: str = ""
    base_variant: str = "baseline"
    ground_truth_overrides: dict[str, Any] = Field(default_factory=dict)
    oil_market_overrides: dict[str, Any] = Field(default_factory=dict)


class CustomScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    base_variant: str
    ground_truth_overrides: dict[str, Any]
    oil_market_overrides: dict[str, Any]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

class ParameterInfo(BaseModel):
    name: str
    type: str
    default: Any
    min: Optional[Any] = None
    max: Optional[Any] = None
    description: str = ""


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportCSVRequest(BaseModel):
    sim_id: str


# ---------------------------------------------------------------------------
# WebSocket messages
# ---------------------------------------------------------------------------

class WSSimCommand(BaseModel):
    type: str  # "step", "auto", "pause"
    interval_ms: int = 1000

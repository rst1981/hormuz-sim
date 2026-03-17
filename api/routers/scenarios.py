"""Scenario variant and custom scenario endpoints."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import CustomScenarioCreate, CustomScenarioResponse

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

VARIANTS = [
    {"id": "baseline", "name": "Baseline",
     "description": "Day 18 calibrated starting conditions — selective blockade, $98 oil, 7.5 escalation"},
    {"id": "houthi_activation", "name": "Houthi Activation",
     "description": "Houthis activate Red Sea attacks from turn 1 — dual chokepoint crisis"},
    {"id": "interceptor_crisis", "name": "Interceptor Crisis",
     "description": "Israeli interceptor stocks at 8% — near-depletion emergency"},
    {"id": "mojtaba_surfaces", "name": "Mojtaba Surfaces",
     "description": "Mojtaba Khamenei surfaces on turn 3 and calls for ceasefire"},
    {"id": "russian_confirmed", "name": "Russian Confirmed",
     "description": "Russian resupply confirmed at 95% — co-belligerency exposed"},
    {"id": "uprising_breakthrough", "name": "Uprising Breakthrough",
     "description": "Major city uprising overwhelms IRGC on turn 4"},
    {"id": "chinese_carrier", "name": "Chinese Carrier",
     "description": "China willing to guarantee at 70% — PLA-N carrier group deployment"},
    {"id": "strait_trap", "name": "Strait Trap",
     "description": "Strait of Hormuz in full trap mode — near-total disruption from turn 1"},
]

CUSTOM_DIR = Path(__file__).resolve().parents[2] / "data" / "custom_scenarios"


@router.get("/variants")
def list_variants():
    return VARIANTS


@router.get("/custom")
def list_custom():
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = []
    for f in CUSTOM_DIR.glob("*.json"):
        try:
            scenarios.append(json.loads(f.read_text()))
        except Exception:
            continue
    return scenarios


@router.post("/custom", response_model=CustomScenarioResponse)
def create_custom(req: CustomScenarioCreate):
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    scenario_id = uuid.uuid4().hex[:12]
    data = {
        "id": scenario_id,
        "name": req.name,
        "description": req.description,
        "base_variant": req.base_variant,
        "ground_truth_overrides": req.ground_truth_overrides,
        "oil_market_overrides": req.oil_market_overrides,
    }
    (CUSTOM_DIR / f"{scenario_id}.json").write_text(json.dumps(data, indent=2))
    return data


@router.get("/custom/{scenario_id}", response_model=CustomScenarioResponse)
def get_custom(scenario_id: str):
    path = CUSTOM_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Custom scenario {scenario_id} not found")
    return json.loads(path.read_text())


@router.put("/custom/{scenario_id}", response_model=CustomScenarioResponse)
def update_custom(scenario_id: str, req: CustomScenarioCreate):
    path = CUSTOM_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Custom scenario {scenario_id} not found")
    data = {
        "id": scenario_id,
        "name": req.name,
        "description": req.description,
        "base_variant": req.base_variant,
        "ground_truth_overrides": req.ground_truth_overrides,
        "oil_market_overrides": req.oil_market_overrides,
    }
    path.write_text(json.dumps(data, indent=2))
    return data


@router.delete("/custom/{scenario_id}")
def delete_custom(scenario_id: str):
    path = CUSTOM_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Custom scenario {scenario_id} not found")
    path.unlink()
    return {"status": "deleted"}

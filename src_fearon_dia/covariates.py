"""
Covariate extraction — bridge between the existing simulation state
and the Fearon/DIA duration models.

Extracts structured covariates from GroundTruth, agents, OilMarket,
EscalationState, and InfoEnvironment each turn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.agents import Agent, MilitaryAgent, PoliticalAgent, CompositeAgent, StochasticAgent
from src.beliefs import BeliefVar


@dataclass
class CovariateVector:
    """All covariates the Fearon and DIA models need for one turn."""

    turn: int = 0

    # --- Fearon covariates ---

    # Information asymmetry: average KL divergence between opposing agents
    info_asymmetry: float = 1.0

    # P(victory) for each side
    p_victory_iran: float = 0.5
    p_victory_israel: float = 0.5
    p_victory_us: float = 0.5

    # Accumulated costs (normalized 0-1)
    cost_iran: float = 0.0
    cost_coalition: float = 0.0

    # Bargaining range: set of deals both sides prefer to continued fighting
    bargaining_range: float = 0.0

    # Commitment problem severity (0 = credible deals, 1 = no trust)
    commitment_problem: float = 0.5

    # Information revelation rate (signals per turn, weighted by precision)
    info_revelation_rate: float = 0.0

    # --- DIA covariates ---

    # Conflict intensity (escalation level, 0-10)
    escalation_level: float = 5.0

    # Number of active parties
    n_active_parties: int = 0

    # External intervention pressure (sum of non-belligerent desires to end)
    external_pressure: float = 0.0

    # Geographic scope (0 = Gulf only, 1 = multi-theater)
    geographic_scope: float = 0.0

    # Nuclear dimension
    nuclear_progress: float = 0.0

    # Regime survival risk
    regime_survival: float = 0.5

    # Economic pressure (oil price deviation from baseline, normalized)
    economic_pressure: float = 0.0

    # --- Shared ---
    oil_price: float = 63.0
    strait_flow: float = 1.0
    iran_missiles: float = 0.5
    israel_interceptors: float = 0.25
    us_political_will: float = 0.5
    irgc_cohesion: float = 0.5
    china_guarantee: float = 0.4


def extract_covariates(
    agents: dict[str, Agent],
    world_state: dict,
    turn: int,
) -> CovariateVector:
    """
    Extract a CovariateVector from the current simulation state.

    This is the sole bridge between the existing agent-based simulation
    and the Fearon/DIA duration models.
    """
    cv = CovariateVector(turn=turn)

    # --- Information asymmetry ---
    # Average belief divergence between opposing agent pairs
    opposing = [
        ("irgc_military", "idf"),
        ("irgc_military", "pentagon"),
        ("iran_composite", "us_trump"),
    ]
    divergence_sum = 0.0
    divergence_count = 0
    for a_id, b_id in opposing:
        if a_id in agents and b_id in agents:
            a = agents[a_id]
            b = agents[b_id]
            div = a.beliefs.divergence(b.beliefs)
            # Normalize: KL divergence can be large; sigmoid-map to [0,1]
            normalized = 2.0 / (1.0 + math.exp(-div / 5.0)) - 1.0
            divergence_sum += normalized
            divergence_count += 1
    if divergence_count > 0:
        cv.info_asymmetry = divergence_sum / divergence_count
    else:
        # Decay info asymmetry naturally over time
        cv.info_asymmetry = max(0.1, 1.0 - turn * 0.01)

    # --- P(victory) ---
    if "irgc_military" in agents:
        cv.p_victory_iran = agents["irgc_military"].p_victory()
    if "idf" in agents:
        cv.p_victory_israel = agents["idf"].p_victory()
    if "pentagon" in agents:
        cv.p_victory_us = agents["pentagon"].p_victory()

    # --- Accumulated costs ---
    iran_cost = 0.0
    coalition_cost = 0.0
    for aid, agent in agents.items():
        if isinstance(agent, MilitaryAgent):
            if aid in ("irgc_military",):
                iran_cost += agent.accumulated_cost
            elif aid in ("idf", "pentagon"):
                coalition_cost += agent.accumulated_cost
        elif isinstance(agent, PoliticalAgent):
            if aid in ("iran_composite",):
                iran_cost += agent.current_pain * 0.5
            elif aid in ("us_trump", "israel"):
                coalition_cost += agent.current_pain * 0.3
    # Normalize costs to [0,1] range (cap at 5.0 as max expected cost)
    cv.cost_iran = min(1.0, iran_cost / 5.0)
    cv.cost_coalition = min(1.0, coalition_cost / 5.0)

    # --- Bargaining range ---
    # Fearon: bargaining range = space of mutually preferred deals
    # Wider when costs are high (more deals beat continued fighting)
    # Narrower when commitment problems are severe
    p_iran = cv.p_victory_iran
    p_coalition = max(cv.p_victory_israel, cv.p_victory_us)
    # If both think they'll win (p_a + p_b > 1), range is negative -> no deal
    # As costs accumulate, they're willing to accept worse deals
    cost_benefit = (cv.cost_iran + cv.cost_coalition) * 0.5
    raw_range = 1.0 - (p_iran + p_coalition) + cost_benefit
    cv.bargaining_range = max(0.0, min(1.0, raw_range))

    # --- Commitment problem ---
    china_guarantee = world_state.get("china_willing_to_guarantee", 0.4)
    regime_survival = world_state.get("regime_survival_index", 0.5)
    # Commitment problems worsen when: no guarantor, regime unstable (can't
    # trust a deal with a potentially collapsing government), power shifts
    cv.commitment_problem = max(0.0, min(1.0,
        0.3 * (1.0 - china_guarantee)           # no credible guarantor
        + 0.3 * (1.0 - regime_survival)         # regime instability
        + 0.2 * abs(p_iran - p_coalition)        # power asymmetry -> shifting
        + 0.2 * cv.info_asymmetry                # can't verify claims
    ))
    cv.china_guarantee = china_guarantee

    # --- Information revelation rate ---
    # Higher escalation = more fighting = more info revealed
    esc = world_state.get("escalation_level", 5.0)
    cv.info_revelation_rate = min(1.0, esc / 10.0 * 0.7 + 0.3 * (1.0 - cv.info_asymmetry))

    # --- DIA covariates ---
    cv.escalation_level = esc

    # Active parties
    cv.n_active_parties = sum(1 for a in agents.values() if a.active)

    # External pressure (mediators + non-belligerents wanting war to end)
    mediator_ids = ["turkey", "china", "gcc"]
    ext = 0.0
    for mid in mediator_ids:
        if mid in agents:
            ext += agents[mid].wants_war_to_end(world_state)
    cv.external_pressure = min(1.0, ext / 2.0)  # normalize

    # Geographic scope
    houthi_active = world_state.get("houthi_activation_prob", 0.25) > 0.5
    red_sea_disrupted = world_state.get("red_sea_flow", 1.0) < 0.7
    strait_disrupted = world_state.get("strait_flow", 1.0) < 0.7
    scope = 0.0
    if strait_disrupted:
        scope += 0.4
    if red_sea_disrupted or houthi_active:
        scope += 0.3
    if world_state.get("hezbollah_full_war_prob", 0.15) > 0.5:
        scope += 0.3
    cv.geographic_scope = min(1.0, scope)

    # Nuclear dimension
    cv.nuclear_progress = world_state.get("iran_nuclear_progress", 0.4)

    # Regime survival
    cv.regime_survival = regime_survival

    # Economic pressure (deviation from $63 baseline, normalized)
    oil = world_state.get("oil_price", 63.0)
    cv.oil_price = oil
    cv.economic_pressure = min(1.0, max(0.0, (oil - 63.0) / 100.0))

    # Shared state
    cv.strait_flow = world_state.get("strait_flow", 1.0)
    cv.iran_missiles = world_state.get("iran_missiles", 0.5)
    cv.israel_interceptors = world_state.get("israel_interceptor_fraction", 0.25)
    cv.us_political_will = world_state.get("us_political_will", 0.5)
    cv.irgc_cohesion = world_state.get("irgc_cohesion", 0.5)

    return cv

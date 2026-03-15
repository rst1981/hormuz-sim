"""
Escalation system — emergent from belief errors and miscalculation.

Escalation is NOT a score that agents increment. It is an emergent
property of the gap between what agents BELIEVE and what is TRUE,
combined with the actions those beliefs produce.

When Agent A misreads Agent B's intentions (noisy signals → wrong
beliefs → wrong actions), Agent B reads A's action through ITS
noisy channel and may over-react. This spiral is the engine of
escalation.

The system also implements Richardson-style dynamics: each side's
escalation rate is a function of the other's level plus grievance
minus fatigue.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .beliefs import BeliefState, BeliefVar
from .agents import Agent, Action, ActionType


# ---------------------------------------------------------------------------
# Action escalation weights
# ---------------------------------------------------------------------------

ACTION_ESCALATION_WEIGHT: dict[ActionType, float] = {
    # Military — high escalation potential
    ActionType.MISSILE_STRIKE: 0.8,
    ActionType.DRONE_STRIKE: 0.5,
    ActionType.AIR_STRIKE: 0.6,
    ActionType.NAVAL_ACTION: 0.5,
    ActionType.CYBER_ATTACK: 1.2,       # disproportionate — crosses a threshold
    ActionType.SPECIAL_OPERATION: 0.7,

    # Proxy
    ActionType.PROXY_ACTIVATE: 0.6,
    ActionType.PROXY_RESTRAIN: -0.3,     # de-escalatory

    # Strait
    ActionType.STRAIT_TIGHTEN: 0.4,
    ActionType.STRAIT_LOOSEN: -0.4,
    ActionType.STRAIT_TRAP: 1.5,         # major escalation

    # Diplomatic — generally de-escalatory
    ActionType.CEASEFIRE_OFFER: -0.6,
    ActionType.CEASEFIRE_REJECT: 0.3,
    ActionType.BACK_CHANNEL: -0.3,
    ActionType.PUBLIC_STATEMENT: 0.1,    # depends on content
    ActionType.DIPLOMATIC_DEMAND: 0.2,

    # Economic
    ActionType.SANCTIONS_TIGHTEN: 0.2,
    ActionType.OIL_PRODUCTION_CHANGE: 0.0,
    ActionType.RESERVE_RELEASE: -0.1,
    ActionType.REFLAG_SHIPS: -0.1,

    # Internal
    ActionType.INTERNAL_CRACKDOWN: 0.1,  # low external escalation
    ActionType.PROTEST_ESCALATE: 0.1,

    # Coalition
    ActionType.COALITION_REQUEST: 0.2,
    ActionType.COALITION_JOIN: 0.3,
    ActionType.COALITION_DECLINE: -0.1,

    # Posture
    ActionType.ESCALATE: 0.5,
    ActionType.DE_ESCALATE: -0.5,
    ActionType.HOLD: 0.0,

    # Info
    ActionType.SIGNAL_DISINFORMATION: 0.2,
}


@dataclass
class EscalationState:
    """
    Tracks the emergent escalation level of the conflict.

    Escalation is computed from:
    1. Action contributions (weighted by type and intensity)
    2. Miscalculation spirals (belief divergence → wrong actions)
    3. Richardson dynamics (reactive escalation)
    4. Fatigue dampening (accumulated cost reduces escalation pressure)
    """

    # Current escalation level (0-10)
    level: float = 7.5  # starting at Day 18 level from scenario

    # Richardson parameters per side
    # grievance: how much latent escalation pressure exists
    # reactivity: how strongly one side reacts to the other's escalation
    # fatigue: accumulated cost dampening escalation
    richardson_state: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "iran": {"grievance": 0.8, "reactivity": 0.6, "fatigue": 0.1},
            "us_israel": {"grievance": 0.5, "reactivity": 0.5, "fatigue": 0.05},
            "gulf": {"grievance": 0.3, "reactivity": 0.3, "fatigue": 0.2},
        }
    )

    # History for trend analysis
    history: list[float] = field(default_factory=lambda: [7.5])

    # Miscalculation events this turn
    miscalculation_events: list[str] = field(default_factory=list)

    def compute_action_contribution(
        self, actions: list[tuple[str, Action]]
    ) -> float:
        """
        Compute net escalation pressure from all actions this turn.
        """
        total = 0.0
        for agent_id, action in actions:
            weight = ACTION_ESCALATION_WEIGHT.get(action.action_type, 0.0)
            # Scale by intensity
            contribution = weight * action.intensity
            total += contribution
        return total

    def compute_miscalculation_pressure(
        self,
        agents: dict[str, Agent],
        ground_truth: dict[BeliefVar, float],
    ) -> float:
        """
        Miscalculation-driven escalation.

        When agents' beliefs diverge significantly from each other
        AND from ground truth, their actions are based on wrong
        assumptions. This produces surprises, over-reactions, and
        escalation spirals.

        Returns additional escalation pressure from miscalculation.
        """
        self.miscalculation_events = []
        pressure = 0.0

        # Key variables where miscalculation drives escalation
        critical_vars = [
            BeliefVar.IRAN_MISSILE_STOCKS,
            BeliefVar.ISRAEL_INTERCEPTOR_STOCKS,
            BeliefVar.US_POLITICAL_WILL,
            BeliefVar.REGIME_SURVIVAL_PROB,
            BeliefVar.HOUTHI_ACTIVATION_PROB,
            BeliefVar.IRAN_NUCLEAR_PROGRESS,
        ]

        for var in critical_vars:
            if var not in ground_truth:
                continue

            truth = ground_truth[var]

            for agent_id, agent in agents.items():
                belief_mean = agent.beliefs.mean(var)
                error = abs(belief_mean - truth)

                if error > 0.3:
                    # Significant miscalculation
                    pressure += error * 0.3
                    self.miscalculation_events.append(
                        f"{agent_id} misreads {var.value}: "
                        f"believes {belief_mean:.2f}, truth {truth:.2f}"
                    )

        # Cross-agent divergence — when two opponents read the same
        # situation differently, their actions surprise each other
        opposing_pairs = [
            ("irgc_military", "idf"),
            ("irgc_military", "us_trump"),
            ("iran_composite", "us_trump"),
        ]
        for a_id, b_id in opposing_pairs:
            if a_id not in agents or b_id not in agents:
                continue
            for var in critical_vars:
                a_mean = agents[a_id].beliefs.mean(var)
                b_mean = agents[b_id].beliefs.mean(var)
                div = abs(a_mean - b_mean)
                if div > 0.4:
                    pressure += div * 0.2
                    self.miscalculation_events.append(
                        f"{a_id} vs {b_id} diverge on {var.value}: "
                        f"{a_mean:.2f} vs {b_mean:.2f}"
                    )

        return pressure

    def compute_richardson(
        self,
        action_contributions: dict[str, float],
    ) -> float:
        """
        Richardson arms-race/escalation spiral dynamics.

        dx/dt = k*y + g - f*x

        Where:
        - x = this side's escalation pressure
        - y = other side's escalation (action contribution)
        - k = reactivity coefficient
        - g = grievance (latent escalation pressure)
        - f = fatigue dampening
        """
        net_pressure = 0.0

        for side, params in self.richardson_state.items():
            # Get the opposing side's action contribution
            if side == "iran":
                other_contribution = action_contributions.get("us_israel", 0)
            elif side == "us_israel":
                other_contribution = action_contributions.get("iran", 0)
            else:
                other_contribution = (
                    action_contributions.get("iran", 0)
                    + action_contributions.get("us_israel", 0)
                ) * 0.5

            dx = (
                params["reactivity"] * other_contribution
                + params["grievance"]
                - params["fatigue"] * self.level
            )

            net_pressure += dx

            # Fatigue increases over time (slowly)
            params["fatigue"] += 0.002

        return net_pressure

    def update(
        self,
        all_actions: list[tuple[str, Action]],
        agents: dict[str, Agent],
        ground_truth: dict[BeliefVar, float],
    ) -> float:
        """
        Update escalation level for this turn.

        Combines action contributions, miscalculation pressure,
        and Richardson dynamics.
        """
        # 1. Direct action contributions
        action_pressure = self.compute_action_contribution(all_actions)

        # 2. Miscalculation pressure
        misc_pressure = self.compute_miscalculation_pressure(
            agents, ground_truth
        )

        # 3. Richardson dynamics
        # Group actions by side for Richardson
        side_contributions: dict[str, float] = {}
        for agent_id, action in all_actions:
            side = self._agent_to_side(agent_id)
            weight = ACTION_ESCALATION_WEIGHT.get(action.action_type, 0.0)
            side_contributions[side] = (
                side_contributions.get(side, 0.0) + weight * action.intensity
            )
        richardson_pressure = self.compute_richardson(side_contributions)

        # 4. Combine with weights (scaled down — escalation moves slowly)
        delta = (
            action_pressure * 0.15
            + misc_pressure * 0.15
            + richardson_pressure * 0.1
        )

        # 5. Apply with heavy smoothing (escalation has high inertia)
        self.level = self.level * 0.85 + (self.level + delta) * 0.15
        self.level = max(0.0, min(10.0, self.level))

        self.history.append(self.level)
        return self.level

    def _agent_to_side(self, agent_id: str) -> str:
        """Map agent IDs to Richardson sides."""
        iran_side = {
            "irgc_military", "iran_composite", "iran_fm",
            "kh_pmf", "houthis", "hezbollah",
        }
        us_side = {
            "us_trump", "pentagon", "idf", "israel",
        }
        if agent_id in iran_side:
            return "iran"
        elif agent_id in us_side:
            return "us_israel"
        else:
            return "gulf"

    @property
    def trend(self) -> str:
        if len(self.history) < 3:
            return "insufficient_data"
        recent = self.history[-3:]
        if recent[-1] > recent[0] + 0.3:
            return "escalating"
        elif recent[-1] < recent[0] - 0.3:
            return "de-escalating"
        else:
            return "stable"

    @property
    def phase(self) -> str:
        """Current escalation phase."""
        if self.level < 3:
            return "diplomatic_tensions"
        elif self.level < 5:
            return "proxy_conflict"
        elif self.level < 7:
            return "direct_military"
        elif self.level < 9:
            return "multi_state_war"
        else:
            return "approaching_total_war"

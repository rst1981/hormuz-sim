"""
War termination system — hybrid Wittman convergence + Zartman ripeness.

Military actors: Wittman — war ends when p(victory) estimates converge.
Political actors: Zartman — war ends when pain exceeds threshold AND
                  a face-saving exit is visible.

Termination requires SUFFICIENT actors to agree. A single actor wanting
to stop doesn't end the war. The termination check evaluates whether
enough critical actors are aligned to produce a ceasefire or other
termination condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .agents import Agent, MilitaryAgent, PoliticalAgent, StochasticAgent, CompositeAgent


class TerminationOutcome(Enum):
    CONTINUING = "continuing"
    CEASEFIRE = "ceasefire"
    REGIME_COLLAPSE = "regime_collapse"
    ESCALATION_BEYOND_MODEL = "escalation_beyond_model"
    FROZEN_CONFLICT = "frozen_conflict"
    INTERCEPTOR_FAILURE = "interceptor_failure"
    TIME_LIMIT = "time_limit"


@dataclass
class TerminationState:
    """Tracks termination dynamics across the simulation."""

    outcome: TerminationOutcome = TerminationOutcome.CONTINUING

    # Wittman convergence tracking
    # Maps (agent_a, agent_b) -> history of p_victory divergence
    convergence_history: dict[tuple[str, str], list[float]] = field(
        default_factory=dict
    )

    # Zartman ripeness tracking
    ripeness_history: dict[str, list[float]] = field(default_factory=dict)

    # Consecutive low-escalation turns (for frozen conflict)
    low_escalation_turns: int = 0

    # Turn counter
    max_turns: int = 120

    def check_termination(
        self,
        agents: dict[str, Agent],
        world_state: dict,
        turn: int,
    ) -> TerminationOutcome:
        """
        Master termination check. Evaluates all termination conditions.
        """
        # 1. Time limit
        if turn >= self.max_turns:
            self.outcome = TerminationOutcome.TIME_LIMIT
            return self.outcome

        # 2. Escalation beyond model
        escalation = world_state.get("escalation_level", 0)
        if escalation >= 9.5:
            self.outcome = TerminationOutcome.ESCALATION_BEYOND_MODEL
            return self.outcome

        # 3. Israeli interceptor failure
        interceptor_stock = world_state.get("israel_interceptor_fraction", 1.0)
        if interceptor_stock <= 0.05:
            self.outcome = TerminationOutcome.INTERCEPTOR_FAILURE
            return self.outcome

        # 4. Regime collapse
        regime_survival = world_state.get("regime_survival_index", 1.0)
        if regime_survival <= 0.1:
            self.outcome = TerminationOutcome.REGIME_COLLAPSE
            return self.outcome

        # 5. Frozen conflict
        if escalation < 4.0:
            self.low_escalation_turns += 1
        else:
            self.low_escalation_turns = 0
        if self.low_escalation_turns >= 5:
            self.outcome = TerminationOutcome.FROZEN_CONFLICT
            return self.outcome

        # 6. Ceasefire — the complex one
        if self._check_ceasefire(agents, world_state, turn):
            self.outcome = TerminationOutcome.CEASEFIRE
            return self.outcome

        self.outcome = TerminationOutcome.CONTINUING
        return self.outcome

    def _check_ceasefire(
        self,
        agents: dict[str, Agent],
        world_state: dict,
        turn: int,
    ) -> bool:
        """
        Ceasefire requires alignment of multiple actors.

        Two parallel checks:
        1. Wittman: military actors' p(victory) estimates converge
           (they agree on the outcome, making continued fighting irrational)
        2. Zartman: political actors perceive mutual ripeness
           (enough pain + visible exit)

        Both conditions must be met for ceasefire.
        """
        military_converged = self._check_wittman(agents, world_state, turn)
        politically_ripe = self._check_zartman(agents, world_state, turn)

        # Either can trigger ceasefire, but political requires higher threshold
        if military_converged and politically_ripe:
            return True
        # Political ripeness alone can force ceasefire if strong enough
        if politically_ripe and self._political_pressure_overwhelming(agents, world_state):
            return True
        return False

    def _political_pressure_overwhelming(
        self, agents: dict[str, Agent], world_state: dict,
    ) -> bool:
        """Check if political pressure alone is strong enough to end the war."""
        # Count agents wanting war to end at high level
        high_desire_count = 0
        for agent_id, agent in agents.items():
            desire = agent.wants_war_to_end(world_state)
            if desire > 0.7:
                high_desire_count += 1
        # If majority of agents want out badly, political pressure overwhelms
        return high_desire_count >= len(agents) * 0.5

    def _check_wittman(
        self,
        agents: dict[str, Agent],
        world_state: dict,
        turn: int,
    ) -> bool:
        """
        Wittman convergence check.

        Wars end when opponents' p(victory) estimates converge —
        they agree on who's winning, making the outcome predictable
        and continued fighting wasteful.

        Check pairs of opposing military agents. If their p(victory)
        estimates are close AND both recognize it, convergence is
        achieved.
        """
        # Define opposing military pairs
        opposing_pairs = [
            ("irgc_military", "idf"),
            ("irgc_military", "pentagon"),
        ]

        convergence_threshold = 0.15  # p(victory) estimates within 15%
        convergence_turns_needed = 3  # sustained for 3 turns

        any_converged = False

        for pair in opposing_pairs:
            agent_a_id, agent_b_id = pair
            if agent_a_id not in agents or agent_b_id not in agents:
                continue

            agent_a = agents[agent_a_id]
            agent_b = agents[agent_b_id]

            # Get each side's p(victory)
            p_a = agent_a.p_victory()
            p_b = agent_b.p_victory()

            # Convergence = they agree on relative position
            divergence = abs(p_a + p_b - 1.0)

            pair_key = pair
            if pair_key not in self.convergence_history:
                self.convergence_history[pair_key] = []
            self.convergence_history[pair_key].append(divergence)

            # Check sustained convergence
            history = self.convergence_history[pair_key]
            if len(history) < convergence_turns_needed:
                continue

            recent = history[-convergence_turns_needed:]
            if not all(d < convergence_threshold for d in recent):
                continue

            # Also check that BOTH agents want the war to end
            desire_a = agent_a.wants_war_to_end(world_state)
            desire_b = agent_b.wants_war_to_end(world_state)

            if desire_a < 0.4 or desire_b < 0.4:
                continue

            any_converged = True

        return any_converged

    def _check_zartman(
        self,
        agents: dict[str, Agent],
        world_state: dict,
        turn: int,
    ) -> bool:
        """
        Zartman ripeness check.

        The war is ripe for termination when CRITICAL political actors
        perceive mutual hurting stalemate + a way out.

        Critical actors for ceasefire:
        - US (Trump) must be in DEAL or willing
        - Iran composite must have sufficient dove faction influence
        - At least one mediator (Turkey, China) must be active
        """
        # Required actors for ceasefire
        critical_ids = ["us_trump", "iran_composite"]
        mediator_ids = ["turkey", "china"]

        # Check critical actors' termination desire
        for agent_id in critical_ids:
            if agent_id not in agents:
                continue
            agent = agents[agent_id]
            desire = agent.wants_war_to_end(world_state)

            # Track ripeness history
            if agent_id not in self.ripeness_history:
                self.ripeness_history[agent_id] = []
            self.ripeness_history[agent_id].append(desire)

            # Use rolling average for stochastic agents (Trump)
            # — single-turn mode shouldn't block ceasefire if trend is ripe
            history = self.ripeness_history[agent_id]
            if len(history) >= 3:
                avg_desire = sum(history[-5:]) / min(5, len(history))
            else:
                avg_desire = desire

            # Must want war to end at threshold level (use average)
            if avg_desire < 0.35:
                return False

        # Check mediator availability
        mediator_active = False
        for med_id in mediator_ids:
            if med_id in agents:
                med = agents[med_id]
                # Mediator is active if they're pushing for ceasefire
                if med.wants_war_to_end(world_state) > 0.6:
                    mediator_active = True
                    break

        if not mediator_active:
            return False

        # Check that Israel isn't blocking
        # Israel can continue fighting even if US wants to stop —
        # but without US support, campaign degrades
        if "israel" in agents:
            israel = agents["israel"]
            israel_desire = israel.wants_war_to_end(world_state)
            us_support = world_state.get("us_support_to_israel", 1.0)

            # If Israel wants to continue AND still has US support → block
            if israel_desire < 0.3 and us_support > 0.5:
                return False

        return True

    def to_dict(self) -> dict:
        return {
            "outcome": self.outcome.value,
            "low_escalation_turns": self.low_escalation_turns,
            "max_turns": self.max_turns,
            "convergence_history": {
                f"{a}_vs_{b}": vals
                for (a, b), vals in self.convergence_history.items()
            },
            "ripeness_history": dict(self.ripeness_history),
        }

    def get_convergence_report(
        self, agents: dict[str, Agent]
    ) -> dict:
        """Generate a report on termination dynamics."""
        report = {
            "outcome": self.outcome.value,
            "low_escalation_turns": self.low_escalation_turns,
            "convergence": {},
            "ripeness": {},
        }

        for pair, history in self.convergence_history.items():
            report["convergence"][f"{pair[0]}_vs_{pair[1]}"] = {
                "current_divergence": history[-1] if history else None,
                "trend": (
                    "converging"
                    if len(history) >= 3 and history[-1] < history[-3]
                    else "diverging"
                ),
            }

        for agent_id, history in self.ripeness_history.items():
            report["ripeness"][agent_id] = {
                "current": history[-1] if history else None,
                "trend": (
                    "ripening"
                    if len(history) >= 3 and history[-1] > history[-3]
                    else "unripe"
                ),
            }

        return report

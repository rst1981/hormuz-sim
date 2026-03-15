"""
Duration-based termination — drop-in replacement for src/termination.py.

Implements the same check_termination(agents, world_state, turn) interface
as TerminationState, but uses the Fearon/DIA ensemble hazard rate to
determine WHEN the war ends, then a state-based classifier to determine
HOW it ends.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.agents import Agent
from src.termination import TerminationOutcome

from .covariates import extract_covariates, CovariateVector
from .ensemble import EnsembleState, EnsembleStrategy


@dataclass
class DurationTermination:
    """
    Duration-model-based termination engine.

    Drop-in replacement for TerminationState. Same method signatures,
    same TerminationOutcome enum. Different internals.

    Instead of checking Wittman convergence and Zartman ripeness,
    this engine:
      1. Extracts covariates from the simulation state
      2. Feeds them to the Fearon/DIA ensemble
      3. Rolls against the ensemble hazard rate
      4. If terminating, classifies the termination mode
    """

    ensemble: EnsembleState = field(default_factory=EnsembleState)
    outcome: TerminationOutcome = TerminationOutcome.CONTINUING
    max_turns: int = 120

    # Covariate history for analysis
    covariate_history: list[CovariateVector] = field(default_factory=list)

    # Hard thresholds (same as Branch A for comparability)
    escalation_ceiling: float = 9.5
    interceptor_floor: float = 0.05
    regime_collapse_floor: float = 0.1
    frozen_escalation_threshold: float = 4.0
    frozen_turns_needed: int = 5
    low_escalation_turns: int = 0

    def check_termination(
        self,
        agents: dict[str, Agent],
        world_state: dict,
        turn: int,
    ) -> TerminationOutcome:
        """
        Master termination check — matches TerminationState interface.

        Checks hard-threshold terminations first (these override the
        duration model), then consults the ensemble hazard rate for
        probabilistic termination.
        """
        # 1. Time limit (hard)
        if turn >= self.max_turns:
            self.outcome = TerminationOutcome.TIME_LIMIT
            return self.outcome

        # 2. Escalation beyond model (hard)
        escalation = world_state.get("escalation_level", 0)
        if escalation >= self.escalation_ceiling:
            self.outcome = TerminationOutcome.ESCALATION_BEYOND_MODEL
            return self.outcome

        # 3. Interceptor failure (hard)
        interceptor = world_state.get("israel_interceptor_fraction", 1.0)
        if interceptor <= self.interceptor_floor:
            self.outcome = TerminationOutcome.INTERCEPTOR_FAILURE
            return self.outcome

        # 4. Regime collapse (hard)
        regime = world_state.get("regime_survival_index", 1.0)
        if regime <= self.regime_collapse_floor:
            self.outcome = TerminationOutcome.REGIME_COLLAPSE
            return self.outcome

        # 5. Frozen conflict (hard)
        if escalation < self.frozen_escalation_threshold:
            self.low_escalation_turns += 1
        else:
            self.low_escalation_turns = 0
        if self.low_escalation_turns >= self.frozen_turns_needed:
            self.outcome = TerminationOutcome.FROZEN_CONFLICT
            return self.outcome

        # 6. Duration model termination (probabilistic)
        cv = extract_covariates(agents, world_state, turn)
        self.covariate_history.append(cv)

        # Get ensemble hazard rate
        hazard = self.ensemble.update(cv)

        # Roll against hazard rate
        if random.random() < hazard:
            # War ends — classify how
            self.outcome = self._classify_termination(cv, world_state, agents)
            return self.outcome

        self.outcome = TerminationOutcome.CONTINUING
        return self.outcome

    def _classify_termination(
        self,
        cv: CovariateVector,
        world_state: dict,
        agents: dict[str, Agent],
    ) -> TerminationOutcome:
        """
        When the duration model says the war ends, determine HOW.

        Uses the world state at the moment of termination to assign
        a termination mode. This mirrors Branch A's outcome taxonomy
        for comparability.
        """
        regime = cv.regime_survival
        escalation = cv.escalation_level
        interceptors = cv.israel_interceptors

        # Regime on the brink -> collapse
        if regime < 0.25:
            return TerminationOutcome.REGIME_COLLAPSE

        # Very high escalation at termination -> escalation beyond model
        if escalation > 8.0:
            return TerminationOutcome.ESCALATION_BEYOND_MODEL

        # Very low escalation -> frozen conflict
        if escalation < 3.0:
            return TerminationOutcome.FROZEN_CONFLICT

        # Interceptors nearly gone -> interceptor failure
        if interceptors < 0.1:
            return TerminationOutcome.INTERCEPTOR_FAILURE

        # Default: ceasefire (the most common negotiated termination)
        return TerminationOutcome.CEASEFIRE

    def get_convergence_report(self, agents: dict[str, Agent]) -> dict:
        """
        Generate a report compatible with Branch A's format.

        Provides ensemble diagnostics instead of Wittman/Zartman data.
        """
        report = self.ensemble.get_report()

        # Add Branch-A-compatible fields
        report["outcome"] = self.outcome.value
        report["low_escalation_turns"] = self.low_escalation_turns

        # Substitute convergence/ripeness with duration model equivalents
        report["convergence"] = {
            "fearon_info_asymmetry": {
                "current_divergence": report["fearon_report"].get("info_asymmetry", 1.0),
                "trend": report["fearon_report"].get("trend", "unknown"),
            }
        }
        report["ripeness"] = {
            "ensemble_hazard": {
                "current": report["ensemble_hazard"],
                "trend": (
                    "ripening"
                    if len(self.ensemble.ensemble_hazard_history) >= 3
                    and self.ensemble.ensemble_hazard_history[-1]
                    > self.ensemble.ensemble_hazard_history[-3]
                    else "unripe"
                ),
            }
        }

        return report

    def get_duration_report(self) -> dict:
        """Extended report with full duration model diagnostics."""
        n = len(self.ensemble.ensemble_hazard_history)
        report = {
            "ensemble": self.ensemble.get_report(),
            "survival_curve": [
                self.ensemble.survival_probability(t) for t in range(1, n + 1)
            ],
            "hazard_curve": {
                "ensemble": list(self.ensemble.ensemble_hazard_history),
                "fearon": list(self.ensemble.fearon_hazard_history),
                "dia": list(self.ensemble.dia_hazard_history),
            },
            "weight_evolution": list(self.ensemble.weight_history),
        }
        if self.covariate_history:
            last = self.covariate_history[-1]
            report["final_covariates"] = {
                "info_asymmetry": last.info_asymmetry,
                "bargaining_range": last.bargaining_range,
                "commitment_problem": last.commitment_problem,
                "cost_iran": last.cost_iran,
                "cost_coalition": last.cost_coalition,
                "escalation": last.escalation_level,
                "external_pressure": last.external_pressure,
                "economic_pressure": last.economic_pressure,
            }
        return report

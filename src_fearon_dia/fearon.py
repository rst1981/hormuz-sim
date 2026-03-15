"""
Fearon rationalist bargaining model for conflict duration.

Wars occur because of:
  (a) Information asymmetry about relative power and resolve
  (b) Commitment problems that prevent credible agreements

Duration depends on how quickly private information is revealed through
fighting, how fast costs accumulate, and whether commitment problems
can be overcome.

Reference: Fearon, J.D. (1995). "Rationalist Explanations for War."
           International Organization, 49(3), 379-414.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .covariates import CovariateVector


@dataclass
class FearonState:
    """Tracks Fearon model dynamics across turns."""

    # Information asymmetry trajectory
    initial_asymmetry: float = 1.0
    asymmetry_history: list[float] = field(default_factory=list)

    # Bargaining range trajectory
    range_history: list[float] = field(default_factory=list)

    # Commitment problem trajectory
    commitment_history: list[float] = field(default_factory=list)

    # Accumulated mutual costs
    mutual_cost_history: list[float] = field(default_factory=list)

    # Information revelation rate (how fast fighting reveals private info)
    revelation_history: list[float] = field(default_factory=list)

    # Hazard rate trajectory
    hazard_history: list[float] = field(default_factory=list)

    # Model parameters
    base_hazard: float = 0.005          # Per-turn baseline hazard
    info_decay_weight: float = 2.5      # How much info decay boosts hazard
    bargaining_weight: float = 2.0      # How much bargaining range boosts hazard
    commitment_weight: float = 1.5      # How much commitment problems reduce hazard
    cost_acceleration: float = 1.0      # How costs accelerate termination
    # Minimum asymmetry floor (some info is never fully revealed)
    asymmetry_floor: float = 0.15

    def update(self, cv: CovariateVector) -> None:
        """Update Fearon state with new covariates."""
        self.asymmetry_history.append(cv.info_asymmetry)
        self.range_history.append(cv.bargaining_range)
        self.commitment_history.append(cv.commitment_problem)
        self.mutual_cost_history.append(
            (cv.cost_iran + cv.cost_coalition) / 2.0
        )
        self.revelation_history.append(cv.info_revelation_rate)

    def hazard_rate(self, cv: CovariateVector) -> float:
        """
        Compute per-turn probability of conflict termination
        according to Fearon's rationalist framework.

        h(t) = h_base * f(info_revealed) * g(bargaining_range) * d(commitment)

        Where:
          f(.) = increasing in information revelation (as private info
                 is revealed, optimistic overestimates shrink)
          g(.) = increasing in bargaining range (wider range = more
                 deals both sides prefer to fighting)
          d(.) = decreasing in commitment problems (severe commitment
                 problems shrink effective bargaining range)

        The hazard rate is:
          - Low early (high info asymmetry, parties don't know each other's type)
          - Rising as fighting reveals information and costs accumulate
          - Potentially reduced if commitment problems grow (e.g., nuclear)
        """
        # Information factor: as asymmetry decays, war becomes "solvable"
        # info_revealed ranges from 0 (nothing learned) to 1 (full info)
        info_revealed = max(0.0, 1.0 - cv.info_asymmetry)
        # Nonlinear: marginal info has increasing returns (last bit matters most)
        f_info = info_revealed ** 0.7 * self.info_decay_weight

        # Bargaining range factor: wider range = more mutually acceptable deals
        g_range = cv.bargaining_range * self.bargaining_weight

        # Cost acceleration: accumulated costs expand the effective range
        mutual_cost = (cv.cost_iran + cv.cost_coalition) / 2.0
        cost_factor = 1.0 + mutual_cost * self.cost_acceleration

        # Commitment problem dampener: severe problems prevent agreement
        # even when bargaining range is wide
        d_commit = max(0.1, 1.0 - cv.commitment_problem * 0.8)

        # Compose the hazard rate
        h = self.base_hazard * (1.0 + f_info) * (1.0 + g_range) * cost_factor * d_commit

        # Time factor: very long wars have increasing pressure to end
        # (war-weariness beyond what costs capture)
        if cv.turn > 30:
            war_weariness = 1.0 + 0.01 * (cv.turn - 30)
            h *= war_weariness

        # Clamp to reasonable range
        h = max(0.001, min(0.25, h))

        self.hazard_history.append(h)
        return h

    def expected_remaining_duration(self, cv: CovariateVector) -> float:
        """
        Expected remaining turns, given current hazard rate.
        For a constant hazard h, E[T] = 1/h.
        """
        h = self.hazard_history[-1] if self.hazard_history else self.hazard_rate(cv)
        return 1.0 / max(0.001, h)

    def survival_probability(self, turn: int) -> float:
        """
        Cumulative survival probability: S(t) = product(1 - h(i)) for i in 1..t.
        """
        s = 1.0
        for h in self.hazard_history[:turn]:
            s *= (1.0 - h)
        return s

    def get_report(self) -> dict:
        """Diagnostic report on Fearon model state."""
        n = len(self.hazard_history)
        return {
            "current_hazard": self.hazard_history[-1] if n > 0 else 0.0,
            "cumulative_survival": self.survival_probability(n),
            "info_asymmetry": self.asymmetry_history[-1] if self.asymmetry_history else 1.0,
            "bargaining_range": self.range_history[-1] if self.range_history else 0.0,
            "commitment_problem": self.commitment_history[-1] if self.commitment_history else 0.5,
            "mutual_cost": self.mutual_cost_history[-1] if self.mutual_cost_history else 0.0,
            "info_revelation_rate": self.revelation_history[-1] if self.revelation_history else 0.0,
            "trend": (
                "accelerating"
                if n >= 3 and self.hazard_history[-1] > self.hazard_history[-3]
                else "stable_or_decelerating"
            ),
        }

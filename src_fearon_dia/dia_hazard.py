"""
DIA-style empirical hazard-rate model for conflict duration.

Uses historical conflict duration distributions (Weibull, log-normal)
calibrated from empirical data, adjusted via proportional hazards
covariates specific to the Hormuz scenario.

Historical analogues:
  1. Interstate limited war (Falklands, Gulf War): short, decisive
  2. Proxy/maritime hybrid (Tanker War 1987-88): longer, grinding
  3. Multi-party regional (various ME wars): high variance

References:
  - Bennett, D.S. & Stam, A.C. (1996). "The Duration of Interstate Wars,
    1816-1985." American Political Science Review.
  - Cunningham, D.E. (2006). "Veto Players and Civil War Duration."
    American Journal of Political Science.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .covariates import CovariateVector


@dataclass
class ConflictArchetype:
    """A historical conflict archetype with fitted duration distribution."""
    name: str
    distribution: str  # "weibull" or "lognormal"
    # Weibull params: h(t) = (k/lambda) * (t/lambda)^(k-1)
    # k > 1 means increasing hazard (war more likely to end as it continues)
    # k < 1 means decreasing hazard (the longer it lasts, the longer it lasts)
    shape: float = 1.5   # k (Weibull shape)
    scale: float = 60.0  # lambda (in turns; 1 turn = 2 days)
    # Log-normal params: h(t) derived from LN(mu, sigma)
    mu: float = 3.5
    sigma: float = 1.0
    # Weight in the mixture
    weight: float = 0.33

    def hazard(self, turn: int) -> float:
        """Per-turn hazard rate from this archetype's distribution."""
        t = max(1, turn)
        if self.distribution == "weibull":
            return self._weibull_hazard(t)
        elif self.distribution == "lognormal":
            return self._lognormal_hazard(t)
        return 0.01

    def _weibull_hazard(self, t: int) -> float:
        """
        Weibull hazard: h(t) = (k/lambda) * (t/lambda)^(k-1)
        """
        k = self.shape
        lam = self.scale
        h = (k / lam) * ((t / lam) ** (k - 1))
        return min(0.5, h)

    def _lognormal_hazard(self, t: int) -> float:
        """
        Log-normal hazard: h(t) = f(t) / S(t)
        where f is the PDF and S is the survival function.
        """
        ln_t = math.log(t) if t > 0 else 0
        # Standard normal PDF and CDF
        z = (ln_t - self.mu) / self.sigma

        # PDF of log-normal
        try:
            f = (1.0 / (t * self.sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * z * z)
        except (OverflowError, ValueError):
            f = 0.0

        # Survival function: S(t) = 1 - Phi(z)
        s = 0.5 * (1.0 - math.erf(z / math.sqrt(2)))
        s = max(1e-10, s)

        h = f / s
        return min(0.5, h)

    def survival(self, turn: int) -> float:
        """Cumulative survival probability at turn t."""
        if self.distribution == "weibull":
            t = max(1, turn)
            return math.exp(-((t / self.scale) ** self.shape))
        elif self.distribution == "lognormal":
            t = max(1, turn)
            z = (math.log(t) - self.mu) / self.sigma
            return 0.5 * (1.0 - math.erf(z / math.sqrt(2)))
        return 1.0


# Historical archetypes calibrated for this scenario
# Turns are in simulation units (1 turn = 2 days)
ARCHETYPES = [
    ConflictArchetype(
        name="interstate_limited",
        distribution="weibull",
        shape=2.0,          # Increasing hazard — wars get harder to sustain
        scale=25.0,          # ~50 days median
        weight=0.30,
    ),
    ConflictArchetype(
        name="proxy_maritime_hybrid",
        distribution="weibull",
        shape=1.3,           # Mildly increasing hazard
        scale=100.0,         # ~200 days median (Tanker War analog)
        weight=0.35,
    ),
    ConflictArchetype(
        name="multiparty_regional",
        distribution="lognormal",
        mu=3.8,              # exp(3.8) ~ 45 turns ~ 90 days median
        sigma=1.1,           # High variance — could be short or very long
        weight=0.35,
    ),
]


@dataclass
class DIAState:
    """Tracks DIA model dynamics across turns."""

    archetypes: list[ConflictArchetype] = field(default_factory=lambda: list(ARCHETYPES))

    # Cox proportional hazards coefficients
    # Positive = accelerates termination (shorter wars)
    # Negative = decelerates termination (longer wars)
    beta: dict[str, float] = field(default_factory=lambda: {
        "escalation_intensity": 0.15,    # Higher intensity -> shorter
        "n_parties":           -0.08,    # More parties -> longer
        "external_pressure":    0.25,    # More external pressure -> shorter
        "geographic_scope":    -0.12,    # Wider scope -> longer
        "nuclear_dimension":   -0.20,    # Nuclear risk -> longer (harder to settle)
        "regime_survival":      0.10,    # Collapsing regime -> shorter (decisive)
        "economic_pressure":    0.18,    # Oil price pain -> shorter
        "info_asymmetry":      -0.15,    # More asymmetry -> longer
    })

    # Parameter uncertainty (std dev for Monte Carlo sampling)
    beta_uncertainty: dict[str, float] = field(default_factory=lambda: {
        "escalation_intensity": 0.05,
        "n_parties":            0.03,
        "external_pressure":    0.08,
        "geographic_scope":     0.05,
        "nuclear_dimension":    0.08,
        "regime_survival":      0.04,
        "economic_pressure":    0.06,
        "info_asymmetry":       0.05,
    })

    # History tracking
    hazard_history: list[float] = field(default_factory=list)
    covariate_contributions: list[dict[str, float]] = field(default_factory=list)

    def _covariate_vector(self, cv: CovariateVector) -> dict[str, float]:
        """Map CovariateVector to the beta coefficient names."""
        return {
            "escalation_intensity": cv.escalation_level / 10.0,
            "n_parties": cv.n_active_parties / 18.0,  # normalize by max agents
            "external_pressure": cv.external_pressure,
            "geographic_scope": cv.geographic_scope,
            "nuclear_dimension": cv.nuclear_progress,
            "regime_survival": 1.0 - cv.regime_survival,  # invert: lower survival = higher pressure
            "economic_pressure": cv.economic_pressure,
            "info_asymmetry": cv.info_asymmetry,
        }

    def _proportional_hazards_multiplier(self, cv: CovariateVector) -> float:
        """
        Cox proportional hazards: exp(beta . x)

        This multiplier scales the base hazard from the archetype mixture
        based on scenario-specific covariates.
        """
        x = self._covariate_vector(cv)
        linear_predictor = sum(
            self.beta[k] * x.get(k, 0.0)
            for k in self.beta
        )
        # Track contributions for diagnostics
        contributions = {k: self.beta[k] * x.get(k, 0.0) for k in self.beta}
        self.covariate_contributions.append(contributions)

        return math.exp(linear_predictor)

    def hazard_rate(self, cv: CovariateVector) -> float:
        """
        Compute per-turn hazard rate from DIA empirical model.

        h_DIA(t) = [sum_j w_j * h_j(t)] * exp(beta . x)

        Where h_j(t) is the base hazard from archetype j, w_j is its weight,
        and exp(beta . x) is the proportional hazards adjustment.
        """
        turn = cv.turn

        # Base hazard from archetype mixture
        base_h = sum(
            arch.weight * arch.hazard(turn)
            for arch in self.archetypes
        )

        # Apply proportional hazards adjustment
        ph_mult = self._proportional_hazards_multiplier(cv)
        h = base_h * ph_mult

        # Clamp
        h = max(0.001, min(0.3, h))

        self.hazard_history.append(h)
        return h

    def survival_probability(self, turn: int) -> float:
        """Cumulative survival: S(t) = product(1 - h(i))."""
        s = 1.0
        for h in self.hazard_history[:turn]:
            s *= (1.0 - h)
        return s

    def base_survival(self, turn: int) -> float:
        """Base survival from archetype mixture (without covariates)."""
        return sum(
            arch.weight * arch.survival(turn)
            for arch in self.archetypes
        )

    def get_report(self) -> dict:
        """Diagnostic report on DIA model state."""
        n = len(self.hazard_history)
        report = {
            "current_hazard": self.hazard_history[-1] if n > 0 else 0.0,
            "cumulative_survival": self.survival_probability(n),
            "archetype_contributions": {
                arch.name: arch.hazard(n) * arch.weight
                for arch in self.archetypes
            },
        }
        if self.covariate_contributions:
            report["covariate_effects"] = dict(self.covariate_contributions[-1])
        return report

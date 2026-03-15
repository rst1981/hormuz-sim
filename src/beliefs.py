"""
Bayesian belief system with signal noise.

Each agent maintains probability distributions over key unknowns.
Beliefs update via Bayes' rule, but signal quality (precision, lag,
deliberate falsification) means agents can diverge from ground truth
and from each other — driving miscalculation and escalation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


def _digamma(x: float) -> float:
    """
    Digamma function approximation (Stirling series).
    psi(x) ~ ln(x) - 1/(2x) - 1/(12x^2) + 1/(120x^4) for large x.
    For small x, use recurrence: psi(x) = psi(x+1) - 1/x.
    """
    result = 0.0
    # Shift x up until x >= 6 for accurate Stirling
    while x < 6.0:
        result -= 1.0 / x
        x += 1.0
    # Stirling series
    result += math.log(x) - 1.0 / (2.0 * x)
    x2 = x * x
    result -= 1.0 / (12.0 * x2)
    result += 1.0 / (120.0 * x2 * x2)
    return result


# ---------------------------------------------------------------------------
# Core belief variables — the unknowns agents hold distributions over
# ---------------------------------------------------------------------------

class BeliefVar(Enum):
    """Key unknowns in the simulation that agents maintain beliefs about."""

    # Leadership / regime
    MOJTABA_ALIVE = "mojtaba_alive"                    # P(successor is alive)
    IRGC_COHESION = "irgc_cohesion"                    # 0-1 organizational integrity
    REGIME_SURVIVAL_PROB = "regime_survival_prob"       # P(Islamic Republic survives)

    # Military stocks
    IRAN_MISSILE_STOCKS = "iran_missile_stocks"        # estimated fraction remaining (0-1)
    IRAN_DRONE_STOCKS = "iran_drone_stocks"
    ISRAEL_INTERCEPTOR_STOCKS = "israel_interceptor_stocks"
    US_PGM_STOCKS = "us_pgm_stocks"                    # precision-guided munitions

    # Capability
    IRAN_NUCLEAR_PROGRESS = "iran_nuclear_progress"    # 0-1 toward breakout
    IRAN_CYBER_CAPABILITY = "iran_cyber_capability"    # 0-1 readiness
    FORDOW_DESTROYED = "fordow_destroyed"              # P(Fordow facility destroyed)
    KHARG_TERMINAL_DAMAGED = "kharg_terminal_damaged"  # P(oil terminal destroyed)

    # External support
    RUSSIA_SUPPLYING_IRAN = "russia_supplying_iran"    # P(active resupply)
    CHINA_WILLING_TO_GUARANTEE = "china_guarantee"     # P(China offers security guarantee)

    # Political will
    US_POLITICAL_WILL = "us_political_will"            # 0-1 commitment to continue
    TRUMP_DEAL_READINESS = "trump_deal_readiness"      # 0-1 how close to DEAL mode
    ISRAEL_WILL_TO_CONTINUE = "israel_will_continue"
    GULF_STATES_BREAKING_POINT = "gulf_breaking_point" # 0-1 proximity to breaking with US

    # Proxy
    HOUTHI_ACTIVATION_PROB = "houthi_activation"       # P(Red Sea attacks begin)
    HEZBOLLAH_FULL_WAR_PROB = "hezbollah_full_war"

    # Economic
    OIL_PRICE_EXPECTATION = "oil_price_expectation"    # expected $/barrel
    CEASEFIRE_PROBABILITY = "ceasefire_probability"     # market-implied P(ceasefire)

    # Uprising
    UPRISING_INTENSITY = "uprising_intensity"          # 0-1 current pressure on regime
    UPRISING_IRGC_DRAIN = "uprising_irgc_drain"        # fraction of IRGC tied down internally


# ---------------------------------------------------------------------------
# Beta distribution belief — natural for probability/proportion estimates
# ---------------------------------------------------------------------------

@dataclass
class BetaBelief:
    """
    A belief represented as a Beta distribution.

    Beta(alpha, beta) is the natural conjugate prior for binary/proportion
    unknowns. Mean = alpha/(alpha+beta). Concentration = alpha+beta
    (higher = more confident).

    This handles the bulk of our belief variables — probabilities and
    proportions on [0, 1].
    """

    alpha: float = 1.0  # successes + prior
    beta: float = 1.0   # failures + prior

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def concentration(self) -> float:
        """Total evidence. Higher = more confident."""
        return self.alpha + self.beta

    @property
    def variance(self) -> float:
        ab = self.alpha + self.beta
        return (self.alpha * self.beta) / (ab * ab * (ab + 1))

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)

    def sample(self) -> float:
        """Draw a sample from the belief distribution."""
        return random.betavariate(self.alpha, self.beta)

    def update(self, observation: float, signal_precision: float,
               signal_bias: float = 0.0) -> None:
        """
        Bayesian update given a noisy signal.

        Args:
            observation: The signal value (0-1 for proportion/probability).
            signal_precision: How informative the signal is (0 = pure noise,
                1 = perfect information). Maps to equivalent sample size.
            signal_bias: Systematic bias in the signal (-1 to 1). Positive
                bias inflates the observation, negative deflates it.
                Models deliberate disinformation.
        """
        # Apply bias — this is where disinformation enters
        biased_obs = max(0.0, min(1.0, observation + signal_bias))

        # Precision maps to equivalent sample size
        # precision=1.0 → n=10 (strong update)
        # precision=0.1 → n=1 (weak update)
        # precision=0.0 → no update
        if signal_precision <= 0:
            return

        n = signal_precision * 10.0

        # Beta-binomial update: treat observation as proportion of n "trials"
        successes = biased_obs * n
        failures = n - successes

        self.alpha += successes
        self.beta += failures

    def divergence_from(self, other: BetaBelief) -> float:
        """
        KL divergence from this belief to another.
        Measures how different two agents' beliefs are.
        High divergence = high potential for miscalculation.
        """
        # Approximate KL divergence for Beta distributions
        from math import lgamma
        try:
            kl = (lgamma(self.alpha + self.beta) - lgamma(self.alpha)
                  - lgamma(self.beta) - lgamma(other.alpha + other.beta)
                  + lgamma(other.alpha) + lgamma(other.beta)
                  + (self.alpha - other.alpha)
                  * (_digamma(self.alpha)
                     - _digamma(self.alpha + self.beta))
                  + (self.beta - other.beta)
                  * (_digamma(self.beta)
                     - _digamma(self.alpha + self.beta)))
            return max(0.0, kl)
        except (ValueError, OverflowError):
            return float('inf')

    def copy(self) -> BetaBelief:
        return BetaBelief(alpha=self.alpha, beta=self.beta)

    def __repr__(self) -> str:
        return f"Beta(μ={self.mean:.3f}, σ={self.std:.3f}, n={self.concentration:.1f})"


# ---------------------------------------------------------------------------
# Gaussian belief — for continuous unbounded variables (oil price, etc.)
# ---------------------------------------------------------------------------

@dataclass
class GaussianBelief:
    """
    A belief represented as a Gaussian distribution.

    Used for continuous variables like oil price expectations where
    the domain isn't bounded to [0,1].
    """

    mean: float = 0.0
    precision: float = 1.0  # 1/variance — precision parameterization

    @property
    def variance(self) -> float:
        return 1.0 / self.precision if self.precision > 0 else float('inf')

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)

    def sample(self) -> float:
        return random.gauss(self.mean, self.std)

    def update(self, observation: float, signal_precision: float,
               signal_bias: float = 0.0) -> None:
        """
        Gaussian-Gaussian conjugate update.

        Args:
            observation: Observed value.
            signal_precision: Precision of the signal (1/noise_variance).
            signal_bias: Systematic bias added to observation.
        """
        if signal_precision <= 0:
            return

        biased_obs = observation + signal_bias

        # Conjugate update: posterior precision = prior precision + signal precision
        new_precision = self.precision + signal_precision
        new_mean = ((self.precision * self.mean + signal_precision * biased_obs)
                    / new_precision)

        self.mean = new_mean
        self.precision = new_precision

    def divergence_from(self, other: GaussianBelief) -> float:
        """KL divergence from self to other."""
        if other.precision <= 0 or self.precision <= 0:
            return float('inf')
        v_self = self.variance
        v_other = other.variance
        return 0.5 * (math.log(v_other / v_self)
                      + v_self / v_other
                      + (self.mean - other.mean) ** 2 / v_other
                      - 1.0)

    def copy(self) -> GaussianBelief:
        return GaussianBelief(mean=self.mean, precision=self.precision)

    def __repr__(self) -> str:
        return f"N(μ={self.mean:.2f}, σ={self.std:.2f})"


# ---------------------------------------------------------------------------
# Belief state — an agent's complete set of beliefs
# ---------------------------------------------------------------------------

Belief = BetaBelief | GaussianBelief

# Which variables use Gaussian vs Beta
GAUSSIAN_VARS = {BeliefVar.OIL_PRICE_EXPECTATION}


@dataclass
class BeliefState:
    """
    An agent's complete belief state — probability distributions over
    all key unknowns.

    Agents see the world through their beliefs, not through ground truth.
    Two agents can hold radically different beliefs about the same variable
    based on their signal access, interpretation biases, and priors.
    """

    beliefs: dict[BeliefVar, Belief] = field(default_factory=dict)

    # Hard priors — beliefs the agent refuses to update past
    # Maps variable -> (min_mean, max_mean)
    # e.g., IRGC won't update REGIME_SURVIVAL_PROB below 0.3
    # (they can't psychologically accept regime death)
    hard_priors: dict[BeliefVar, tuple[float, float]] = field(
        default_factory=dict
    )

    def get(self, var: BeliefVar) -> Belief:
        if var not in self.beliefs:
            if var in GAUSSIAN_VARS:
                self.beliefs[var] = GaussianBelief()
            else:
                self.beliefs[var] = BetaBelief()
        return self.beliefs[var]

    def mean(self, var: BeliefVar) -> float:
        return self.get(var).mean

    def sample(self, var: BeliefVar) -> float:
        return self.get(var).sample()

    def update(self, var: BeliefVar, observation: float,
               signal_precision: float, signal_bias: float = 0.0) -> None:
        """
        Update a belief given a noisy signal, respecting hard priors.
        """
        belief = self.get(var)
        belief.update(observation, signal_precision, signal_bias)

        # Enforce hard priors — clamp the distribution
        if var in self.hard_priors:
            lo, hi = self.hard_priors[var]
            if isinstance(belief, BetaBelief):
                # If mean drifts outside hard prior range, nudge alpha/beta
                # to bring it back while preserving concentration
                if belief.mean < lo:
                    conc = belief.concentration
                    belief.alpha = lo * conc
                    belief.beta = (1 - lo) * conc
                elif belief.mean > hi:
                    conc = belief.concentration
                    belief.alpha = hi * conc
                    belief.beta = (1 - hi) * conc
            elif isinstance(belief, GaussianBelief):
                belief.mean = max(lo, min(hi, belief.mean))

    def divergence(self, other: BeliefState,
                   variables: Optional[list[BeliefVar]] = None) -> float:
        """
        Total KL divergence across specified variables (or all shared).
        Measures how different two agents' worldviews are.
        """
        if variables is None:
            variables = list(
                set(self.beliefs.keys()) & set(other.beliefs.keys())
            )
        total = 0.0
        for var in variables:
            if var in self.beliefs and var in other.beliefs:
                d = self.beliefs[var].divergence_from(other.beliefs[var])
                if math.isfinite(d):
                    total += d
        return total

    def p_victory_estimate(self) -> float:
        """
        Composite estimate of P(my side wins), derived from beliefs.
        Used for Wittman convergence calculation.

        This is a generic estimator — agents override with their own
        victory function that weights variables differently.
        """
        return self.mean(BeliefVar.REGIME_SURVIVAL_PROB)

    def copy(self) -> BeliefState:
        new = BeliefState(
            beliefs={k: v.copy() for k, v in self.beliefs.items()},
            hard_priors=dict(self.hard_priors),
        )
        return new

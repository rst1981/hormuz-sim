"""
Ensemble combiner — blends Fearon and DIA hazard rates.

Three strategies:
  1. Bayesian Model Averaging (BMA): weighted blend, weights updated
     based on predictive performance.
  2. Fearon-prior / DIA-update: use Fearon for structure, DIA for calibration.
  3. Regime-switching: weight Fearon early, DIA late.

Default: BMA.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .fearon import FearonState
from .dia_hazard import DIAState
from .covariates import CovariateVector


class EnsembleStrategy(Enum):
    BMA = "bma"
    FEARON_PRIOR_DIA_UPDATE = "fearon_prior_dia_update"
    REGIME_SWITCHING = "regime_switching"


@dataclass
class EnsembleState:
    """Manages the ensemble of Fearon and DIA duration models."""

    fearon: FearonState = field(default_factory=FearonState)
    dia: DIAState = field(default_factory=DIAState)
    strategy: EnsembleStrategy = EnsembleStrategy.BMA

    # BMA weights (sum to 1)
    w_fearon: float = 0.5
    w_dia: float = 0.5
    # Learning rate for BMA weight updates
    bma_learning_rate: float = 0.05

    # Regime-switching crossover point (turn at which DIA dominates)
    regime_crossover: int = 40

    # History
    ensemble_hazard_history: list[float] = field(default_factory=list)
    fearon_hazard_history: list[float] = field(default_factory=list)
    dia_hazard_history: list[float] = field(default_factory=list)
    weight_history: list[tuple[float, float]] = field(default_factory=list)

    # For BMA: track prediction accuracy
    _predicted_escalation: list[float] = field(default_factory=list)
    _actual_escalation: list[float] = field(default_factory=list)

    def update(self, cv: CovariateVector) -> float:
        """
        Update both models with new covariates and return ensemble hazard rate.
        """
        # Update Fearon state
        self.fearon.update(cv)

        # Compute individual hazard rates
        h_fearon = self.fearon.hazard_rate(cv)
        h_dia = self.dia.hazard_rate(cv)

        self.fearon_hazard_history.append(h_fearon)
        self.dia_hazard_history.append(h_dia)

        # Combine via selected strategy
        if self.strategy == EnsembleStrategy.BMA:
            h_ensemble = self._bma(h_fearon, h_dia, cv)
        elif self.strategy == EnsembleStrategy.FEARON_PRIOR_DIA_UPDATE:
            h_ensemble = self._fearon_prior_dia_update(h_fearon, h_dia, cv)
        elif self.strategy == EnsembleStrategy.REGIME_SWITCHING:
            h_ensemble = self._regime_switching(h_fearon, h_dia, cv)
        else:
            h_ensemble = 0.5 * h_fearon + 0.5 * h_dia

        h_ensemble = max(0.001, min(0.3, h_ensemble))
        self.ensemble_hazard_history.append(h_ensemble)
        self.weight_history.append((self.w_fearon, self.w_dia))

        return h_ensemble

    def _bma(
        self, h_fearon: float, h_dia: float, cv: CovariateVector
    ) -> float:
        """
        Bayesian Model Averaging.

        Weight models by their past predictive performance. The model
        whose implied dynamics better match observed escalation trajectory
        gets upweighted.

        We use escalation trajectory as the pseudo-observable for weight
        updating because we can't observe the "true" hazard — the war
        either ends or it doesn't. But escalation trajectory correlates
        with termination pressure, so a model whose hazard rate better
        tracks escalation changes is likely better calibrated.
        """
        # Track escalation for weight updating
        self._actual_escalation.append(cv.escalation_level)

        # Update weights based on prediction accuracy (after enough data)
        if len(self._actual_escalation) >= 3:
            # Each model's "predicted" escalation direction based on hazard trend
            # Higher hazard = predicting war nearing end = escalation should be lower
            # This is a crude proxy, but serviceable for BMA
            fearon_prediction_error = self._model_error(
                self.fearon_hazard_history, self._actual_escalation
            )
            dia_prediction_error = self._model_error(
                self.dia_hazard_history, self._actual_escalation
            )

            # Pseudo-Bayesian update: lower error -> higher weight
            # Use softmax-like updating
            max_err = max(fearon_prediction_error, dia_prediction_error, 0.01)
            fearon_score = math.exp(-fearon_prediction_error / max_err)
            dia_score = math.exp(-dia_prediction_error / max_err)
            total = fearon_score + dia_score

            target_w_fearon = fearon_score / total
            # Smooth update
            self.w_fearon += self.bma_learning_rate * (target_w_fearon - self.w_fearon)
            self.w_dia = 1.0 - self.w_fearon

        return self.w_fearon * h_fearon + self.w_dia * h_dia

    def _model_error(
        self, hazard_history: list[float], escalation_history: list[float]
    ) -> float:
        """
        Compute model error as directional disagreement between
        hazard changes and escalation changes.

        If hazard goes up (more likely to end) but escalation also goes up
        (conflict intensifying), that's a prediction error.
        """
        if len(hazard_history) < 3 or len(escalation_history) < 3:
            return 0.5

        error = 0.0
        n = min(len(hazard_history), len(escalation_history))
        lookback = min(5, n - 1)

        for i in range(n - lookback, n):
            if i < 1:
                continue
            dh = hazard_history[i] - hazard_history[i - 1]
            de = escalation_history[i] - escalation_history[i - 1]
            # Higher hazard should correspond to lower escalation (de-escalating)
            # so dh > 0 and de > 0 is disagreement
            if (dh > 0 and de > 0) or (dh < 0 and de < 0):
                error += abs(dh) + abs(de) * 0.1

        return error / max(1, lookback)

    def _fearon_prior_dia_update(
        self, h_fearon: float, h_dia: float, cv: CovariateVector
    ) -> float:
        """
        Use Fearon as a prior, DIA as a likelihood update.

        The Fearon model provides the theoretical structure (why does this
        war last this long?). The DIA model provides empirical calibration
        (historically, how long do wars like this last?).

        Combined via log-linear pooling:
          log(h_ensemble) = w_prior * log(h_fearon) + w_data * log(h_dia)
        """
        # Early: prior dominates; late: data dominates
        t = cv.turn
        w_prior = max(0.3, 0.7 - t * 0.005)
        w_data = 1.0 - w_prior

        # Log-linear pooling
        log_h = w_prior * math.log(max(1e-6, h_fearon)) + w_data * math.log(max(1e-6, h_dia))
        return math.exp(log_h)

    def _regime_switching(
        self, h_fearon: float, h_dia: float, cv: CovariateVector
    ) -> float:
        """
        Regime-switching: Fearon dominates early (information dynamics),
        DIA dominates late (empirical patterns take over).

        Smooth sigmoid transition at crossover point.
        """
        t = cv.turn
        # Sigmoid transition
        dia_weight = 1.0 / (1.0 + math.exp(-(t - self.regime_crossover) / 8.0))
        fearon_weight = 1.0 - dia_weight

        # Update tracked weights for reporting
        self.w_fearon = fearon_weight
        self.w_dia = dia_weight

        return fearon_weight * h_fearon + dia_weight * h_dia

    def survival_probability(self, turn: int) -> float:
        """Cumulative survival from ensemble hazard."""
        s = 1.0
        for h in self.ensemble_hazard_history[:turn]:
            s *= (1.0 - h)
        return s

    def expected_remaining_duration(self) -> float:
        """Expected remaining turns based on current hazard rate."""
        if not self.ensemble_hazard_history:
            return 60.0
        h = self.ensemble_hazard_history[-1]
        return 1.0 / max(0.001, h)

    def get_report(self) -> dict:
        """Comprehensive ensemble diagnostic report."""
        n = len(self.ensemble_hazard_history)
        return {
            "strategy": self.strategy.value,
            "ensemble_hazard": self.ensemble_hazard_history[-1] if n > 0 else 0.0,
            "fearon_hazard": self.fearon_hazard_history[-1] if self.fearon_hazard_history else 0.0,
            "dia_hazard": self.dia_hazard_history[-1] if self.dia_hazard_history else 0.0,
            "w_fearon": self.w_fearon,
            "w_dia": self.w_dia,
            "survival": self.survival_probability(n),
            "expected_remaining": self.expected_remaining_duration(),
            "fearon_report": self.fearon.get_report(),
            "dia_report": self.dia.get_report(),
        }

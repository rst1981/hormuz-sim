"""
Monte Carlo runner for Branch B (Fearon/DIA ensemble).

Extends the base Monte Carlo with duration-specific analytics:
  - Duration distribution with fitted parametric form
  - Survival curves with confidence bands
  - Hazard rate curves (Fearon, DIA, ensemble)
  - Information asymmetry and bargaining range evolution
  - Model weight evolution (BMA)
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Optional

from src.termination import TerminationOutcome

from .duration_termination import DurationTermination
from .ensemble import EnsembleStrategy
from .simulation_b import create_simulation_b


@dataclass
class RunResultB:
    """Result of a single simulation run with duration analytics."""
    run_id: int
    variant: str
    outcome: TerminationOutcome
    turns: int
    final_oil_price: float
    final_escalation: float
    final_metrics: dict
    seed: int

    # Duration model diagnostics
    final_hazard_fearon: float = 0.0
    final_hazard_dia: float = 0.0
    final_hazard_ensemble: float = 0.0
    final_survival: float = 0.0
    final_info_asymmetry: float = 1.0
    final_bargaining_range: float = 0.0
    final_commitment_problem: float = 0.5
    final_w_fearon: float = 0.5
    final_w_dia: float = 0.5

    # Full trajectories (for aggregation)
    hazard_trajectory: list[float] = field(default_factory=list)
    survival_trajectory: list[float] = field(default_factory=list)
    info_asymmetry_trajectory: list[float] = field(default_factory=list)
    bargaining_range_trajectory: list[float] = field(default_factory=list)


@dataclass
class MonteCarloResultB:
    """Aggregated results from N simulation runs with duration analytics."""
    variant: str
    n_runs: int
    ensemble_strategy: str = "bma"
    results: list[RunResultB] = field(default_factory=list)

    @property
    def outcome_distribution(self) -> dict[str, float]:
        counts: dict[str, int] = {}
        for r in self.results:
            key = r.outcome.value
            counts[key] = counts.get(key, 0) + 1
        return {k: v / self.n_runs for k, v in sorted(counts.items())}

    @property
    def duration_stats(self) -> dict[str, float]:
        turns = [r.turns for r in self.results]
        return {
            "mean": statistics.mean(turns),
            "median": statistics.median(turns),
            "std": statistics.stdev(turns) if len(turns) > 1 else 0,
            "min": min(turns),
            "max": max(turns),
            "p10": sorted(turns)[max(0, len(turns) // 10)],
            "p90": sorted(turns)[min(len(turns) - 1, 9 * len(turns) // 10)],
        }

    @property
    def oil_price_stats(self) -> dict[str, float]:
        prices = [r.final_oil_price for r in self.results]
        return {
            "mean": statistics.mean(prices),
            "median": statistics.median(prices),
            "std": statistics.stdev(prices) if len(prices) > 1 else 0,
            "min": min(prices),
            "max": max(prices),
        }

    @property
    def escalation_stats(self) -> dict[str, float]:
        levels = [r.final_escalation for r in self.results]
        return {
            "mean": statistics.mean(levels),
            "median": statistics.median(levels),
            "std": statistics.stdev(levels) if len(levels) > 1 else 0,
        }

    @property
    def hazard_stats(self) -> dict[str, dict[str, float]]:
        """Final hazard rate statistics for each model component."""
        return {
            "fearon": {
                "mean": statistics.mean([r.final_hazard_fearon for r in self.results]),
                "std": statistics.stdev([r.final_hazard_fearon for r in self.results])
                if len(self.results) > 1 else 0,
            },
            "dia": {
                "mean": statistics.mean([r.final_hazard_dia for r in self.results]),
                "std": statistics.stdev([r.final_hazard_dia for r in self.results])
                if len(self.results) > 1 else 0,
            },
            "ensemble": {
                "mean": statistics.mean([r.final_hazard_ensemble for r in self.results]),
                "std": statistics.stdev([r.final_hazard_ensemble for r in self.results])
                if len(self.results) > 1 else 0,
            },
        }

    @property
    def weight_stats(self) -> dict[str, float]:
        """Final BMA weights averaged across runs."""
        return {
            "w_fearon_mean": statistics.mean([r.final_w_fearon for r in self.results]),
            "w_dia_mean": statistics.mean([r.final_w_dia for r in self.results]),
        }

    @property
    def info_asymmetry_stats(self) -> dict[str, float]:
        vals = [r.final_info_asymmetry for r in self.results]
        return {
            "mean": statistics.mean(vals),
            "std": statistics.stdev(vals) if len(vals) > 1 else 0,
        }

    @property
    def bargaining_range_stats(self) -> dict[str, float]:
        vals = [r.final_bargaining_range for r in self.results]
        return {
            "mean": statistics.mean(vals),
            "std": statistics.stdev(vals) if len(vals) > 1 else 0,
        }

    def mean_trajectory(self, field_name: str) -> list[float]:
        """
        Compute mean trajectory across runs for a given field.
        Pads shorter runs with their final value.
        """
        max_len = max(len(getattr(r, field_name)) for r in self.results)
        if max_len == 0:
            return []

        means = []
        for t in range(max_len):
            vals = []
            for r in self.results:
                traj = getattr(r, field_name)
                if t < len(traj):
                    vals.append(traj[t])
                elif traj:
                    vals.append(traj[-1])  # pad with final value
            means.append(statistics.mean(vals) if vals else 0.0)
        return means

    def summary(self) -> str:
        lines = [
            f"=== Fearon/DIA Monte Carlo: {self.variant} ({self.n_runs} runs, {self.ensemble_strategy}) ===",
            "",
            "Outcome Distribution:",
        ]
        for outcome, frac in self.outcome_distribution.items():
            bar = "#" * int(frac * 40)
            lines.append(f"  {outcome:30s} {frac:6.1%} {bar}")

        dur = self.duration_stats
        lines.append(f"\nDuration (turns): mean={dur['mean']:.1f}, "
                     f"median={dur['median']:.0f}, "
                     f"range=[{dur['min']}-{dur['max']}], "
                     f"p10-p90=[{dur['p10']}-{dur['p90']}]")

        oil = self.oil_price_stats
        lines.append(f"Final oil price: mean=${oil['mean']:.1f}, "
                     f"median=${oil['median']:.1f}, "
                     f"range=[${oil['min']:.0f}-${oil['max']:.0f}]")

        esc = self.escalation_stats
        lines.append(f"Final escalation: mean={esc['mean']:.2f}, "
                     f"median={esc['median']:.2f}")

        # Duration-model-specific stats
        hs = self.hazard_stats
        lines.append(f"\nHazard rates (final): "
                     f"Fearon={hs['fearon']['mean']:.4f}, "
                     f"DIA={hs['dia']['mean']:.4f}, "
                     f"Ensemble={hs['ensemble']['mean']:.4f}")

        ws = self.weight_stats
        lines.append(f"BMA weights (final): "
                     f"w_fearon={ws['w_fearon_mean']:.3f}, "
                     f"w_dia={ws['w_dia_mean']:.3f}")

        ia = self.info_asymmetry_stats
        br = self.bargaining_range_stats
        lines.append(f"Info asymmetry (final): {ia['mean']:.3f} +/- {ia['std']:.3f}")
        lines.append(f"Bargaining range (final): {br['mean']:.3f} +/- {br['std']:.3f}")

        return "\n".join(lines)


def run_monte_carlo_b(
    variant: str = "baseline",
    n_runs: int = 100,
    max_turns: int = 120,
    base_seed: Optional[int] = None,
    ensemble_strategy: EnsembleStrategy = EnsembleStrategy.BMA,
    verbose: bool = False,
) -> MonteCarloResultB:
    """Run N simulations with the Fearon/DIA ensemble and aggregate."""
    mc = MonteCarloResultB(
        variant=variant, n_runs=n_runs,
        ensemble_strategy=ensemble_strategy.value,
    )

    for i in range(n_runs):
        seed = (base_seed + i) if base_seed is not None else random.randint(0, 2**32)
        random.seed(seed)

        sim = create_simulation_b(
            variant=variant,
            max_turns=max_turns,
            ensemble_strategy=ensemble_strategy,
        )
        outcome = sim.run(max_turns=max_turns, verbose=verbose)

        last_report = sim.reports[-1] if sim.reports else None
        term = sim.termination

        # Extract duration model diagnostics
        if isinstance(term, DurationTermination):
            ens = term.ensemble
            result = RunResultB(
                run_id=i,
                variant=variant,
                outcome=outcome,
                turns=sim.turn,
                final_oil_price=last_report.oil_price if last_report else 0,
                final_escalation=last_report.escalation_level if last_report else 0,
                final_metrics=dict(last_report.key_metrics) if last_report else {},
                seed=seed,
                final_hazard_fearon=ens.fearon_hazard_history[-1] if ens.fearon_hazard_history else 0,
                final_hazard_dia=ens.dia_hazard_history[-1] if ens.dia_hazard_history else 0,
                final_hazard_ensemble=ens.ensemble_hazard_history[-1] if ens.ensemble_hazard_history else 0,
                final_survival=ens.survival_probability(sim.turn),
                final_info_asymmetry=ens.fearon.asymmetry_history[-1] if ens.fearon.asymmetry_history else 1.0,
                final_bargaining_range=ens.fearon.range_history[-1] if ens.fearon.range_history else 0.0,
                final_commitment_problem=ens.fearon.commitment_history[-1] if ens.fearon.commitment_history else 0.5,
                final_w_fearon=ens.w_fearon,
                final_w_dia=ens.w_dia,
                hazard_trajectory=list(ens.ensemble_hazard_history),
                survival_trajectory=[ens.survival_probability(t) for t in range(1, sim.turn + 1)],
                info_asymmetry_trajectory=list(ens.fearon.asymmetry_history),
                bargaining_range_trajectory=list(ens.fearon.range_history),
            )
        else:
            result = RunResultB(
                run_id=i, variant=variant, outcome=outcome,
                turns=sim.turn,
                final_oil_price=last_report.oil_price if last_report else 0,
                final_escalation=last_report.escalation_level if last_report else 0,
                final_metrics=dict(last_report.key_metrics) if last_report else {},
                seed=seed,
            )

        mc.results.append(result)

        if not verbose and (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{n_runs} runs...")

    return mc


def compare_variants_b(
    variants: list[str],
    n_runs: int = 50,
    max_turns: int = 120,
    base_seed: int = 42,
    ensemble_strategy: EnsembleStrategy = EnsembleStrategy.BMA,
) -> dict[str, MonteCarloResultB]:
    """Run Monte Carlo across multiple scenario variants and compare."""
    results = {}
    for variant in variants:
        print(f"\n{'='*60}")
        print(f"Running variant: {variant} (Fearon/DIA {ensemble_strategy.value})")
        print(f"{'='*60}")
        mc = run_monte_carlo_b(
            variant=variant,
            n_runs=n_runs,
            max_turns=max_turns,
            base_seed=base_seed,
            ensemble_strategy=ensemble_strategy,
        )
        results[variant] = mc
        print(mc.summary())

    # Comparison summary
    print(f"\n{'='*60}")
    print(f"VARIANT COMPARISON (Fearon/DIA {ensemble_strategy.value})")
    print(f"{'='*60}")
    print(f"{'Variant':25s} {'Ceasefire':>10s} {'Collapse':>10s} {'Esc.Beyond':>10s} "
          f"{'Intcpt.Fail':>11s} {'Duration':>10s} {'Oil':>10s}")
    for variant, mc in results.items():
        dist = mc.outcome_distribution
        dur = mc.duration_stats
        oil = mc.oil_price_stats
        print(f"{variant:25s} "
              f"{dist.get('ceasefire', 0):10.1%} "
              f"{dist.get('regime_collapse', 0):10.1%} "
              f"{dist.get('escalation_beyond_model', 0):10.1%} "
              f"{dist.get('interceptor_failure', 0):11.1%} "
              f"{dur['mean']:10.1f} "
              f"${oil['mean']:9.1f}")

    return results

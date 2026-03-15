"""
Monte Carlo runner — run N simulations with probabilistic variance
and aggregate outcome distributions.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Optional

from .simulation import Simulation
from .termination import TerminationOutcome


@dataclass
class RunResult:
    """Result of a single simulation run."""
    run_id: int
    variant: str
    outcome: TerminationOutcome
    turns: int
    final_oil_price: float
    final_escalation: float
    final_metrics: dict
    seed: int


@dataclass
class MonteCarloResult:
    """Aggregated results from N simulation runs."""
    variant: str
    n_runs: int
    results: list[RunResult] = field(default_factory=list)

    @property
    def outcome_distribution(self) -> dict[str, float]:
        """Fraction of runs ending in each outcome."""
        counts: dict[str, int] = {}
        for r in self.results:
            key = r.outcome.value
            counts[key] = counts.get(key, 0) + 1
        return {k: v / self.n_runs for k, v in sorted(counts.items())}

    @property
    def duration_stats(self) -> dict[str, float]:
        """Statistics on conflict duration (in turns)."""
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

    def summary(self) -> str:
        lines = [
            f"=== Monte Carlo Results: {self.variant} ({self.n_runs} runs) ===",
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

        return "\n".join(lines)


def run_monte_carlo(
    variant: str = "baseline",
    n_runs: int = 100,
    max_turns: int = 120,
    base_seed: Optional[int] = None,
    verbose: bool = False,
) -> MonteCarloResult:
    """
    Run N simulations and aggregate results.

    Args:
        variant: Scenario variant to run.
        n_runs: Number of simulation runs.
        max_turns: Maximum turns per run.
        base_seed: Base random seed (run i uses base_seed + i).
        verbose: Print each run's progress.
    """
    mc = MonteCarloResult(variant=variant, n_runs=n_runs)

    for i in range(n_runs):
        seed = (base_seed + i) if base_seed is not None else random.randint(0, 2**32)
        random.seed(seed)

        sim = Simulation()
        sim.setup(variant=variant, max_turns=max_turns)
        outcome = sim.run(max_turns=max_turns, verbose=verbose)

        last_report = sim.reports[-1] if sim.reports else None
        result = RunResult(
            run_id=i,
            variant=variant,
            outcome=outcome,
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


def compare_variants(
    variants: list[str],
    n_runs: int = 50,
    max_turns: int = 120,
    base_seed: int = 42,
) -> dict[str, MonteCarloResult]:
    """Run Monte Carlo across multiple scenario variants and compare."""
    results = {}
    for variant in variants:
        print(f"\n{'='*60}")
        print(f"Running variant: {variant}")
        print(f"{'='*60}")
        mc = run_monte_carlo(
            variant=variant,
            n_runs=n_runs,
            max_turns=max_turns,
            base_seed=base_seed,
        )
        results[variant] = mc
        print(mc.summary())

    # Comparison summary
    print(f"\n{'='*60}")
    print("VARIANT COMPARISON")
    print(f"{'='*60}")
    print(f"{'Variant':25s} {'Ceasefire':>10s} {'Collapse':>10s} {'Esc.Beyond':>10s} "
          f"{'Duration':>10s} {'Oil':>10s}")
    for variant, mc in results.items():
        dist = mc.outcome_distribution
        dur = mc.duration_stats
        oil = mc.oil_price_stats
        print(f"{variant:25s} "
              f"{dist.get('ceasefire', 0):10.1%} "
              f"{dist.get('regime_collapse', 0):10.1%} "
              f"{dist.get('escalation_beyond_model', 0):10.1%} "
              f"{dur['mean']:10.1f} "
              f"${oil['mean']:9.1f}")

    return results

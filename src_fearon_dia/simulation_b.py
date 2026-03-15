"""
Simulation wrapper for Branch B (Fearon/DIA ensemble).

Uses composition: wraps the existing Simulation from src/ but replaces
the termination engine with DurationTermination. All agent behavior,
beliefs, signals, oil market, and escalation mechanics remain identical.

The only difference is HOW termination is decided:
  Branch A: Wittman convergence + Zartman ripeness (emergent from agent beliefs)
  Branch B: Fearon/DIA ensemble hazard rate (duration modeling)
"""

from __future__ import annotations

from src.simulation import Simulation
from src.termination import TerminationOutcome

from .duration_termination import DurationTermination
from .ensemble import EnsembleStrategy


def create_simulation_b(
    variant: str = "baseline",
    max_turns: int = 120,
    ensemble_strategy: EnsembleStrategy = EnsembleStrategy.BMA,
) -> Simulation:
    """
    Create a Simulation instance with the Fearon/DIA termination engine.

    Returns a standard Simulation object — the only modification is
    that sim.termination is a DurationTermination instead of TerminationState.
    """
    sim = Simulation()
    sim.setup(variant=variant, max_turns=max_turns)

    # Swap termination engine
    duration_term = DurationTermination(max_turns=max_turns)
    duration_term.ensemble.strategy = ensemble_strategy
    sim.termination = duration_term

    return sim


def run_single(
    variant: str = "baseline",
    max_turns: int = 120,
    ensemble_strategy: EnsembleStrategy = EnsembleStrategy.BMA,
    verbose: bool = True,
) -> tuple[Simulation, TerminationOutcome]:
    """Run a single simulation with the Fearon/DIA termination engine."""
    sim = create_simulation_b(variant, max_turns, ensemble_strategy)
    outcome = sim.run(max_turns=max_turns, verbose=verbose)
    return sim, outcome

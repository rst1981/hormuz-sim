"""
Hormuz Crisis Simulation — Entry Point

Usage:
    python run.py                          # Single baseline run (verbose)
    python run.py --variant houthi_activation
    python run.py --monte-carlo 100        # 100 Monte Carlo runs
    python run.py --compare                # Compare all variants
    python run.py --turns 60               # Limit to 60 turns
    python run.py --seed 42                # Reproducible run
    python run.py --csv output.csv         # Export metrics to CSV
"""

import argparse
import random
import sys

from src.simulation import Simulation
from src.monte_carlo import run_monte_carlo, compare_variants

VARIANTS = [
    "baseline",
    "houthi_activation",
    "interceptor_crisis",
    "mojtaba_surfaces",
    "russian_confirmed",
    "uprising_breakthrough",
    "chinese_carrier",
    "strait_trap",
]


def main():
    parser = argparse.ArgumentParser(description="Hormuz Crisis Simulation")
    parser.add_argument("--variant", default="baseline", choices=VARIANTS,
                       help="Scenario variant to run")
    parser.add_argument("--monte-carlo", type=int, default=0, metavar="N",
                       help="Run N Monte Carlo simulations")
    parser.add_argument("--compare", action="store_true",
                       help="Compare all variants")
    parser.add_argument("--turns", type=int, default=120,
                       help="Maximum turns per simulation")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducibility")
    parser.add_argument("--csv", type=str, default=None,
                       help="Export metrics to CSV file")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress per-turn output")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.compare:
        compare_variants(
            variants=VARIANTS,
            n_runs=args.monte_carlo or 50,
            max_turns=args.turns,
            base_seed=args.seed or 42,
        )
        return

    if args.monte_carlo > 0:
        mc = run_monte_carlo(
            variant=args.variant,
            n_runs=args.monte_carlo,
            max_turns=args.turns,
            base_seed=args.seed,
        )
        print(mc.summary())
        return

    # Single run
    sim = Simulation()
    sim.setup(variant=args.variant)

    print(f"Hormuz Crisis Simulation — Variant: {args.variant}")
    print(f"Starting from Day 18 of hostilities (March 15, 2026)")
    print(f"Each turn = ~2 days")
    print("=" * 60)
    print()

    outcome = sim.run(max_turns=args.turns, verbose=not args.quiet)

    print()
    print("=" * 60)
    print(f"SIMULATION ENDED: {outcome.value}")
    print(f"Duration: {sim.turn} turns ({sim.turn * 2} days, Day {18 + sim.turn * 2})")
    print(f"Final oil price: ${sim.oil_market.price:.1f}")
    print(f"Final escalation: {sim.escalation.level:.2f} ({sim.escalation.phase})")
    print()

    # Termination report
    term_report = sim.termination.get_convergence_report(sim.agents)
    print("Convergence Report:")
    for pair, data in term_report["convergence"].items():
        print(f"  {pair}: divergence={data['current_divergence']:.3f} ({data['trend']})")
    print("Ripeness Report:")
    for agent_id, data in term_report["ripeness"].items():
        print(f"  {agent_id}: ripeness={data['current']:.3f} ({data['trend']})")

    # CSV export
    if args.csv:
        csv_data = sim.get_metrics_csv()
        with open(args.csv, "w") as f:
            f.write(csv_data)
        print(f"\nMetrics exported to {args.csv}")


if __name__ == "__main__":
    main()

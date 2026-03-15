"""
Hormuz Crisis Simulation — Fearon/DIA Ensemble Branch Entry Point

Usage:
    python run_fearon_dia.py                          # Single baseline run
    python run_fearon_dia.py --variant houthi_activation
    python run_fearon_dia.py --monte-carlo 100        # 100 Monte Carlo runs
    python run_fearon_dia.py --compare                # Compare all variants
    python run_fearon_dia.py --ensemble regime_switching
    python run_fearon_dia.py --turns 60 --seed 42
    python run_fearon_dia.py --csv output.csv
"""

import argparse
import random
import sys

from src_fearon_dia.simulation_b import run_single
from src_fearon_dia.monte_carlo_b import run_monte_carlo_b, compare_variants_b
from src_fearon_dia.ensemble import EnsembleStrategy
from src_fearon_dia.duration_termination import DurationTermination

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

STRATEGIES = {
    "bma": EnsembleStrategy.BMA,
    "fearon_prior": EnsembleStrategy.FEARON_PRIOR_DIA_UPDATE,
    "regime_switching": EnsembleStrategy.REGIME_SWITCHING,
}


def main():
    parser = argparse.ArgumentParser(
        description="Hormuz Crisis Simulation — Fearon/DIA Ensemble Branch"
    )
    parser.add_argument("--variant", default="baseline", choices=VARIANTS,
                       help="Scenario variant to run")
    parser.add_argument("--monte-carlo", type=int, default=0, metavar="N",
                       help="Run N Monte Carlo simulations")
    parser.add_argument("--compare", action="store_true",
                       help="Compare all variants")
    parser.add_argument("--ensemble", default="bma", choices=list(STRATEGIES.keys()),
                       help="Ensemble strategy (default: bma)")
    parser.add_argument("--turns", type=int, default=120,
                       help="Maximum turns per simulation")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducibility")
    parser.add_argument("--csv", type=str, default=None,
                       help="Export metrics to CSV file")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress per-turn output")

    args = parser.parse_args()

    strategy = STRATEGIES[args.ensemble]

    if args.seed is not None:
        random.seed(args.seed)

    if args.compare:
        compare_variants_b(
            variants=VARIANTS,
            n_runs=args.monte_carlo or 50,
            max_turns=args.turns,
            base_seed=args.seed or 42,
            ensemble_strategy=strategy,
        )
        return

    if args.monte_carlo > 0:
        mc = run_monte_carlo_b(
            variant=args.variant,
            n_runs=args.monte_carlo,
            max_turns=args.turns,
            base_seed=args.seed,
            ensemble_strategy=strategy,
        )
        print(mc.summary())
        return

    # Single run
    sim, outcome = run_single(
        variant=args.variant,
        max_turns=args.turns,
        ensemble_strategy=strategy,
        verbose=not args.quiet,
    )

    print()
    print("=" * 60)
    print(f"SIMULATION ENDED: {outcome.value}")
    print(f"Duration: {sim.turn} turns ({sim.turn * 2} days, Day {18 + sim.turn * 2})")
    print(f"Final oil price: ${sim.oil_market.price:.1f}")
    print(f"Final escalation: {sim.escalation.level:.2f} ({sim.escalation.phase})")
    print()

    # Duration model report
    term = sim.termination
    if isinstance(term, DurationTermination):
        dr = term.get_duration_report()
        ens = dr["ensemble"]
        print("Duration Model Report:")
        print(f"  Strategy: {ens['strategy']}")
        print(f"  Final hazard: Fearon={ens['fearon_hazard']:.4f}, "
              f"DIA={ens['dia_hazard']:.4f}, Ensemble={ens['ensemble_hazard']:.4f}")
        print(f"  BMA weights: w_fearon={ens['w_fearon']:.3f}, w_dia={ens['w_dia']:.3f}")
        print(f"  Survival probability: {ens['survival']:.4f}")
        print(f"  Expected remaining: {ens['expected_remaining']:.1f} turns")

        fr = ens["fearon_report"]
        print(f"\n  Fearon state:")
        print(f"    Info asymmetry: {fr['info_asymmetry']:.3f}")
        print(f"    Bargaining range: {fr['bargaining_range']:.3f}")
        print(f"    Commitment problem: {fr['commitment_problem']:.3f}")
        print(f"    Mutual cost: {fr['mutual_cost']:.3f}")
        print(f"    Trend: {fr['trend']}")

        if "final_covariates" in dr:
            fc = dr["final_covariates"]
            print(f"\n  Final covariates:")
            for k, v in fc.items():
                print(f"    {k}: {v:.3f}")

    # Convergence report (Branch A compatible format)
    term_report = term.get_convergence_report(sim.agents)
    print("\nConvergence Report:")
    for pair, data in term_report.get("convergence", {}).items():
        print(f"  {pair}: divergence={data['current_divergence']:.3f} ({data['trend']})")
    print("Ripeness Report:")
    for agent_id, data in term_report.get("ripeness", {}).items():
        print(f"  {agent_id}: ripeness={data['current']:.3f} ({data['trend']})")

    # CSV export
    if args.csv:
        csv_data = sim.get_metrics_csv()
        with open(args.csv, "w") as f:
            f.write(csv_data)
        print(f"\nMetrics exported to {args.csv}")


if __name__ == "__main__":
    main()

# Hormuz Crisis Simulation

Multi-agent geopolitical simulation of a Strait of Hormuz crisis scenario (Operation Epic Fury), modeled from Day 18 of hostilities. Built with two independent analytical branches for conflict termination, enabling comparative analysis of theoretical frameworks.

## Scenario

An Israeli decapitation strike against Iran's Supreme Leader triggers a regional war involving 18 agents across military, political, proxy, and mediator roles. The simulation models:

- **18 BDI agents** with Bayesian belief updating over 22 key unknowns
- **Noisy signal environment** with 14 signal types, costly signaling, and per-agent information access
- **Nonlinear oil market** with selective Strait blockade, panic multipliers, and insurance collapse
- **Emergent escalation** via Richardson arms race dynamics and miscalculation pressure
- **Stochastic Trump** (4-mode Markov chain: RALLY, DEAL, ESCALATION, DISTRACTION)
- **Composite Iran** with 4 factional power bases and veto dynamics
- **8 scenario variants** across 800 Monte Carlo runs per branch

## Two Analytical Branches

### Wittman-Zartman (`src/`)

Termination emerges endogenously from agent dynamics:
- **Wittman convergence**: military actors' p(victory) estimates converge, making continued fighting irrational
- **Zartman ripeness**: political actors perceive mutual hurting stalemate + a face-saving exit

Baseline results: 57% interceptor failure, 21% ceasefire, 15% escalation beyond model

### Fearon/DIA Ensemble (`src_fearon_dia/`)

Duration modeled directly via hazard rates:
- **Fearon bargaining**: information asymmetry decay, bargaining range, commitment problems
- **DIA empirical**: Weibull/LogNormal archetype mixture with Cox proportional hazards
- **BMA ensemble**: Bayesian Model Averaging with adaptive weights

Baseline results: 53% interceptor failure, 24% regime collapse, 13% ceasefire

Both branches share identical agents, beliefs, signals, oil market, and escalation mechanics. They differ only in how they determine when and why the war ends.

## Usage

```bash
# Wittman-Zartman branch
python run.py                              # Single baseline run
python run.py --monte-carlo 100            # 100 Monte Carlo runs
python run.py --compare                    # Compare all 8 variants
python run.py --variant houthi_activation --seed 42

# Fearon/DIA branch
python run_fearon_dia.py                   # Single baseline run
python run_fearon_dia.py --monte-carlo 100
python run_fearon_dia.py --compare
python run_fearon_dia.py --ensemble regime_switching
```

Options: `--variant`, `--monte-carlo N`, `--compare`, `--turns`, `--seed`, `--csv`, `--quiet`

Fearon/DIA also supports: `--ensemble {bma, fearon_prior, regime_switching}`

## Scenario Variants

| Variant | Description |
|---|---|
| `baseline` | Day 18 status quo |
| `houthi_activation` | Houthis activate Red Sea attacks (most destabilizing) |
| `interceptor_crisis` | Israel starts at 8% interceptor stocks |
| `mojtaba_surfaces` | Khamenei successor emerges publicly |
| `russian_confirmed` | Russia confirmed supplying Iran |
| `uprising_breakthrough` | Major city uprising overwhelms IRGC |
| `chinese_carrier` | China willing to guarantee ceasefire |
| `strait_trap` | Iran activates selective strait blockade |

## Documents

| File | Description |
|---|---|
| `SCENARIO_DOCUMENT.pdf` | Complete scenario definition (1240 lines) |
| `FINDINGS_WITTMAN_ZARTMAN.pdf` | Wittman-Zartman branch findings with math appendix |
| `FINDINGS_FEARON_DIA.pdf` | Fearon/DIA branch findings with math appendix |
| `COMPARATIVE_ANALYSIS.pdf` | White paper comparing both analytical approaches |

## Project Structure

```
hormuz-sim/
  src/                        # Wittman-Zartman branch
    beliefs.py                #   Bayesian belief system (Beta/Gaussian)
    signals.py                #   Signal taxonomy and information environment
    agents.py                 #   18 BDI agents (Military, Political, Stochastic, Composite, Proxy)
    escalation.py             #   Richardson dynamics + miscalculation pressure
    termination.py            #   Wittman convergence + Zartman ripeness
    oil_market.py             #   Nonlinear oil market with selective blockade
    scenario.py               #   Agent instantiation with Day 18 calibration
    simulation.py             #   9-step turn loop + ground truth
    monte_carlo.py            #   Monte Carlo runner
  src_fearon_dia/             # Fearon/DIA branch
    covariates.py             #   Covariate extraction from sim state
    fearon.py                 #   Rationalist bargaining model
    dia_hazard.py             #   Empirical hazard-rate model (3 archetypes)
    ensemble.py               #   BMA / Fearon-prior / regime-switching
    duration_termination.py   #   Drop-in termination replacement
    simulation_b.py           #   Simulation wrapper (swaps termination only)
    monte_carlo_b.py          #   MC runner with duration analytics
  run.py                      # CLI entry point (Wittman-Zartman)
  run_fearon_dia.py           # CLI entry point (Fearon/DIA)
```

## Key Finding

Both branches agree that **interceptor depletion is the dominant outcome** (~53-57%), regardless of termination framework. Where they disagree reveals genuine theoretical uncertainty: the Wittman-Zartman branch finds ceasefire is possible through political coordination (21%), while the Fearon/DIA branch finds the conflict's information structure prevents rational bargaining (zero bargaining range), making regime collapse (24%) more likely than negotiated settlement (13%).

## Requirements

Python 3.10+ (standard library only, no external dependencies).

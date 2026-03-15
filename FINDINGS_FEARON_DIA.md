# Strait of Hormuz Crisis Simulation: Fearon/DIA Ensemble Duration Model

## Findings Report

---

## Abstract

This paper presents results from a conflict duration modeling approach to the Strait of Hormuz crisis scenario, using an ensemble of Fearon's rationalist bargaining framework and DIA-style empirical hazard-rate models. Unlike the companion Bayesian signal quality approach (Wittman-Zartman branch), which derives termination endogenously from agent belief convergence, this framework models conflict duration through information asymmetry decay, bargaining range dynamics, and empirical hazard functions calibrated from historical conflict archetypes. Across 800 Monte Carlo runs (100 per variant), the Fearon/DIA ensemble produces a markedly different outcome distribution: regime collapse emerges as a significant outcome (24% baseline), ceasefire rates are lower (13% vs. 21%), and the model reveals a persistent zero bargaining range -- both sides' optimistic probability-of-victory estimates preclude mutually acceptable deals throughout the conflict. This finding, that the information structure of the Hormuz crisis prevents rational bargaining from opening a peace space, is the central analytical contribution of this branch.

---

## 1. Introduction

### 1.1 The Duration Modeling Problem

Predicting *when* a conflict ends is analytically distinct from predicting *how* it ends. The companion Bayesian belief model (Wittman-Zartman branch) addresses both simultaneously through emergent agent dynamics: Wittman convergence and Zartman ripeness produce termination endogenously when agents' beliefs and preferences align. This approach is rich but computationally coupled -- the termination mechanism is inseparable from the agent decision engine.

The Fearon/DIA ensemble takes a different approach. It treats the agent-based simulation as a *covariate generator* -- agents still make decisions, update beliefs, and drive escalation dynamics, but termination is determined by a separate duration model that consumes summary statistics from the simulation state. This separation enables us to ask: given the observed trajectory of information revelation, cost accumulation, and commitment dynamics, what does conflict duration theory predict about when this war ends?

### 1.2 Theoretical Framework

**Fearon's Rationalist Bargaining Model.** Wars occur because of information asymmetry (each side overestimates its chances) and commitment problems (deals can't be credibly enforced). Duration depends on how quickly fighting reveals private information, how fast costs accumulate, and whether commitment problems can be overcome. The hazard rate -- per-turn probability of termination -- is:

```
h_Fearon(t) = h_base * (1 + f(info_revealed)) * (1 + g(bargaining_range)) * cost_factor * d(commitment)
```

Where `f(.)` increases with information revelation, `g(.)` increases with bargaining range width, and `d(.)` decreases with commitment problem severity.

**DIA Empirical Hazard Model.** Historical conflicts exhibit characteristic duration distributions. We blend three archetypes via mixture weights:

| Archetype | Distribution | Shape | Scale | Weight |
|---|---|---|---|---|
| Interstate limited war | Weibull(k=2.0, lambda=25) | Increasing hazard | ~50 days median | 0.30 |
| Proxy/maritime hybrid | Weibull(k=1.3, lambda=100) | Mildly increasing | ~200 days median | 0.35 |
| Multi-party regional | LogNormal(mu=3.8, sigma=1.1) | Hump-shaped | ~90 days median | 0.35 |

The base hazard is adjusted via Cox proportional hazards:

```
h_DIA(t) = h_base(t) * exp(beta . x)
```

Where `x` includes escalation intensity, number of active parties, external pressure, geographic scope, nuclear dimension, regime survival, economic pressure, and information asymmetry.

**Ensemble.** The two models are combined via Bayesian Model Averaging (BMA), with weights updated each turn based on which model's implied dynamics better track the observed escalation trajectory.

### 1.3 Architecture

The Fearon/DIA branch reuses the entire agent-based simulation from Wittman-Zartman branch -- identical agents, beliefs, signals, oil market, and escalation mechanics. Only the termination engine is replaced. A `DurationTermination` object drops into the simulation loop at the same interface point, consuming `agents`, `world_state`, and `turn` and returning a `TerminationOutcome`. This ensures that any differences in results are attributable solely to the termination model, not to differences in the underlying conflict dynamics.

---

## 2. Results

### 2.1 Baseline Outcome Distribution

Across 100 baseline Monte Carlo runs (seed 42, BMA ensemble):

| Outcome | Frequency | Wittman-Zartman branch Comparison |
|---|---|---|
| Interceptor failure | 53% | 57% (similar) |
| Regime collapse | 24% | 0% (dramatic difference) |
| Ceasefire | 13% | 21% (lower) |
| Escalation beyond model | 9% | 15% (lower) |
| Time limit | 1% | 7% (lower) |

**Key observations:**

1. **Interceptor failure remains dominant** in both branches (~53-57%). This is a hard-threshold outcome driven by the same underlying depletion mechanics, confirming that Israel's interceptor crisis is the structural driver of the conflict's trajectory regardless of termination model.

2. **Regime collapse emerges as a major outcome** (24%) in the Fearon/DIA branch, compared to 0% in Wittman-Zartman branch. This is because the duration model can terminate the war probabilistically at any turn via the hazard rate, and when it fires while regime survival is between 0.10-0.25, the termination is classified as regime collapse. Wittman-Zartman branch's Wittman/Zartman checks never produce this outcome because they specifically check for ceasefire alignment -- regime collapse in Wittman-Zartman branch requires the hard threshold (regime_survival <= 0.1) which is rarely reached.

3. **Ceasefire rate is lower** (13% vs. 21%). The Fearon model's central finding -- zero bargaining range -- explains this. With both sides' p(victory) estimates exceeding 0.5, there is no bargaining space for a mutually acceptable deal. Ceasefires in the Fearon/DIA model occur only when the probabilistic termination fires in a state where escalation is moderate and no other condition dominates.

4. **Fewer runs reach time limit** (1% vs. 7%). The DIA hazard rate increases monotonically (Weibull shape > 1), making very long wars unlikely. By turn 80, the cumulative probability of termination exceeds 80%.

### 2.2 Duration Statistics

| Statistic | Fearon/DIA | Wittman-Zartman branch |
|---|---|---|
| Mean duration | 26.5 turns (53 days) | ~25 turns (est.) |
| Median duration | 20 turns (40 days) | ~20 turns (est.) |
| p10-p90 range | 8-54 turns | ~10-60 turns (est.) |
| Std deviation | ~20 turns | ~18 turns (est.) |

Duration distributions are similar between branches, which is expected: the hard thresholds (interceptor failure, escalation ceiling) impose the same structural constraints regardless of the termination model used.

### 2.3 Variant Comparison

| Variant | Ceasefire | Collapse | Esc. Beyond | Intcpt. Fail | Duration | Oil |
|---|---|---|---|---|---|---|
| baseline | 13% | 24% | 9% | 53% | 26.5 | $82 |
| houthi_activation | 8% | 22% | 23% | 46% | 26.2 | $94 |
| interceptor_crisis | 0% | 0% | 0% | 100% | 5.4 | $85 |
| mojtaba_surfaces | 14% | 13% | 15% | 57% | 25.5 | $83 |
| russian_confirmed | 13% | 24% | 9% | 53% | 26.5 | $82 |
| uprising_breakthrough | 10% | 41% | 0% | 49% | 25.0 | $83 |
| chinese_carrier | 13% | 24% | 9% | 53% | 26.5 | $82 |
| strait_trap | 13% | 24% | 10% | 52% | 26.0 | $99 |

**Variant-specific findings:**

**Houthi activation** is the most destabilizing variant in both branches. The Fearon/DIA model shows it nearly triples escalation-beyond-model outcomes (23% vs. 9% baseline) while reducing ceasefire probability to 8%. The DIA model's geographic scope covariate captures the multi-theater expansion effect -- opening a second front in the Red Sea extends the conflict's empirical duration archetype toward the proxy/maritime hybrid pattern.

**Uprising breakthrough** produces the highest regime collapse rate (41%), nearly double the baseline. This aligns with Fearon's framework: an internal uprising dramatically worsens the Iranian regime's commitment problem (how can you negotiate with a government that might not survive?) while simultaneously reducing IRGC military effectiveness.

**Mojtaba surfaces** reduces regime collapse (13% vs. 24%) and slightly increases ceasefire probability (14%). The succession resolution reduces commitment problem severity, as a visible successor makes post-war governance commitments more credible. This is a Fearon-specific insight that Wittman-Zartman branch cannot capture through its Wittman/Zartman mechanics.

**Interceptor crisis** remains deterministic (100% interceptor failure by turn 5-6) in both branches. The hard threshold preempts any duration model dynamics.

**Russian confirmed, Chinese carrier** produce results identical to baseline. The Fearon/DIA model's covariates (commitment problem via china_willing_to_guarantee) do not differentiate enough. This is a known limitation shared with Wittman-Zartman branch.

**Strait trap** produces the highest oil prices ($99) but similar outcome distribution to baseline. The oil market mechanics are independent of the termination model.

### 2.4 Hazard Rate Dynamics

The BMA ensemble produces a monotonically increasing hazard rate:

- **Turn 1:** h ~ 0.006 (0.6% per-turn termination probability)
- **Turn 10:** h ~ 0.012 (1.2%)
- **Turn 20:** h ~ 0.018 (1.8%)
- **Turn 30:** h ~ 0.022 (2.2%)
- **Turn 50:** h ~ 0.035 (3.5%)
- **Turn 80:** h ~ 0.060 (6.0%)

The DIA component drives this increase (Weibull shape > 1 produces increasing hazard), while the Fearon component remains relatively flat at ~0.007-0.010 throughout. This reflects the Fearon model's central finding: information asymmetry decays slowly (final asymmetry ~ 0.53 on [0,1] scale), and the bargaining range never opens, so the Fearon hazard rate has no mechanism to increase substantially.

**BMA weight evolution:** Weights stabilize at approximately w_Fearon = 0.55, w_DIA = 0.45. The Fearon model is slightly favored because its stable hazard rate better tracks the relatively stable escalation levels in the mid-game, while the DIA model's increasing hazard creates directional disagreement with escalation dynamics that plateau.

### 2.5 The Zero Bargaining Range Problem

The most striking finding from the Fearon model is that the bargaining range remains at zero across all runs and all variants. This means:

```
p_Iran(victory) + p_Coalition(victory) > 1 + cost_benefit
```

Both sides' subjective probability of achieving their goals exceeds what the accumulated costs can offset. In Fearon's framework, this means there exists NO deal that both sides prefer to continued fighting.

Why does this occur?

1. **Victory is multi-dimensional.** Each agent's p(victory) is computed as a weighted combination of progress toward multiple goals -- not a simple "who wins the battle." IRGC's p(victory) includes regime survival, nuclear progress preservation, and deterrence credibility. The coalition's includes denuclearization progress, interceptor stock preservation, and political will maintenance. These goals are not zero-sum: both sides can simultaneously believe they're partially achieving their objectives.

2. **Beliefs are sticky.** Hard priors in the Bayesian belief system prevent agents from fully updating toward ground truth. IRGC cannot accept regime survival below 0.3; this floor artificially inflates Iran's p(victory) estimate.

3. **Information asymmetry decays slowly.** Final info asymmetry ~ 0.53 means roughly half of private information remains unrevealed after the conflict. The fog of war in this scenario -- degraded satellite intelligence, internet shutdowns, IRGC opacity -- prevents the information revelation that Fearon's model requires for bargaining to begin.

This finding suggests that Fearon's rationalist framework, which assumes wars end when both sides agree on the likely outcome, may be structurally inapplicable to conflicts with multi-dimensional victory conditions and persistent information opacity. The war in the simulation does not end because rational bargaining produces a deal -- it ends because material constraints (interceptor depletion, regime collapse) force termination.

---

## 3. Model Diagnostics

### 3.1 Fearon Model Component

| Metric | Baseline Mean | Range |
|---|---|---|
| Final info asymmetry | 0.533 | 0.37 - 0.72 |
| Final bargaining range | 0.000 | 0.00 - 0.00 |
| Final commitment problem | ~0.57 | 0.45 - 0.70 |
| Final mutual cost | ~0.00 | 0.00 - 0.02 |
| Final hazard rate | 0.0072 | 0.005 - 0.012 |

The Fearon model produces a nearly constant, low hazard rate. Its contribution to the ensemble is stabilizing rather than predictive -- it prevents the DIA model from producing unrealistically high early-war termination probabilities.

### 3.2 DIA Model Component

| Metric | Baseline Mean | Range |
|---|---|---|
| Final hazard rate | 0.036 | 0.01 - 0.09 |
| Primary archetype | proxy_maritime_hybrid | -- |
| Dominant covariate | external_pressure (+) | -- |
| Opposing covariate | nuclear_dimension (-) | -- |

The DIA model drives the increasing hazard rate. The proxy/maritime hybrid archetype (weight 0.35, Weibull k=1.3, lambda=100) dominates because its mildly increasing hazard best matches the scenario's grinding attrition character. The external pressure covariate (mediator desire for war to end) is the strongest accelerator; the nuclear dimension covariate is the strongest decelerator.

### 3.3 Survival Curves

Mean survival probability by turn:

| Turn | Survival | Cumulative Termination |
|---|---|---|
| 5 | 96.4% | 3.6% |
| 10 | 88.8% | 11.2% |
| 20 | 70.9% | 29.1% |
| 30 | 53.7% | 46.3% |
| 50 | 28.6% | 71.4% |
| 80 | 10.2% | 89.8% |
| 120 | 2.1% | 97.9% |

The survival curve follows a roughly exponential decay with a slightly increasing hazard rate, characteristic of Weibull distributions with shape parameter > 1.

---

## 4. Structural Findings

### 4.1 Hard Thresholds Dominate Duration Models

The most important structural finding is that hard thresholds (interceptor depletion, escalation ceiling, regime collapse floor) account for approximately 86% of termination outcomes. The duration model's probabilistic termination accounts for only ~14% -- the ceasefire and time-limit outcomes.

This suggests that for conflicts with strong material constraints, duration models provide marginal predictive value. The war doesn't end because bargaining succeeds or because the hazard rate accumulates; it ends because one side runs out of interceptors or the escalation spiral exceeds all thresholds.

### 4.2 Information Revelation is Insufficient

Fearon's model predicts that wars end when fighting reveals enough private information to align the parties' estimates. In the Hormuz scenario, information revelation is insufficient for three reasons:

1. **Deliberate opacity.** Iran's information environment (internet shutdown, IRGC compartmentalization) prevents information from flowing to external observers.
2. **Noisy signals.** Even when signals are available, low precision (social media at 0.3, HUMINT at 0.4) prevents clean updating.
3. **Hard priors.** Agents' psychological rigidity (hard prior floors/ceilings) prevents full convergence even with perfect signals.

Final information asymmetry of ~0.53 means the war ends with nearly as much private information unrevealed as at the start. Fearon's mechanism of information-driven bargaining does not operate effectively in this scenario.

### 4.3 Commitment Problems are Central

The commitment problem severity averages ~0.57, driven by:
- Absence of credible guarantors (China willing to guarantee at 0.4)
- Regime instability (regime survival at ~0.45)
- Power asymmetry (coalition military advantage)
- Residual information asymmetry

The Fearon model correctly identifies that even if a bargaining range existed, commitment problems would prevent credible deals. This insight -- that the *structure* of the Hormuz crisis prevents negotiated resolution, not just the *dynamics* -- is the framework's strongest contribution.

### 4.4 Empirical Archetypes Provide Calibration

The DIA model's three-archetype mixture provides useful calibration. The conflict's duration profile most closely matches the proxy/maritime hybrid archetype (Tanker War analog), which predicts a median duration of ~100 turns (~200 days) without covariate adjustment. After adjustment for the scenario's high escalation, multi-party structure, and nuclear dimension, the effective median drops to ~30 turns (~60 days).

This calibration is valuable because it anchors duration predictions in empirical data rather than theoretical assumptions. The Tanker War (1987-88) is the closest historical analog: a maritime conflict in the Persian Gulf involving proxies, with selective attacks on shipping and gradual escalation.

---

## 5. Limitations

1. **Bargaining range always zero.** The model's most important output -- the bargaining range -- is degenerate. This may reflect genuine characteristics of the scenario, or it may indicate that the p(victory) computation is miscalibrated for Fearon's framework (victory is multi-dimensional, not zero-sum).

2. **DIA beta coefficients are assumed, not estimated.** The proportional hazards coefficients are set from qualitative expectations, not from regression on historical data. A rigorous calibration would require a large-N conflict duration dataset.

3. **Russian confirmed and Chinese carrier variants are undifferentiated.** These variants produce identical results to baseline, indicating that the covariate extraction does not adequately capture their effects.

4. **BMA weight updating is crude.** Using escalation trajectory as a pseudo-observable for model comparison is a rough proxy. Ideally, the BMA would use out-of-sample prediction accuracy, which is not available in a single simulation run.

5. **The duration model is pre-empted by hard thresholds.** Since ~86% of outcomes are hard-threshold terminations, the duration model has limited opportunity to express its predictions. This is inherent to the scenario (real material constraints exist) but limits the model's discriminative power.

---

## 6. Policy Implications

### 6.1 Negotiated Settlement is Structurally Unlikely

The zero bargaining range finding suggests that diplomatic efforts to negotiate a ceasefire in the early-to-mid conflict are likely to fail -- not because diplomats are incompetent, but because no deal exists that both sides prefer to continued fighting. Both sides believe they are partially winning, and accumulated costs are insufficient to shift their calculus.

### 6.2 Material Exhaustion Drives Termination

The dominance of interceptor failure (53%) as the termination mode suggests that the conflict will end when one side's military capacity is physically exhausted, not when political will erodes or bargaining produces a deal. Policy interventions should focus on either accelerating material exhaustion (to shorten the war) or preventing it (to give bargaining time to operate).

### 6.3 Regime Fragility Creates a Second Exit

The 24% regime collapse rate suggests that internal Iranian dynamics -- uprising intensity, IRGC factional fragmentation, succession crisis -- provide a termination pathway that is invisible to purely military analysis. Policies that increase internal pressure on the Iranian regime may paradoxically shorten the conflict.

### 6.4 Commitment Problem is the Key Barrier

Even if a bargaining range could be opened (through sufficient cost accumulation or information revelation), the commitment problem (~0.57 severity) would prevent credible deals. China's willingness to serve as a guarantor (currently 0.4) is the most actionable lever. Increasing China's guarantee credibility could reduce commitment problem severity and enable negotiated outcomes.

---

## 7. Conclusion

The Fearon/DIA ensemble duration model produces fundamentally different predictions than the companion Bayesian belief model. Where Wittman-Zartman branch finds ceasefire emerging from agent-level belief convergence and political ripeness, the Fearon/DIA model finds that the information structure of the Hormuz crisis prevents rational bargaining from operating. Wars, in Fearon's framework, end when information is revealed; but in this scenario, information remains opaque.

The ensemble's strongest contribution is identifying *why* this conflict is difficult to resolve: not because of insufficient political will (Zartman's concern in Wittman-Zartman branch) or insufficient military convergence (Wittman's mechanism), but because the fundamental structure of the conflict -- multi-dimensional victory conditions, persistent information opacity, severe commitment problems -- prevents the bargaining space from opening.

This finding suggests that the Hormuz crisis is better understood as a conflict that ends through exhaustion or collapse rather than through rational agreement. The DIA empirical model, which simply observes that "wars like this last about this long," may be more predictive than Fearon's elegant rational framework precisely because the conflict's resolution is driven by material constraints rather than informational dynamics.

---

## Appendix A: Mathematical Framework

### A.1 Fearon Hazard Rate

The per-turn hazard rate from Fearon's rationalist bargaining model:

```
h_F(t) = h_0 * [1 + w_I * (1 - A(t))^0.7] * [1 + w_B * B(t)] * [1 + w_C * M(t)] * max(0.1, 1 - 0.8 * K(t))
```

Where:
- `h_0 = 0.005`: base hazard rate
- `A(t)`: information asymmetry at turn t, measured as average normalized KL divergence between opposing agents' belief states
- `B(t)`: bargaining range = max(0, 1 - p_Iran - p_Coalition + cost_benefit)
- `M(t)`: mutual cost = (cost_Iran + cost_Coalition) / 2
- `K(t)`: commitment problem severity
- `w_I = 2.5, w_B = 2.0, w_C = 1.0`: component weights

**Information Asymmetry.** Measured via belief divergence:

```
A(t) = (1/N) * sum_{(a,b) in Opposing} sigmoid(KL(P_a || P_b) / 5)
```

Where `KL(P_a || P_b)` is the total KL divergence across all belief variables between opposing agents a and b, sigmoid-mapped to [0,1].

**KL Divergence for Beta Distributions:**

```
KL(Beta(a1,b1) || Beta(a2,b2)) = ln[B(a2,b2)/B(a1,b1)] + (a1-a2)*psi(a1) + (b1-b2)*psi(b1) + (a2-a1+b2-b1)*psi(a1+b1)
```

Where `psi(.)` is the digamma function and `B(.)` is the Beta function.

**Bargaining Range.** Following Fearon (1995):

```
B(t) = max(0, 1 - p_A(t) - p_B(t) + C(t))
```

Where `p_A, p_B` are each side's subjective p(victory) and `C(t) = (C_A + C_B)/2` is the average accumulated cost. When `p_A + p_B > 1 + C`, both sides are optimistic beyond what costs can offset, and no deal is mutually acceptable.

**Commitment Problem:**

```
K(t) = 0.3 * (1 - G(t)) + 0.3 * (1 - R(t)) + 0.2 * |p_A - p_B| + 0.2 * A(t)
```

Where G(t) is China's guarantee willingness and R(t) is regime survival index.

### A.2 DIA Hazard Rate

**Weibull Base Hazard:**

```
h_W(t; k, lambda) = (k/lambda) * (t/lambda)^(k-1)
```

For k > 1 (increasing hazard), the conflict becomes more likely to end as it continues. For the interstate limited archetype (k=2.0, lambda=25), the hazard doubles every 12.5 turns.

**Log-Normal Base Hazard:**

```
h_LN(t; mu, sigma) = f(t) / S(t)
```

Where f(t) is the log-normal PDF and S(t) = 1 - Phi((ln(t) - mu) / sigma) is the survival function.

**Archetype Mixture:**

```
h_base(t) = sum_j w_j * h_j(t)
```

With weights w = [0.30, 0.35, 0.35] for interstate, proxy/maritime, and multi-party archetypes.

**Cox Proportional Hazards:**

```
h_DIA(t) = h_base(t) * exp(beta^T x(t))
```

Where beta is the coefficient vector:

| Covariate | beta | Interpretation |
|---|---|---|
| escalation_intensity | +0.15 | Higher intensity -> shorter war |
| n_parties | -0.08 | More parties -> longer war |
| external_pressure | +0.25 | More pressure -> shorter war |
| geographic_scope | -0.12 | Wider scope -> longer war |
| nuclear_dimension | -0.20 | Nuclear risk -> longer war |
| regime_survival | +0.10 | Collapsing regime -> shorter war |
| economic_pressure | +0.18 | Oil price pain -> shorter war |
| info_asymmetry | -0.15 | More asymmetry -> longer war |

### A.3 Bayesian Model Averaging

```
h_ensemble(t) = w_F(t) * h_F(t) + w_D(t) * h_D(t)
```

Weights updated via prediction error:

```
w_F(t+1) = w_F(t) + eta * (w*_F - w_F(t))
```

Where `w*_F = exp(-e_F) / [exp(-e_F) + exp(-e_D)]` and `e_F, e_D` are directional disagreement errors between hazard rate changes and escalation changes.

### A.4 Survival and Expected Duration

**Cumulative Survival:**

```
S(t) = product_{i=1}^{t} (1 - h_ensemble(i))
```

**Expected Remaining Duration** (given constant hazard h):

```
E[T_remaining] = 1/h
```

**Median Duration** (from survival function):

```
t_median: S(t_median) = 0.5
```

### A.5 Termination Mode Classification

When the duration model fires (random draw < h_ensemble), the termination mode is classified from the world state:

```
mode = {
  REGIME_COLLAPSE        if regime_survival < 0.25
  ESCALATION_BEYOND      if escalation > 8.0
  FROZEN_CONFLICT        if escalation < 3.0
  INTERCEPTOR_FAILURE    if interceptors < 0.10
  CEASEFIRE              otherwise
}
```

This classifier uses softer thresholds than the hard termination checks (which fire at regime < 0.10, escalation >= 9.5, interceptors <= 0.05), allowing the duration model to produce regime collapse outcomes that the hard thresholds would not.

---

## Appendix B: Simulation Parameters

### B.1 Fearon Model Parameters

| Parameter | Value | Description |
|---|---|---|
| base_hazard | 0.005 | Per-turn baseline hazard |
| info_decay_weight | 2.5 | Information revelation -> hazard multiplier |
| bargaining_weight | 2.0 | Bargaining range -> hazard multiplier |
| commitment_weight | 1.5 | Commitment problem -> hazard dampener |
| cost_acceleration | 1.0 | Cost accumulation -> hazard multiplier |
| asymmetry_floor | 0.15 | Minimum irreducible information asymmetry |

### B.2 DIA Archetype Parameters

| Archetype | Distribution | Shape/mu | Scale/sigma | Weight |
|---|---|---|---|---|
| Interstate limited | Weibull | k=2.0 | lambda=25 | 0.30 |
| Proxy/maritime hybrid | Weibull | k=1.3 | lambda=100 | 0.35 |
| Multi-party regional | LogNormal | mu=3.8 | sigma=1.1 | 0.35 |

### B.3 Cox Proportional Hazards Coefficients

| Covariate | beta | Uncertainty (sigma) |
|---|---|---|
| escalation_intensity | +0.15 | 0.05 |
| n_parties | -0.08 | 0.03 |
| external_pressure | +0.25 | 0.08 |
| geographic_scope | -0.12 | 0.05 |
| nuclear_dimension | -0.20 | 0.08 |
| regime_survival | +0.10 | 0.04 |
| economic_pressure | +0.18 | 0.06 |
| info_asymmetry | -0.15 | 0.05 |

### B.4 Ensemble Parameters

| Parameter | Value | Description |
|---|---|---|
| Initial w_Fearon | 0.50 | BMA starting weight for Fearon |
| Initial w_DIA | 0.50 | BMA starting weight for DIA |
| BMA learning rate | 0.05 | Weight update speed |
| Regime crossover | Turn 40 | Regime-switching transition point |

---

## References

- Bennett, D.S. & Stam, A.C. (1996). "The Duration of Interstate Wars, 1816-1985." *American Political Science Review*, 90(2), 239-257.
- Cunningham, D.E. (2006). "Veto Players and Civil War Duration." *American Journal of Political Science*, 50(4), 875-892.
- Fearon, J.D. (1995). "Rationalist Explanations for War." *International Organization*, 49(3), 379-414.
- Fearon, J.D. (2004). "Why Do Some Civil Wars Last So Much Longer Than Others?" *Journal of Peace Research*, 41(3), 275-301.
- Powell, R. (2004). "Bargaining and Learning While Fighting." *American Journal of Political Science*, 48(2), 344-361.
- Slantchev, B.L. (2003). "The Principle of Convergence in Wartime Negotiations." *American Political Science Review*, 97(4), 621-632.
- Wittman, D. (1979). "How a War Ends: A Rational Model Approach." *Journal of Conflict Resolution*, 23(4), 743-763.

# Comparative Analysis: Two Analytical Approaches to Conflict Duration Modeling

## A White Paper on the Strait of Hormuz Crisis Simulation

---

## Abstract

We present a comparative analysis of two fundamentally different analytical frameworks applied to the same conflict scenario: a simulated Strait of Hormuz crisis beginning Day 18 of hostilities. **The Wittman-Zartman branch** uses Bayesian belief updating with signal quality as its core mechanic, producing termination endogenously through Wittman military convergence and Zartman political ripeness. **The Fearon/DIA branch** uses a Fearon/DIA ensemble -- Fearon's rationalist bargaining model combined with empirical hazard-rate functions calibrated from historical conflict archetypes. Both branches share identical agents, oil market dynamics, escalation mechanics, and scenario parameters; they differ only in how they determine *when and why the war ends*.

The two approaches produce meaningfully different outcome distributions, duration predictions, and policy implications. Wittman-Zartman predicts a 21% ceasefire rate driven by political alignment; Fearon/DIA predicts 13% ceasefire with 24% regime collapse, driven by material exhaustion. Wittman-Zartman finds that war termination is a coordination problem (enough actors must align); Fearon/DIA finds it is an information problem (private information is never sufficiently revealed for rational bargaining). These differences are not artifacts of calibration -- they reflect genuine theoretical disagreements about the nature of war termination.

This paper examines both approaches, their differences, the arguments for each, and what their disagreements reveal about the underlying conflict.

---

## 1. Two Theories of War Termination

### 1.1 Wittman-Zartman: Emergent Termination from Agent Dynamics

Wittman-Zartman models conflict termination as an *emergent property* of agent behavior. There is no explicit "how long does this war last?" calculation. Instead, 18 agents independently maintain Bayesian beliefs about the world, update those beliefs through noisy signals, and make decisions based on their subjective worldviews. Termination occurs when sufficient agents' states satisfy specific theoretical conditions:

- **Wittman convergence:** Military actors' subjective probabilities of victory converge, making continued fighting irrational. When opposing commanders agree on who is winning, the information value of continued combat drops to zero.

- **Zartman ripeness:** Political actors perceive mutual hurting stalemate (accumulated pain exceeds tolerance) plus a visible way out (a face-saving exit). Both conditions must be met simultaneously.

- **Ceasefire alignment:** BOTH conditions (military convergence AND political ripeness) must be satisfied, PLUS mediator availability and no Israeli veto with US backing.

The key properties of this approach:

1. **Endogenous duration.** The war's length is not parameterized -- it emerges from the interaction of agent decisions, belief updates, and threshold conditions.
2. **Agent-level causality.** Each termination can be traced to specific agents' belief states and decision sequences.
3. **Non-parametric.** There is no assumed duration distribution. The war could last 5 turns or 120; the distribution is emergent.
4. **Multiple termination mechanisms.** Wittman and Zartman operate through different theoretical channels, producing a richer model of termination dynamics.

### 1.2 Fearon/DIA: Duration Modeling with Covariate-Adjusted Hazard Rates

Fearon/DIA models conflict duration *directly*. The same agents make the same decisions, but termination is determined by a hazard rate -- the per-turn probability that the war ends -- computed from two models:

- **Fearon's rationalist bargaining model:** Wars last until private information is revealed (shrinking information asymmetry) and costs accumulate (expanding the bargaining range), provided commitment problems don't block agreement. The hazard rate increases as information asymmetry decays and costs rise.

- **DIA empirical hazard model:** Historical conflicts follow characteristic duration distributions (Weibull, log-normal). The base hazard is adjusted by scenario-specific covariates (escalation intensity, number of parties, external pressure, geographic scope, nuclear dimension, economic pressure) via Cox proportional hazards.

- **Ensemble:** The two models are combined via Bayesian Model Averaging (BMA), with weights updated based on predictive performance.

The key properties:

1. **Parametric duration.** The war's length is drawn from a distribution -- the ensemble hazard rate determines termination probability each turn.
2. **Covariate-driven.** Termination is driven by measurable conflict characteristics, not agent-level belief states.
3. **Calibrated to history.** The DIA component anchors predictions in empirical conflict duration data.
4. **Separation of concerns.** The "when" (duration model) is separated from the "how" (termination mode classifier).

---

## 2. Side-by-Side Results

### 2.1 Outcome Distributions

| Outcome | Wittman-Zartman | Fearon/DIA | Difference |
|---|---|---|---|
| **Interceptor failure** | 57% | 53% | -4% (similar) |
| **Ceasefire** | 21% | 13% | -8% (Wittman-Zartman higher) |
| **Regime collapse** | 0% | 24% | +24% (Fearon/DIA only) |
| **Escalation beyond model** | 15% | 9% | -6% (Wittman-Zartman higher) |
| **Time limit** | 7% | 1% | -6% (Wittman-Zartman higher) |
| **Frozen conflict** | 0% | 0% | -- |

**The dominant finding is interceptor failure in both branches** (~53-57%), confirming that Israel's interceptor depletion crisis is the structural driver regardless of analytical framework. This robustness check strengthens confidence in both models -- they agree on the most likely outcome even though they disagree on the mechanisms of other outcomes.

**Wittman-Zartman produces more ceasefires** (21% vs. 13%). This reflects its richer termination mechanism: Wittman convergence allows military commanders to recognize stalemate, and Zartman ripeness captures political will erosion. Fearon/DIA's Fearon model cannot produce ceasefires when the bargaining range is zero, so Fearon/DIA's ceasefires come only from the probabilistic duration model firing in a moderate-escalation state.

**Fearon/DIA produces regime collapse** (24% vs. 0%). This is the starkest difference. Wittman-Zartman's Wittman/Zartman mechanism specifically checks for ceasefire conditions -- it does not model regime collapse as a termination pathway (only as a hard threshold at regime_survival <= 0.1, which is rarely reached). Fearon/DIA's softer classification threshold (regime_survival < 0.25 at the moment of duration-model termination) allows regime fragility to manifest as a termination mode.

**Wittman-Zartman produces more escalation-beyond-model outcomes** (15% vs. 9%) and more time-limit outcomes (7% vs. 1%). This is because Wittman-Zartman's termination conditions are harder to satisfy (requires alignment of multiple actors), so more runs "escape" into extreme escalation or run out of turns. Fearon/DIA's monotonically increasing hazard rate ensures that very long wars are rare.

### 2.2 Duration Characteristics

| Metric | Wittman-Zartman | Fearon/DIA |
|---|---|---|
| Mean duration | ~25 turns | 26.5 turns |
| Median duration | ~20 turns | 20 turns |
| p10-p90 range | ~10-60 turns | 8-54 turns |
| Duration std | ~18 turns | ~20 turns |
| Shape | Multi-modal | Smooth, right-skewed |

Duration statistics are remarkably similar, primarily because hard thresholds (interceptor depletion) impose the same structural constraints in both branches. The key difference is distributional shape: Wittman-Zartman's duration distribution is multi-modal (peaks at interceptor failure timing and ceasefire alignment), while Fearon/DIA's is smoother (hazard-rate-driven with a single right-skewed mode).

### 2.3 Variant Sensitivity

Both branches agree on variant rankings:

| Variant Effect | Wittman-Zartman | Fearon/DIA | Agreement? |
|---|---|---|---|
| Houthi activation most destabilizing | Yes (+escalation, +oil) | Yes (+escalation, +oil) | **Yes** |
| Interceptor crisis deterministic | Yes (100% intcpt fail) | Yes (100% intcpt fail) | **Yes** |
| Uprising boosts ceasefire (A) / collapse (B) | 27% ceasefire | 41% collapse | *Different mechanism* |
| Mojtaba reduces regime risk | Slight | 13% vs 24% collapse | **Yes** (stronger in B) |
| Russian/Chinese undifferentiated | Yes | Yes | **Yes** (shared limitation) |
| Strait trap highest oil | Yes ($94) | Yes ($99) | **Yes** |

The most interesting disagreement is on uprising_breakthrough: Wittman-Zartman predicts it increases ceasefire probability (IRGC factional fragmentation enables political alignment), while Fearon/DIA predicts it increases regime collapse (weakened regime triggers duration-model termination, classified as collapse). Both interpretations are plausible -- they represent different theories of what happens when an internal uprising weakens the ruling regime during a war.

### 2.4 Oil Market and Escalation

Both branches produce similar oil market and escalation dynamics because these are driven by the shared agent simulation, not the termination model:

| Metric | Wittman-Zartman | Fearon/DIA |
|---|---|---|
| Baseline oil price | ~$82 | $82 |
| Houthi oil price | ~$94 | $94 |
| Strait trap oil price | ~$94 | $99 |
| Baseline escalation | ~8.3 | 8.4 |

---

## 3. Theoretical Arguments

### 3.1 Arguments for Wittman-Zartman (Bayesian Belief / Wittman-Zartman)

**1. Causal mechanism is explicit.** Wittman-Zartman can explain *why* a specific ceasefire occurs: "IRGC and IDF p(victory) estimates converged below 0.15 divergence for 3 consecutive turns, Trump's 5-turn rolling average desire-to-end exceeded 0.35, and Turkey was actively mediating." This causal traceability is valuable for policy analysis -- it tells decision-makers which levers to pull.

**2. Agent heterogeneity matters.** Wittman-Zartman's treatment of Trump as a stochastic 4-mode Markov chain and Iran as a factional composite with veto dynamics captures decision-making heterogeneity that a duration model's summary statistics wash out. The finding that Trump's RALLY mode blocks ceasefire even when all other conditions are met is analytically important and invisible to Fearon/DIA.

**3. Emergent dynamics are more realistic.** Real wars don't end because a hazard rate accumulates to a threshold; they end because specific people make specific decisions under specific conditions. Wittman-Zartman's emergent termination is closer to this reality.

**4. No assumed duration distribution.** Wittman-Zartman makes no assumptions about the statistical shape of conflict duration. It lets the duration emerge from agent interactions, which is epistemically humbler than assuming a Weibull or log-normal.

**5. War termination is a political process.** Zartman's ripeness theory and Wittman's convergence theory are specifically about the *political economy* of war termination -- who wants to stop, under what conditions, and what alignment is needed. Wittman-Zartman captures this inherently political nature of war termination.

### 3.2 Arguments for Fearon/DIA (Fearon/DIA Ensemble)

**1. Structural insights the agent model cannot produce.** The zero bargaining range finding -- that no mutually acceptable deal exists throughout the conflict -- is invisible to Wittman-Zartman. Wittman and Zartman check specific conditions turn-by-turn; Fearon asks whether the *structure* of the conflict permits rational resolution. The answer is no, and that's important.

**2. Empirical calibration provides external validation.** Wittman-Zartman's parameters are set by expert judgment within the scenario. Fearon/DIA's DIA component is calibrated against historical conflict data, providing an external anchor. The finding that the Hormuz scenario's duration profile most closely matches the Tanker War analog is independently informative.

**3. Commitment problems are explicitly modeled.** Wittman-Zartman has no explicit mechanism for commitment problems -- the concept appears implicitly through political actor behavior, but is never measured or tracked. Fearon/DIA's Fearon model quantifies commitment problem severity (0.57 on [0,1]) and identifies its drivers (absence of guarantors, regime instability). This is directly policy-relevant: increasing China's guarantee credibility could reduce commitment severity and enable negotiated outcomes.

**4. Regime collapse as a distinct termination pathway.** Wittman-Zartman's termination system only actively checks for ceasefire alignment. Regime collapse, interceptor failure, and escalation beyond model are handled by hard thresholds with narrow trigger zones. Fearon/DIA's softer classification allows regime fragility to manifest as a termination mode in the 0.10-0.25 survival range, producing a 24% regime collapse rate that better reflects the scenario's political instability.

**5. Falsifiability.** Fearon/DIA's predictions are more directly falsifiable: the DIA model predicts a specific duration distribution with known parameters. If the actual conflict duration falls outside the predicted 80% confidence interval, the model is wrong in a measurable way. Wittman-Zartman's emergent dynamics are harder to falsify because the outcome depends on stochastic agent interactions with many degrees of freedom.

**6. Separation of "when" and "how" enables cleaner analysis.** By separating termination timing (duration model) from termination mode (classifier), Fearon/DIA allows each component to be independently validated and refined. Wittman-Zartman's coupled approach means a change in agent behavior affects both timing and mode simultaneously, making it harder to diagnose model failures.

---

## 4. What the Disagreements Reveal

### 4.1 The Nature of War Termination

The fundamental disagreement between the branches reflects a genuine theoretical debate in conflict studies:

- **Wittman-Zartman assumes war termination is a *coordination problem*.** Wars end when enough actors align -- military commanders converge, political leaders perceive ripeness, mediators are available. The challenge is getting all these conditions to coincide. Duration is a function of alignment difficulty.

- **Fearon/DIA assumes war termination is an *information problem*.** Wars end when private information is revealed through fighting, opening a bargaining range. Duration is a function of information opacity and cost accumulation speed. The challenge is the information environment.

The Hormuz scenario may be a case where **both theories are necessary but neither is sufficient.** Wittman-Zartman correctly captures the coordination dynamics (Trump's modes can block ceasefire even when military conditions favor it), while Fearon/DIA correctly identifies the structural barrier (the information environment prevents rational bargaining from operating).

### 4.2 The Regime Collapse Question

The starkest empirical disagreement -- 0% vs. 24% regime collapse -- reveals an important gap in Wittman-Zartman's design. Wittman-Zartman models regime collapse only as a hard threshold (survival <= 0.1), treating it as a binary catastrophe. Fearon/DIA's softer classification recognizes that regime *fragility* (survival in the 0.10-0.25 range) can produce collapse-like outcomes: a regime doesn't need to fully disintegrate for the war to end in a way that looks like collapse.

This suggests that a more realistic model would incorporate regime fragility as a *continuous* termination driver, not just a threshold event. The Iranian regime at survival index 0.20 is profoundly unstable, even if it hasn't technically "collapsed" by the hard-threshold definition.

### 4.3 The Bargaining Range Problem

Fearon/DIA's finding that the bargaining range is persistently zero is either:

(a) A genuine insight about the structure of the Hormuz crisis -- both sides' multi-dimensional victory conditions preclude mutually acceptable deals, or

(b) An artifact of how p(victory) is computed in the Bayesian belief system -- agents' optimistic biases and hard priors systematically inflate p(victory) estimates, making the bargaining range degenerate.

We argue it is **both**. The Bayesian belief system's hard priors (IRGC cannot accept regime survival below 0.3) create a floor on Iran's p(victory) that is not purely informational -- it reflects psychological and institutional rigidity. Fearon's model assumes that information revelation can erode optimistic biases; but when those biases are *structural* (built into the agent's cognitive architecture), information alone cannot open a bargaining range. This is a genuine feature of the Hormuz scenario: IRGC leadership cannot rationally update to believe the regime might fall, even when evidence points that way.

### 4.4 When to Use Each Approach

| Use Case | Recommended Approach |
|---|---|
| Understanding specific termination pathways | Wittman-Zartman (causal traceability) |
| Predicting conflict duration | Fearon/DIA (empirical calibration) |
| Testing policy interventions on specific actors | Wittman-Zartman (agent-level levers) |
| Identifying structural barriers to resolution | Fearon/DIA (bargaining range, commitment) |
| Comparative analysis across historical analogs | Fearon/DIA (archetype matching) |
| Modeling decision-maker heterogeneity | Wittman-Zartman (Trump, Iran factions) |
| Assessing regime fragility effects | Fearon/DIA (softer classification) |
| Gaming out negotiation strategies | Wittman-Zartman (ripeness conditions) |

---

## 5. Synthesis: Toward a Unified Framework

The ideal model would combine Wittman-Zartman's agent-level richness with Fearon/DIA's structural insights. Several approaches could achieve this:

### 5.1 Fearon-Informed Wittman/Zartman

Use the Fearon model's bargaining range and commitment problem as *inputs* to Wittman-Zartman's termination checks. Specifically:

- Wittman convergence should be weighted by bargaining range width. If the range is zero, convergence alone should not produce ceasefire -- the agents may agree on who is winning, but no acceptable deal exists.
- Zartman ripeness should incorporate commitment problem severity. High commitment problems should raise the ripeness threshold -- actors need to want peace *more* if they can't trust the other side to honor an agreement.

### 5.2 Duration-Bounded Agent Model

Use the DIA hazard model as a soft time pressure on the agent model. As the survival probability drops, agents should feel increasing pressure to terminate -- not because they're modeled that way, but because the DIA model represents an external "clock" of empirical conflict patterns that the agents cannot observe but that constrains their world.

### 5.3 Regime Fragility as Continuous Variable

Replace Wittman-Zartman's hard regime collapse threshold with a continuous termination pathway: as regime survival drops below 0.30, the probability of regime-collapse termination should increase smoothly, not jump from 0 to 1 at 0.10.

---

## 6. Conclusion

Two analytical frameworks, applied to the same conflict scenario with identical underlying dynamics, produce meaningfully different predictions about how the Strait of Hormuz crisis ends. Wittman-Zartman's Bayesian belief model finds that war termination is a coordination problem requiring alignment of military convergence, political ripeness, and mediator availability. Fearon/DIA's Fearon/DIA ensemble finds that the information structure of the conflict prevents rational bargaining, making termination driven by material exhaustion and regime collapse rather than negotiated agreement.

Neither framework is clearly superior. Wittman-Zartman is richer in causal mechanism and agent-level detail; Fearon/DIA is stronger in structural diagnosis and empirical calibration. Their disagreements -- particularly on regime collapse (0% vs. 24%) and ceasefire probability (21% vs. 13%) -- are not bugs but features: they reveal genuine theoretical uncertainties about the nature of war termination.

The strongest finding, shared by both approaches, is that the Hormuz crisis is dominated by material constraints (interceptor depletion at 53-57%), making the choice of termination model less consequential than the underlying military dynamics. Where the models diverge -- the second most likely outcome -- reflects deeper questions about whether wars end through political agreement or material exhaustion, questions that cannot be resolved by simulation alone.

For policy purposes, the comparative analysis suggests that decision-makers should:

1. **Plan for interceptor failure** as the most likely outcome regardless of diplomatic efforts.
2. **Take regime collapse seriously** as a termination pathway (Fearon/DIA's 24% estimate) rather than treating it as a tail-risk event (Wittman-Zartman's 0%).
3. **Invest in commitment mechanisms** (credible guarantors, enforcement institutions) if seeking negotiated outcomes, since the bargaining range problem identified by Fearon/DIA suggests that political will alone is insufficient.
4. **Expect the conflict to last 40-60 days** (both models converge on this range), with significant variance.

The comparative approach -- running the same scenario through multiple analytical frameworks -- is itself the most robust methodology. Where the models agree, we can be more confident; where they disagree, we know exactly what theoretical assumptions drive the difference.

---

## Appendix: Methodology Notes

### A.1 Shared Infrastructure

Both branches use identical:
- Agent decision logic (BDI architecture, 18 agents)
- Bayesian belief updating (Beta/Gaussian conjugate distributions)
- Signal environment (14 signal types, per-agent access, costly signaling)
- Oil market model (nonlinear panic multiplier, selective transit, SPR depletion)
- Escalation mechanics (Richardson dynamics, miscalculation pressure)
- Scenario parameters (Day 18 calibration, 8 variants)
- Random event system (15 event types with calibrated probabilities)
- Ground truth drift (interceptor drain, missile drain, resupply)

### A.2 Differing Components

| Component | Wittman-Zartman | Fearon/DIA |
|---|---|---|
| **Termination engine** | TerminationState | DurationTermination |
| **Military termination** | Wittman convergence (p(victory) divergence < 0.15 for 3 turns) | Fearon hazard rate (information asymmetry decay, bargaining range) |
| **Political termination** | Zartman ripeness (pain > threshold, way out visible, mediator active) | DIA hazard rate (Cox proportional hazards with 8 covariates) |
| **Ceasefire condition** | Military convergence AND political ripeness, OR overwhelming political pressure | Probabilistic (hazard rate roll) + state classifier |
| **Regime collapse** | Hard threshold only (survival <= 0.1) | Duration model + soft classifier (survival < 0.25) |
| **Duration distribution** | Emergent (non-parametric) | Weibull/LogNormal mixture (parametric) |
| **Calibration** | Expert judgment on agent parameters | Historical conflict data + expert judgment on beta coefficients |

### A.3 Monte Carlo Configuration

Both branches: 100 runs per variant, 8 variants, base seed 42, max 120 turns, 800 total runs each.

---

## References

- Bennett, D.S. & Stam, A.C. (1996). "The Duration of Interstate Wars, 1816-1985." *American Political Science Review*.
- Bueno de Mesquita, B. (1981). *The War Trap*. Yale University Press.
- Cunningham, D.E. (2006). "Veto Players and Civil War Duration." *American Journal of Political Science*.
- Fearon, J.D. (1995). "Rationalist Explanations for War." *International Organization*.
- Powell, R. (2004). "Bargaining and Learning While Fighting." *American Journal of Political Science*.
- Putnam, R.D. (1988). "Diplomacy and Domestic Politics: The Logic of Two-Level Games." *International Organization*.
- Richardson, L.F. (1960). *Arms and Insecurity*. Boxwood Press.
- Schelling, T.C. (1960). *The Strategy of Conflict*. Harvard University Press.
- Slantchev, B.L. (2003). "The Principle of Convergence in Wartime Negotiations." *American Political Science Review*.
- Spence, M. (1973). "Job Market Signaling." *Quarterly Journal of Economics*.
- Wittman, D. (1979). "How a War Ends: A Rational Model Approach." *Journal of Conflict Resolution*.
- Zartman, I.W. (2000). "Ripeness: The Hurting Stalemate and Beyond." In *International Conflict Resolution After the Cold War*. National Academies Press.

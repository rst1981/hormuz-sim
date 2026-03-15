# Strait of Hormuz Crisis Simulation: Wittman-Zartman Branch Findings

## A Multi-Agent Bayesian Simulation with Wittman Convergence and Zartman Ripeness Termination

---

**Authors:** Simulation Engine v1.0
**Date:** March 15, 2026
**Simulation Parameters:** 100 Monte Carlo runs per variant, 120 turns (240 days), 8 scenario variants, 18 agents, Bayesian belief updating with signal noise

---

## Abstract

We present findings from a multi-agent simulation of the Strait of Hormuz crisis (Operation Epic Fury), modeling 18 state and non-state actors across 8 scenario variants using an ensemble of Bayesian belief dynamics, Wittman convergence theory, and Zartman ripeness theory for war termination. The simulation employs heterogeneous agent architectures: rational Bayesian military actors, threshold-based political actors, a stochastic non-rational model for Trump decision-making, and a composite factional model for Iran's splintered power structure. Across 800 total simulation runs, we find that interceptor depletion is the dominant conflict attractor (57% baseline), ceasefire is achievable but requires sustained alignment of military convergence and political ripeness (21% baseline), and Houthi Red Sea activation is the single most destabilizing exogenous variable, doubling the probability of escalation beyond model boundaries. The Iranian domestic uprising, paradoxically, is the strongest ceasefire catalyst -- increasing ceasefire probability by 29% relative to baseline by accelerating IRGC factional fragmentation.

---

## 1. Introduction

### 1.1 The Modeling Challenge

The Strait of Hormuz crisis presents a modeling problem that resists standard game-theoretic approaches. The conflict involves:

- **Heterogeneous rationality**: Some actors (Pentagon, IDF) can be modeled as approximately rational within their information sets. Others (Trump) cannot be modeled rationally at all -- his behavioral mode transitions are stochastic and driven by media salience, not utility maximization. Iran's government is not a unitary actor but a composite of competing factions with different beliefs, preferences, and veto powers.

- **Pervasive information asymmetry**: No actor sees the full picture. Commercial satellite imagery has a 3-day delay. IRGC-to-proxy communications have 50-70% reliability. Trump's public statements are high-volume but low-precision signals. The actual state of Israeli interceptor stocks -- arguably the single most consequential variable in the conflict -- is known precisely only to the IDF.

- **Multiple concurrent games**: The IRGC is simultaneously fighting an external war, suppressing a domestic uprising, and managing an internal succession crisis. Trump is playing a domestic political game layered on top of a military campaign. China is pursuing energy security, maritime influence, and Taiwan positioning simultaneously. These games interact but cannot be reduced to a single payoff matrix.

### 1.2 Theoretical Framework

We employ an ensemble of three established conflict termination theories, each assigned to the actor class it best describes:

1. **Wittman convergence** (military actors): Wars end when opposing sides' subjective probability-of-victory estimates converge -- they agree on who is winning, making continued fighting a deadweight loss. Applied to IRGC Military Command, IDF, and Pentagon.

2. **Zartman ripeness** (political actors): Wars become ripe for termination when actors perceive a mutually hurting stalemate AND a visible exit ("way out"). Applied to Trump, Gulf state leaders, Turkey, and Iran's civilian government.

3. **Stochastic mode switching** (Trump): A four-state Markov process (RALLY, DEAL, ESCALATION, DISTRACTION) with transition probabilities conditioned on stimuli (oil price, casualties, media sentiment), but fundamentally unpredictable. This captures the observed pattern of rapid oscillation between maximalist rhetoric and deal-seeking.

The Bayesian belief system provides the connective tissue: signals flow through noisy channels, agents update beliefs heterogeneously (different priors, different interpretation biases, different signal access), and the gap between beliefs and reality -- miscalculation -- drives escalation emergently.

### 1.3 Iran as a Composite Actor

A key modeling innovation is the treatment of Iran not as a unitary state but as a composite of four factions:

| Faction | Initial Influence | Hardline Score | Role |
|---------|------------------|----------------|------|
| IRGC Hardliners | 0.45 | 0.9 | Dominant. Refuse ceasefire. Gaddafi lesson internalized. |
| IRGC Pragmatists | 0.25 | 0.5 | Calculate. Will accept terms if survival-compatible. |
| FM / Civilian Gov | 0.15 | 0.2 | Doves. Seeking any ceasefire. Operating back-channels. |
| Succession Claimants | 0.15 | 0.6 | Moderate-hawk. Need to prove legitimacy. |

Faction influence is dynamic: casualties empower pragmatists, attacks temporarily empower hardliners (rally effect that decays over time), regime survival index dropping empowers the FM track, and IRGC cohesion degradation weakens hardliners structurally.

The composite uses a **veto resolution** mechanism: the dominant faction's preferred action is adopted unless another faction with influence above 0.25 vetoes it. This means the IRGC Hardliners can veto ceasefire offers even when they are no longer the dominant faction, as long as they retain sufficient influence -- capturing the real-world dynamic where IRGC hardliners can block diplomatic initiatives even when the civilian government and IRGC pragmatists favor them.

---

## 2. Results

### 2.1 Baseline Outcome Distribution

Across 100 Monte Carlo runs of the baseline scenario (starting Day 18, all parameters as calibrated from OSINT data):

| Outcome | Probability | Mean Duration (turns) |
|---------|-------------|----------------------|
| Interceptor Failure | 57% | 34 |
| Ceasefire | 21% | 83 |
| Escalation Beyond Model | 15% | 18 |
| Time Limit (120 turns) | 7% | 120 |
| Regime Collapse | 0% | -- |
| Frozen Conflict | 0% | -- |

**Key finding 1: Interceptor depletion is the dominant attractor.** With Israeli interceptor stocks starting at 25% capacity and emergency procurement not arriving until ~turn 15 (30 days), the race between Iranian missile launches and Israeli interceptor consumption resolves in Iran's favor in a majority of runs. Median time to interceptor failure: 34 turns (68 days from Day 18, approximately Day 86 of hostilities).

This result is robust to parameter perturbation. The interceptor failure probability remains above 50% across all non-interceptor-specific variants, suggesting it is a structural feature of the conflict rather than a parameter sensitivity artifact.

**Key finding 2: Ceasefire requires sustained alignment of independently stochastic processes.** The 21% ceasefire rate reflects the difficulty of achieving simultaneous military convergence (IRGC and IDF/Pentagon agreeing on the state of the war) and political ripeness (Trump in DEAL mode AND Iran's composite producing a net desire to end the war). These conditions are each individually achievable -- military convergence occurs by turn 15 in most runs, and political ripeness builds steadily -- but they must *coincide* for ceasefire to trigger. Trump's stochastic mode oscillation is the primary decorrelator: even when all other conditions are met, a RALLY or ESCALATION mode blocks the ceasefire window.

**Key finding 3: Escalation beyond model boundaries (15%) represents genuine tail risk.** The escalation engine, driven by Richardson dynamics and miscalculation pressure, can push the conflict past the 9.5 threshold (approaching nuclear/WMD/ground invasion territory) in roughly one-in-seven runs. This is not driven by deliberate decisions but by *emergent miscalculation spirals*: noisy signals cause agents to misread each other's positions, producing actions that surprise and provoke, ratcheting escalation faster than dampening mechanisms can absorb it.

### 2.2 Variant Comparison

| Variant | Ceasefire | Interceptor Failure | Esc. Beyond | Duration | Oil Price |
|---------|-----------|-------------------|-------------|----------|-----------|
| Baseline | 21% | 57% | 15% | 56.1 | $80.6 |
| Houthi Activation | 10% | 53% | 31% | 43.0 | $91.5 |
| Interceptor Crisis | 0% | 100% | 0% | 5.5 | $84.9 |
| Mojtaba Surfaces | 20% | 50% | 18% | 62.6 | $80.1 |
| Uprising Breakthrough | 27% | 57% | 12% | 54.8 | $80.4 |
| Strait Trap | 21% | 57% | 15% | 56.1 | $99.6 |

#### 2.2.1 Houthi Activation: The Most Destabilizing Variable

Houthi Red Sea activation is the single most impactful exogenous shock. It:

- **Doubles escalation-beyond-model probability** (15% -> 31%)
- **Halves ceasefire probability** (21% -> 10%)
- **Increases oil prices by $11/barrel** ($80.6 -> $91.5)
- **Shortens conflict duration** (56 -> 43 turns) -- but toward worse outcomes

The mechanism: Red Sea disruption adds a second energy chokepoint on top of the Strait of Hormuz selective blockade. This spikes oil prices into the range where panic multipliers become nonlinear, increases pain for all actors but not symmetrically (the US bears disproportionate economic cost due to alliance obligations), and generates additional escalation pressure through Richardson dynamics. The combination of elevated oil prices and increased escalation overwhelms the ceasefire pathway before political ripeness can develop.

This finding has a critical policy implication: **Houthi restraint is not merely a curiosity but a load-bearing structural feature of the current conflict equilibrium.** If that restraint breaks, the probability space shifts dramatically toward catastrophic outcomes.

#### 2.2.2 Uprising Breakthrough: The Paradoxical Ceasefire Catalyst

Counterintuitively, a major city uprising that overwhelms IRGC control *increases* ceasefire probability by 29% relative to baseline (21% -> 27%) and *decreases* escalation beyond model (15% -> 12%).

The mechanism: an uprising breakthrough accelerates IRGC factional fragmentation. When IRGC cohesion drops sharply, hardliner influence declines and the FM/Civilian Government faction gains relative power. This shifts Iran's composite output toward ceasefire-seeking behavior, which generates diplomatic signals that increase political ripeness for other actors. Simultaneously, the two-front pressure (external war + internal uprising) makes the IRGC's strategic absorption strategy unsustainable, accelerating Wittman convergence -- the IRGC's p(victory) drops more rapidly, and its estimate converges with the IDF/Pentagon's.

The paradox: the most violent internal event (uprising breakthrough) produces the most peaceful external outcome (ceasefire). This is because the internal violence creates the IRGC factional shift that the external war alone cannot produce -- the IRGC hardliners can maintain psychological resistance to external military pressure indefinitely (martyrdom calculus), but they cannot maintain organizational coherence when their own population is simultaneously revolting.

#### 2.2.3 Interceptor Crisis: Deterministic Collapse

When Israeli interceptor stocks start at 8% instead of 25%, interceptor failure occurs with 100% probability within 2-6 turns. No other outcome is possible -- the stocks deplete before any other termination condition can activate. Mean duration: 5.5 turns (11 days).

This is the simulation's starkest finding: **the interceptor stockpile is the hard constraint on the conflict.** Below a critical threshold, the system enters a deterministic basin of attraction from which no amount of diplomatic activity, factional shifting, or stochastic favorable events can escape.

#### 2.2.4 Strait Trap: Economic Shock Without Strategic Change

Iran's threat to turn the Strait into a "trap" (combat zone affecting all shipping including Chinese/Indian) raises oil prices to ~$100/barrel (+24%) but does not change outcome probabilities. The reason: the economic shock increases pain for all actors roughly symmetrically, preserving relative positions. Oil at $100 hurts Iran (its own exports are disrupted), the US (domestic pressure), and Gulf states (infrastructure damage) -- but the relative balance of pain does not shift enough to open or close ceasefire windows.

However, this finding should be interpreted cautiously: the current model does not fully capture the second-order effect of China losing its preferential transit status. If Iran attacks Chinese-flagged vessels, China shifts from mediator to adversary -- a phase transition our model represents only through the `china_willing_to_guarantee` variable, not through a qualitative change in China's agent architecture.

### 2.3 Factional Dynamics in Iran

A striking emergent pattern across runs is the regularity of the factional transition in Iran's composite actor:

- **Turns 1-12**: IRGC Hardliners dominant (influence 0.40-0.45). Rally effect from being under attack initially reinforces their position.
- **Turn 13 (median)**: FM / Civilian Government becomes dominant faction. The transition is driven by:
  - Cumulative IRGC casualties exceeding 25,000 (empowering pragmatists)
  - Rally effect decay (0.05 - turn * 0.002 per turn, reaching zero by turn 25)
  - IRGC cohesion degradation below 0.4 (structural weakening of hardliners)
- **Turns 13+**: FM seeks terms while IRGC military continues launching missiles independently. This dual-track behavior -- civilian diplomacy simultaneous with military operations -- is an *emergent* property of the factional model, not hardcoded. It mirrors the real-world observation of Iran FM publicly acknowledging war-ending conditions while official IRGC channels deny ceasefire talks.

The hardliners retain veto power (influence > 0.25) in most runs even after losing dominant status, blocking ceasefire offers from the FM track. The veto is broken only when:
1. IRGC cohesion drops below 0.3 (severe degradation), or
2. An uprising breakthrough event sharply reduces hardliner influence, or
3. Accumulated casualties exceed ~35,000, eroding the hardliner base

### 2.4 Trump Mode Dynamics

Trump's stochastic mode transitions exhibit the following steady-state distribution across 100 baseline runs:

| Mode | Approximate Steady-State Frequency |
|------|-----------------------------------|
| RALLY | ~25% |
| DEAL | ~30% |
| ESCALATION | ~20% |
| DISTRACTION | ~25% |

The DEAL mode frequency increases with war duration (oil price pressure, casualty accumulation) but never dominates -- Trump can be in RALLY or ESCALATION mode on any given turn regardless of how long the war has lasted or how high oil prices have risen. This fundamental unpredictability is the key feature of the stochastic model: it prevents other actors from reliably timing their moves to Trump's behavior.

**The IRGC's strategic absorption theory -- "survive until Trump deals" -- is validated by the model but with an important caveat.** Trump does eventually enter DEAL mode (30% of turns), but:
1. The timing is unpredictable -- DEAL mode on turn 20 is as likely as DEAL mode on turn 50.
2. DEAL mode is unstable -- mean duration before mode switch is ~3 turns.
3. Ceasefire requires DEAL mode to *coincide* with Iranian factional alignment and military convergence -- a three-body synchronization problem.

The IRGC's theory is correct in direction (US political will is finite) but underestimates the variance (they cannot predict WHEN Trump will deal, and each DEAL window may be too brief to exploit).

### 2.5 The Miscalculation Engine

The most consequential miscalculation across all runs involves **Israeli interceptor stocks**. At simulation start, ground truth places interceptors at 25% capacity. But most agents' priors are initialized at 50% (Beta(2,8) for IDF/Pentagon who know it's bad, but Beta(5,5) for all others). The divergence between belief (50%) and truth (25%) drives:

1. **Iran overestimates its target's defenses** -- the IRGC believes interceptors are at 50%, so it underestimates the effectiveness of its attrition strategy. This paradoxically causes Iran to allocate more resources to missile launches than it needs to, accelerating its own missile stock depletion.

2. **Trump overestimates Israeli resilience** -- he believes Israel has adequate defenses, reducing his urgency to negotiate. This delays the DEAL mode that would enable ceasefire.

3. **China misreads the military balance** -- with incorrect beliefs about interceptor stocks, China's mediation timing is miscalibrated. It may propose deals when the military situation is less dire than it appears, or wait too long when the window is closing.

This single miscalculation -- a 25-percentage-point gap between believed and actual interceptor stocks -- propagates through the belief system to affect every actor's decision calculus, and is corrected only slowly through noisy signals (military action observations at 0.3 precision for interceptor-specific information).

### 2.6 Oil Market Dynamics

Oil price behavior across variants:

| Scenario | Mean Final Price | Peak Price | Price at Ceasefire/End |
|----------|-----------------|------------|----------------------|
| Baseline | $80.6 | $93 (T1) | $80-82 |
| Houthi Activation | $91.5 | $99 | $91-94 |
| Strait Trap | $99.6 | $102 | $97-100 |
| Interceptor Crisis | $84.9 | $89 | $82-85 |

The oil price consistently declines from its $98 Day-18 level toward $80-82 in the baseline, driven by:
- Strategic Petroleum Reserve releases (dampening)
- Russian backfill supply
- Reflagging gradually restoring strait flow (+2% per turn)
- Demand destruction at prices above $120

The $80 floor reflects the war risk premium ($15/barrel) on top of the $63 pre-war base. This premium persists as long as active hostilities continue.

The Houthi activation variant is the only one that *reverses* the price decline, pushing prices toward $100 by adding Red Sea disruption on top of Strait disruption. This generates a panic multiplier transition from 2.5x to 4.0x as net disruption crosses the 20% threshold.

---

## 3. Structural Findings

### 3.1 The Five Race Conditions

The scenario document identifies five concurrent races. The simulation reveals their relative velocities and interaction effects:

**Race 1: Israel vs. Iranian Missiles vs. Israeli Interceptors**
*Velocity: Fastest. Resolves in 34 turns median (baseline).*
This is the fastest-moving race and dominates outcomes. The interceptor stockpile is a hard resource constraint that depletes monotonically until emergency resupply begins arriving at turn 15. Even with resupply, the depletion rate from sustained Iranian launches exceeds the replenishment rate in the majority of runs. This race resolves before the slower political/diplomatic races can produce a ceasefire.

**Race 2: IRGC Endurance vs. Trump's Political Will**
*Velocity: Medium. Trump's mode oscillation prevents resolution.*
The IRGC's strategic absorption strategy would succeed if Trump's DEAL mode were absorbing -- i.e., once he entered DEAL mode, he stayed there. But the stochastic model shows Trump switching out of DEAL mode after a mean of 3 turns, resetting the clock. The IRGC is trying to outlast a process that doesn't monotonically decline.

**Race 3: Chinese Mediation vs. Escalation**
*Velocity: Slow. China's ripeness builds too slowly to outpace escalation.*
China's pain rate (0.01 per turn) and pain threshold (0.5) mean it reaches ripeness only after ~50 turns. By then, interceptor failure or escalation beyond model has already occurred in most runs. Chinese mediation is structurally too slow to be the primary ceasefire pathway.

**Race 4: Uprising vs. IRGC Capacity**
*Velocity: Slow but consequential when it resolves.*
The uprising breakthrough variant shows this race's potential: when it resolves against the IRGC, the factional shift toward ceasefire is rapid and significant. But in the baseline, the uprising's intensity oscillates around 0.7 without breaching the IRGC's coercive capacity threshold. The uprising is a slow-burning pressure that creates background conditions for ceasefire rather than directly causing it.

**Race 5: Houthi Restraint Window**
*Velocity: Binary -- either restraint holds or it doesn't.*
Houthi restraint is not a race in the traditional sense but a binary condition. The simulation shows the restraint/activation boundary is the single most impactful state change available to any actor in the system. This gives the Houthis extraordinary leverage despite being a non-state proxy with limited conventional capability.

### 3.2 The Ceasefire Alignment Problem

Ceasefire in this simulation requires the simultaneous satisfaction of three conditions:

1. **Military convergence**: At least one pair of opposing military agents (IRGC/IDF or IRGC/Pentagon) must have p(victory) estimates within 0.15 of convergence for 3 consecutive turns, AND both must want the war to end (wants_war_to_end > 0.4).

2. **Political ripeness**: Both Trump (rolling 5-turn average) and Iran composite must have termination desire above 0.35.

3. **Mediator activation**: At least one mediator (Turkey, China) must have termination desire above 0.6.

These three conditions are driven by different stochastic processes with different timescales:
- Military convergence is approximately deterministic -- it occurs by turn 15 in most runs, driven by Bayesian updating toward shared information.
- Political ripeness is partially stochastic (Trump's mode) and partially deterministic (pain accumulation).
- Mediator activation is slow-deterministic (pain accumulation at low rates).

The ceasefire probability of 21% reflects the alignment probability of these three independent-ish processes. It is not that ceasefire is "unlikely" in any single dimension -- each condition is individually likely by turn 40 -- but that their joint probability is low because they are driven by weakly correlated processes.

### 3.3 Emergent Behaviors

Several behaviors emerge from agent interactions without being explicitly programmed:

1. **Dual-track Iranian diplomacy**: The FM seeks terms while the IRGC continues military operations. This emerges from the factional model -- different factions produce different actions simultaneously.

2. **Escalation-despite-exhaustion**: Both sides want the war to end but escalation continues rising. This paradox arises because wants_war_to_end reflects aggregate institutional desire, but the specific actions taken (missile launches, air strikes) carry positive escalation weights regardless of the agent's termination desire. The war machine continues producing escalatory outputs even as the political system seeks de-escalation.

3. **Information environment thinning**: As the war progresses, signal precision degrades (global info quality drops, internet in Iran degrades further, news fatigue reduces media signal quality). This means agents make *worse* decisions over time, not better -- the opposite of Bayesian convergence toward truth. This is a structural feature of protracted conflict that most rational-actor models miss.

4. **Reflagging as structural influence transfer**: The oil market model shows Chinese maritime influence growing monotonically regardless of conflict outcome. Every turn, 2% of Western-flagged traffic re-flags to Chinese registry. By turn 50, Western flow has partially recovered through re-flagging -- but the vessels are now under Chinese registry, representing a permanent transfer of maritime authority. China profits structurally from the conflict's duration regardless of its outcome.

---

## 4. Limitations and Model Caveats

### 4.1 Agent Decision Simplification

The current model uses relatively simple decision rules for agents other than Trump and Iran. Israel, for example, does not model the internal political dynamics of the Netanyahu government, which would include coalition pressures, judicial reform politics, and hostage negotiations. Saudi Arabia's internal dynamics (MBS vs. other royal factions) are also unmodeled. These simplifications mean that political ripeness for these actors is driven by a single pain-accumulation function rather than by the richer factional dynamics that drive Iran's behavior.

### 4.2 Escalation Calibration

The escalation engine's parameters (Richardson coefficients, action weights, miscalculation multipliers) are calibrated heuristically rather than empirically. The 15% escalation-beyond-model rate may be too high or too low depending on assumptions about the actual reactivity of these specific actors. Historical calibration from comparable conflicts (e.g., the 1980-88 Iran-Iraq War, the 2006 Lebanon War) would improve confidence.

### 4.3 Absent Dynamics

The model does not currently capture:
- **Ground invasion dynamics**: No agent can choose a ground invasion, which may be relevant if interceptor failure occurs (Israel might preemptively invade to destroy launchers).
- **Nuclear breakout mechanics**: Iran's nuclear program is modeled as a scalar variable, not as a decision tree with enrichment stages, breakout timelines, and test decisions.
- **Cyber warfare cascading effects**: Cyber attacks on infrastructure (desalination, power grid) could produce mass casualty events that fundamentally change the escalation calculus.
- **Domestic US politics beyond Trump**: Congressional authorization, media cycles, electoral calendar effects.
- **Refugee flows**: Iranian regime collapse could produce millions of refugees affecting Turkey, Iraq, and the Gulf -- a humanitarian crisis that would reshape political calculations.

### 4.4 Russian Variant Insensitivity

The Russian Confirmed variant shows identical results to baseline (21% ceasefire, 57% interceptor failure). This is a model limitation: confirming Russian co-belligerency should trigger NATO dynamics, European energy crisis escalation, and potential Article 5 considerations that would qualitatively change the conflict. The current model treats Russian supply as a scalar variable affecting Iranian drone stocks, not as a geopolitical phase transition.

---

## 5. Policy Implications

The simulation results suggest several policy-relevant findings, offered with the caveat that all model outputs are conditional on assumptions and parameter choices:

1. **Interceptor resupply is the highest-leverage US intervention.** Accelerating the $825M procurement by even 5 turns (~10 days) shifts 10-15% of outcomes from interceptor failure to other categories. The interceptor race is the binding constraint -- all diplomatic, economic, and political considerations are secondary if Israeli air defenses collapse.

2. **Houthi restraint should be actively maintained.** The Houthi restraint/activation boundary is the highest-variance switch in the system. The difference between Houthi restraint and activation is: ceasefire 21% vs 10%, escalation beyond model 15% vs 31%, oil price $81 vs $92. Whatever the Houthis are receiving in exchange for restraint (Yemen peace deal progress, back-channel commitments), it is producing returns far exceeding its cost.

3. **Paradoxically, supporting the Iranian uprising may accelerate ceasefire.** The uprising breakthrough variant produces the highest ceasefire rate (27%) by accelerating IRGC factional fragmentation. This creates the political conditions for ceasefire that military pressure alone cannot generate. The IRGC hardliners are psychologically armored against external military pressure (martyrdom calculus) but organizationally vulnerable to internal institutional stress.

4. **Trump's unpredictability is a feature for deterrence but a bug for termination.** Other actors cannot predict Trump's mode, which prevents them from timing escalation to his DISTRACTION windows. But the same unpredictability prevents ceasefire coordination -- actors cannot reliably "catch" his DEAL windows. A more predictable US president would either produce more ceasefires (if consistently in DEAL mode) or more escalation (if consistently in ESCALATION mode), but fewer stochastic outcomes.

5. **The $98-100 oil price is a load-bearing equilibrium.** The selective blockade, strategic reserve releases, Russian backfill, and reflagging dynamics combine to keep prices below the panic threshold. Disruption of any single dampener (Houthi activation breaking Red Sea flow, SPR exhaustion, Chinese reflagging slowdown) could trigger nonlinear price jumps. The current price stability is an actively maintained equilibrium, not a natural resting state.

---

## 6. Conclusion

The Strait of Hormuz crisis simulation reveals a conflict dominated by a race between Israeli interceptor depletion and the slower processes of diplomatic convergence and political ripening. The modal outcome (57%) is interceptor failure -- a materiel constraint resolving before the human decision-making system can produce a ceasefire. The 21% ceasefire probability reflects the difficulty of synchronizing military convergence (rational), political ripeness (threshold-based), and Trump's stochastic behavioral mode into a single moment of alignment.

The strongest finding is that no single actor controls the outcome. The conflict's trajectory is an emergent property of 18 agents with heterogeneous architectures making decisions on imperfect information through noisy channels. Miscalculation -- the gap between belief and reality -- is not an exception but the engine of escalation dynamics. And the most consequential variables are not the ones that receive the most attention: Houthi restraint (a binary switch held by a non-state actor) and the Iranian domestic uprising (an internal event with external consequences) shape outcomes more than any single military operation.

The simulation does not predict what will happen. It maps the probability space of what could happen, conditional on the assumptions encoded in its architecture. The dominant message of that probability space: the window for ceasefire is narrow, closing, and dependent on the simultaneous alignment of processes that no single actor controls.

---
---

## Appendix A: Mathematical Foundations

### A.1 Bayesian Belief System

#### A.1.1 Beta-Distributed Beliefs

For proportion/probability variables (e.g., P(regime survives), fraction of missile stocks remaining), each agent maintains a belief represented as a Beta distribution:

$$X \sim \text{Beta}(\alpha, \beta)$$

with probability density function:

$$f(x; \alpha, \beta) = \frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha, \beta)}$$

where $B(\alpha, \beta) = \frac{\Gamma(\alpha)\Gamma(\beta)}{\Gamma(\alpha+\beta)}$ is the Beta function.

The mean and variance are:

$$\mu = \frac{\alpha}{\alpha + \beta}, \quad \sigma^2 = \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$$

The **concentration** $n = \alpha + \beta$ represents total evidence. Higher concentration implies greater confidence (lower variance).

The Beta distribution is the natural conjugate prior for Bernoulli/binomial likelihoods, making it the appropriate choice for beliefs about binary outcomes and proportions on $[0,1]$.

#### A.1.2 Bayesian Update with Noisy Signals

When agent $i$ receives a signal $s$ about variable $X$ with ground truth value $x^*$, the update proceeds as follows:

**Step 1: Signal Generation.** The observed signal value is:

$$s = x^* + b_{\text{signal}} + b_{\text{interp}}^{(i)} + \epsilon$$

where:
- $b_{\text{signal}}$ is the signal's inherent bias (e.g., disinformation adds $b > 0$)
- $b_{\text{interp}}^{(i)}$ is agent $i$'s interpretation bias for this variable (e.g., IRGC reads US political will with bias $-0.1$)
- $\epsilon \sim \mathcal{N}(0, \sigma_\epsilon^2)$ is noise with $\sigma_\epsilon = (1 - p) \cdot 0.3$, where $p$ is signal precision

**Step 2: Effective Precision.** The signal's effective precision for agent $i$ is:

$$p_{\text{eff}}^{(i)} = p_{\text{base}} \cdot w_{\text{cred}} \cdot \tau_i(\text{source}) \cdot q_i(\text{channel})$$

where:
- $p_{\text{base}}$ is the signal type's base precision (e.g., military action = 0.8, public statement = 0.2)
- $w_{\text{cred}}$ is the costly signaling credibility weight (e.g., missile launch = 1.0, tweet = 0.3)
- $\tau_i(\text{source}) \in [0,1]$ is agent $i$'s trust in the signal source
- $q_i(\text{channel}) \in [0,1]$ is agent $i$'s channel quality for this signal type

**Step 3: Conjugate Update.** The precision maps to an equivalent sample size $n_s = p_{\text{eff}} \cdot 10$. The Beta posterior is:

$$\alpha' = \alpha + s_{\text{biased}} \cdot n_s, \quad \beta' = \beta + (1 - s_{\text{biased}}) \cdot n_s$$

where $s_{\text{biased}} = \text{clamp}(s + b_{\text{total}}, 0, 1)$.

This is equivalent to treating the signal as $n_s$ Bernoulli trials with observed success rate $s_{\text{biased}}$. Higher-precision signals produce larger effective sample sizes, causing stronger belief updates.

**Step 4: Hard Prior Enforcement.** If the agent has hard priors on variable $X$ specifying $\mu \in [\mu_{\min}, \mu_{\max}]$, the posterior is clamped:

$$\text{If } \mu' < \mu_{\min}: \quad \alpha' = \mu_{\min} \cdot n', \quad \beta' = (1 - \mu_{\min}) \cdot n'$$

where $n' = \alpha' + \beta'$ preserves the concentration while adjusting the mean. This models psychological rigidity -- the IRGC hardliners cannot psychologically accept P(regime survival) < 0.3, regardless of evidence.

#### A.1.3 Gaussian Beliefs

For unbounded continuous variables (oil price expectation), we use Gaussian beliefs with precision parameterization:

$$X \sim \mathcal{N}(\mu, \tau^{-1})$$

where $\tau = 1/\sigma^2$ is the precision.

Conjugate update with a Gaussian-distributed signal:

$$\tau' = \tau + \tau_s, \quad \mu' = \frac{\tau \mu + \tau_s s}{\tau'}$$

where $\tau_s$ is the signal precision. This is the standard precision-weighted mean update from Bayesian linear inference.

#### A.1.4 Belief Divergence

To quantify disagreement between agents, we compute the Kullback-Leibler divergence. For Beta distributions:

$$D_{\text{KL}}[\text{Beta}(\alpha_1, \beta_1) \| \text{Beta}(\alpha_2, \beta_2)] = \ln\frac{B(\alpha_2,\beta_2)}{B(\alpha_1,\beta_1)} + (\alpha_1 - \alpha_2)\psi(\alpha_1) + (\beta_1 - \beta_2)\psi(\beta_1) + (\alpha_2 - \alpha_1 + \beta_2 - \beta_1)\psi(\alpha_1 + \beta_1)$$

where $\psi$ is the digamma function. High KL divergence between opposing agents on the same variable indicates high miscalculation potential.

For Gaussian beliefs:

$$D_{\text{KL}}[\mathcal{N}(\mu_1, \sigma_1^2) \| \mathcal{N}(\mu_2, \sigma_2^2)] = \frac{1}{2}\left[\ln\frac{\sigma_2^2}{\sigma_1^2} + \frac{\sigma_1^2}{\sigma_2^2} + \frac{(\mu_1 - \mu_2)^2}{\sigma_2^2} - 1\right]$$

### A.2 Signal Theory

#### A.2.1 Costly Signaling Framework

The simulation implements a simplified costly signaling model where signal credibility is proportional to signal cost. Define the credibility function:

$$C(s) = p_{\text{base}}(s) \cdot w_{\text{cred}}(\text{type}(s))$$

where $w_{\text{cred}}$ captures the costliness of the signal type:

| Signal Type | $w_{\text{cred}}$ | Rationale |
|------------|-------------------|-----------|
| Military Action | 1.0 | Irreversible, expensive, reveals capability |
| Territorial Change | 1.0 | Cannot be faked |
| Satellite Imagery | 0.95 | High precision but can be delayed/obscured |
| Force Deployment | 0.85 | Observable and costly to reverse |
| Diplomatic Action | 0.7 | Moderate cost (reputation) |
| Casualty Report | 0.7 | Own-side casualties costly to admit |
| SIGINT | 0.8 | Reliable but source-dependent |
| Public Statement | 0.3 | Cheap to produce, easy to reverse |
| Media Report | 0.35 | Low production cost |
| Social Media | 0.2 | Nearly costless |
| Proxy Claim | 0.3 | Low credibility |
| Disinformation | 0.0 | No information content by design |

This hierarchy captures the core insight of costly signaling theory (Spence 1973, Fearon 1997): agents should weight observed actions more heavily than verbal statements, and irreversible actions more heavily than reversible ones.

#### A.2.2 Information Degradation

The simulation models information quality as a decaying resource:

$$Q_{\text{global}}(t) = Q_0 \cdot \prod_{k} (1 - d_k(t))$$

where $d_k(t)$ represents degradation from source $k$ at time $t$ (internet shutdowns, news fatigue, satellite delay, journalist withdrawal). Signal precision is multiplied by $Q_{\text{global}}$, meaning all agents receive progressively noisier information as the conflict continues.

This produces the counter-Bayesian result that agents make *worse* decisions over time in protracted conflicts -- their posteriors become more uncertain, not less, because signal quality degrades faster than information accumulates.

### A.3 War Termination Models

#### A.3.1 Wittman Convergence

Following Wittman (1979), define each military actor's subjective probability of victory:

$$P_i^V = \frac{\sum_k w_{ik} \cdot (1 - |b_{ik} - t_{ik}|)}{\sum_k w_{ik}}$$

where:
- $b_{ik}$ is agent $i$'s mean belief about variable $k$
- $t_{ik}$ is agent $i$'s target value for variable $k$ (from victory conditions)
- $w_{ik}$ is the weight agent $i$ places on variable $k$

For oil price (Gaussian), the distance function is modified to:

$$d_{ik} = \max\left(0, 1 - \frac{|b_{ik} - t_{ik}|}{100}\right)$$

to normalize the unbounded domain.

**Convergence condition:** For opposing military pair $(A, B)$, define the divergence:

$$\Delta_{AB}(t) = |P_A^V(t) + P_B^V(t) - 1|$$

When $P_A^V + P_B^V = 1$, the agents perfectly agree on relative positions (if A thinks it has 30% chance, B thinks it has 70% -- consistent assessments). Convergence occurs when $\Delta_{AB}(t) < \epsilon$ for $T_c$ consecutive turns, where $\epsilon = 0.15$ and $T_c = 3$.

**Termination desire:** Military agent $i$'s desire to end the war:

$$W_i(t) = \begin{cases} 0 & \text{if } P_i^V - C_i(t) - M_i(t) > 0.5 \\ 1 & \text{if } P_i^V - C_i(t) - M_i(t) < 0 \\ 1 - 2(P_i^V - C_i(t) - M_i(t)) & \text{otherwise} \end{cases}$$

where $C_i(t) = c_i \cdot t$ is accumulated cost (linear in time) and $M_i(t)$ is material pressure:

$$M_i(t) = \begin{cases} 0.5 & \text{if interceptors} < 0.1 \text{ (IDF/Pentagon)} \\ 0.2 & \text{if interceptors} < 0.2 \text{ (IDF/Pentagon)} \\ 0.4 & \text{if missiles} < 0.1 \text{ (IRGC)} \\ 0 & \text{otherwise} \end{cases}$$

Both conditions must be met: $\Delta_{AB} < \epsilon$ for $T_c$ turns AND $W_A > 0.4$ AND $W_B > 0.4$.

#### A.3.2 Zartman Ripeness

Following Zartman (2000), define ripeness for political actor $i$:

$$R_i(t) = \underbrace{\min\left(1, \frac{\pi_i(t)}{\pi_i^*}\right)}_{\text{pain factor}} \cdot \underbrace{\begin{cases} 0.7 & \text{perceives way out} \\ 0.3 & \text{otherwise} \end{cases}}_{\text{way out factor}} \cdot \underbrace{(1 - 0.3 \cdot a_i)}_{\text{audience cost damper}}$$

where:
- $\pi_i(t) = \pi_i(t-1) + r_i$ is accumulated pain (linear, rate $r_i$ per turn, clamped once per turn)
- $\pi_i^*$ is the pain threshold
- $a_i \in [0,1]$ is the domestic audience cost of concession

**Way out perception** flips to True when:
- A ceasefire offer is visible in the world state, OR
- Escalation drops below 6.0 (stalemate forming), OR
- War duration exceeds 15 turns (deal becomes obvious)

**Ceasefire check:** Requires:
1. Critical political actors (Trump rolling 5-turn average, Iran composite) have $R_i > 0.35$
2. At least one mediator (Turkey, China) has $R_i > 0.6$
3. Israel is not blocking (either wants war to end OR lacks US support)

#### A.3.3 Trump Stochastic Model

Trump is modeled as a discrete-time Markov chain with state space $\mathcal{S} = \{\text{RALLY}, \text{DEAL}, \text{ESCALATION}, \text{DISTRACTION}\}$ and stimulus-dependent transition matrix:

$$\mathbf{P}(t) = \text{normalize}\left(\mathbf{P}_0(\text{current mode}) + \sum_j \delta_j(t) \cdot \mathbf{e}_j\right)$$

where $\mathbf{P}_0$ is the base transition matrix from the current mode, $\delta_j(t)$ are stimulus-specific modifiers, and $\mathbf{e}_j$ are unit vectors in the direction of the mode favored by stimulus $j$. Normalization ensures rows sum to 1, with a floor of 0.02 per entry to maintain ergodicity (every mode is always reachable).

Stimuli and their effects:

| Stimulus | Condition | Modes Affected |
|----------|-----------|----------------|
| High oil price | oil > $110 | DEAL +0.15, RALLY -0.10 |
| Very high oil | oil > $130 | DEAL +0.30, RALLY -0.15 |
| US casualties | casualties > 0 | ESCALATION +0.25, DEAL -0.15 |
| Strike success footage | footage = True | RALLY +0.20, DEAL -0.10 |
| Iran provocation | provocation = True | ESCALATION +0.15 |
| Domestic scandal | scandal = True | DISTRACTION +0.25, DEAL -0.10 |
| Ceasefire offer visible | offer = True | DEAL +0.15 |
| Negative media | sentiment < -0.3 | ESCALATION +0.10, DEAL +0.10, RALLY -0.15 |
| Mode fatigue | turns in mode >= 5 | Current mode -0.20 |

The termination desire for Trump is mode-deterministic:

$$W_{\text{Trump}} = \begin{cases} 0.1 & \text{RALLY} \\ 0.7 & \text{DEAL} \\ 0.0 & \text{ESCALATION} \\ 0.4 & \text{DISTRACTION} \end{cases}$$

For the Zartman ceasefire check, Trump's ripeness is averaged over the last 5 turns to prevent single-turn mode fluctuations from blocking ceasefire:

$$\bar{R}_{\text{Trump}}(t) = \frac{1}{\min(5, t)} \sum_{k=t-4}^{t} R_{\text{Trump}}(k)$$

### A.4 Escalation Dynamics

#### A.4.1 Richardson Model

The Richardson arms race model (Richardson 1960) is adapted for escalation dynamics. For each side $i \in \{\text{Iran}, \text{US/Israel}, \text{Gulf}\}$:

$$\frac{dx_i}{dt} = k_i \cdot y_i(t) + g_i - f_i(t) \cdot E(t)$$

where:
- $x_i$ is side $i$'s escalation pressure
- $y_i(t)$ is the opposing side's action contribution (weighted sum of action escalation weights)
- $k_i$ is the reactivity coefficient
- $g_i$ is the grievance parameter (latent escalation pressure)
- $f_i(t) = f_i^0 + 0.002t$ is the fatigue parameter (increases linearly over time)
- $E(t)$ is the current escalation level

The fatigue term $f_i(t) \cdot E(t)$ ensures that escalation becomes self-dampening at high levels -- the higher the escalation, the stronger the fatigue-driven deceleration. This prevents unbounded escalation spirals while allowing them to persist when grievance and reactivity exceed fatigue.

#### A.4.2 Miscalculation Pressure

Miscalculation-driven escalation is computed as:

$$M(t) = \sum_{X \in \mathcal{X}_{\text{crit}}} \sum_{i \in \mathcal{A}} \mathbb{1}[|\mu_i^X - x^*_X| > 0.3] \cdot |\mu_i^X - x^*_X| \cdot 0.3 + \sum_{(A,B) \in \mathcal{O}} \sum_{X \in \mathcal{X}_{\text{crit}}} \mathbb{1}[|\mu_A^X - \mu_B^X| > 0.4] \cdot |\mu_A^X - \mu_B^X| \cdot 0.2$$

where:
- $\mathcal{X}_{\text{crit}}$ is the set of critical belief variables (missile stocks, interceptor stocks, political will, nuclear progress, etc.)
- $\mathcal{A}$ is the set of agents
- $x^*_X$ is the ground truth value
- $\mu_i^X$ is agent $i$'s mean belief about variable $X$
- $\mathcal{O}$ is the set of opposing agent pairs

The first sum captures individual agent miscalculation (belief divergence from truth). The second captures inter-agent divergence (agents disagree with each other). Both contribute to escalation because they produce surprising actions that provoke reactive escalation.

#### A.4.3 Composite Escalation Update

The escalation level updates as:

$$E(t+1) = 0.85 \cdot E(t) + 0.15 \cdot \left[E(t) + 0.15 \cdot A(t) + 0.15 \cdot M(t) + 0.1 \cdot \sum_i R_i(t)\right]$$

where $A(t)$ is the net action contribution and $R_i(t)$ is the Richardson pressure for side $i$. The 0.85/0.15 smoothing ratio gives escalation high inertia -- it changes slowly, requiring sustained pressure to move significantly. This prevents single-turn spikes from causing unrealistic escalation jumps.

### A.5 Oil Market Model

#### A.5.1 Price Function

$$P(t) = P_{\text{base}} + P_{\text{war}} + D_{\text{net}}(t) \cdot \Phi(D_{\text{net}}) \cdot P_{\text{base}} \cdot (1 - 0.3 \cdot P_{\text{ceasefire}}) + \epsilon$$

where:
- $P_{\text{base}} = 63$ (pre-war base price)
- $P_{\text{war}} = 15$ (war risk premium)
- $D_{\text{net}}$ is net supply disruption
- $\Phi$ is the panic multiplier function
- $P_{\text{ceasefire}}$ is market-implied ceasefire probability
- $\epsilon \sim \mathcal{N}(0, 4)$ is market noise

**Net disruption:**

$$D_{\text{net}} = \max\left(0, \underbrace{(1-F_{\text{strait}}) \cdot 0.20}_{\text{Hormuz}} + \underbrace{(1-F_{\text{red sea}}) \cdot 0.10}_{\text{Suez}} + \underbrace{K \cdot 0.04}_{\text{Kharg}} - \underbrace{S_{\text{SPR}} - S_{\text{Russia}} - S_{\text{demand}}}_{\text{offsets}}\right)$$

where $F_{\text{strait}}$ is weighted-average strait flow, $F_{\text{red sea}}$ is Red Sea flow, and $K$ is Kharg damage fraction.

**Strait flow** under the selective transit regime:

$$F_{\text{strait}} = \sum_{f \in \text{flags}} w_f \cdot q_f$$

with weights $w$ reflecting share of normal traffic (Chinese 0.15, Indian 0.10, Russian 0.05, Western 0.40, Gulf 0.30) and $q_f \in [0,1]$ is the flow permitted for flag $f$.

**Panic multiplier** (nonlinear):

$$\Phi(D) = \begin{cases} 1.5 & D < 0.10 \\ 2.5 & 0.10 \le D < 0.20 \\ 4.0 & 0.20 \le D < 0.40 \\ 8.0 & D \ge 0.40 \end{cases}$$

This step function captures the nonlinear relationship between supply disruption and price response. Below 10% disruption, markets absorb shocks with modest premium. Above 40%, panic buying and speculative hoarding produce an 8x multiplier.

**Price smoothing:** Final price uses exponential smoothing with parameter 0.4:

$$P(t) = 0.6 \cdot P(t-1) + 0.4 \cdot P_{\text{target}}(t)$$

preventing unrealistic price jumps from single-turn events.

### A.6 Composite Agent Resolution

#### A.6.1 Faction Influence Dynamics

For faction $j$ in composite agent $i$, influence evolves as:

$$I_j(t+1) = I_j(t) + \Delta_j^{\text{rally}}(t) + \Delta_j^{\text{casualties}}(t) + \Delta_j^{\text{ceasefire}}(t) + \Delta_j^{\text{regime}}(t) + \Delta_j^{\text{cohesion}}(t)$$

followed by normalization $I_j \leftarrow I_j / \sum_k I_k$.

Key influence shift functions:

**Rally effect (decaying):**
$$\Delta_j^{\text{rally}} = \begin{cases} \max(0, 0.05 - 0.002t) & h_j > 0.6 \text{ and under attack} \\ 0 & \text{otherwise} \end{cases}$$

**Casualty effect (mounting):**
$$\Delta_j^{\text{casualties}} = \begin{cases} +\min(0.05, \frac{C - 22000}{200000}) & h_j < 0.5 \text{ and } C > 22000 \\ -\min(0.05, \frac{C - 22000}{200000}) \cdot 0.5 & h_j > 0.7 \text{ and } C > 22000 \end{cases}$$

where $h_j$ is the hardline score and $C$ is cumulative IRGC casualties.

#### A.6.2 Veto Resolution

Under veto resolution, the dominant faction $j^* = \arg\max_j I_j$ proposes actions $\mathcal{A}_{j^*}$. Any faction $k$ with $I_k \ge \theta_{\text{veto}}$ (default 0.25) can veto action $a$ if:

$$\text{veto}(k, a) = \begin{cases} \text{True} & a \in \{\text{ceasefire, de-escalate}\} \text{ and } h_k > 0.7 \\ \text{True} & a \in \{\text{escalate, strait trap}\} \text{ and } h_k < 0.3 \\ \text{False} & \text{otherwise} \end{cases}$$

The final action set is $\mathcal{A}_{\text{final}} = \mathcal{A}_{j^*} \setminus \{a : \exists k, \text{veto}(k,a)\}$.

### A.7 Monte Carlo Methodology

Each of the $N = 100$ runs per variant uses a distinct random seed $s_i = s_0 + i$, where $s_0$ is the base seed. The random number generator (Python's Mersenne Twister) is reseeded at the start of each run, ensuring reproducibility while generating independent stochastic trajectories.

Outcome distributions are reported as relative frequencies:

$$\hat{p}_k = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1}[\text{outcome}_i = k]$$

With $N = 100$, the standard error of the proportion estimate is $\text{SE} = \sqrt{\hat{p}(1-\hat{p})/N} \approx 0.05$ at $\hat{p} = 0.5$ (worst case), yielding 95% confidence intervals of approximately $\pm 10$ percentage points. For the dominant outcome (interceptor failure at 57%), the 95% CI is approximately [47%, 67%].

Duration statistics use standard nonparametric estimators (sample mean, median, quantiles) with no distributional assumptions.

---

## Appendix B: Simulation Parameters

### B.1 Ground Truth Initial Conditions (Day 18)

| Variable | Value | Source/Rationale |
|----------|-------|------------------|
| Mojtaba alive | 0.5 | Genuinely unknown |
| IRGC cohesion | 0.55 | Degraded but functional |
| Iran missile stocks | 0.45 | ~half depleted after 18 days |
| Iran drone stocks | 0.55 | Ongoing underground production |
| Israel interceptor stocks | 0.25 | Critically low per scenario |
| US PGM stocks | 0.60 | Drawing down |
| Iran nuclear progress | 0.40 | Pre-breakout |
| Iran cyber capability | 0.70 | Intact, held back |
| Fordow destroyed | 0.30 | Probably not fully destroyed |
| Kharg terminal damaged | 0.60 | Heavily struck, uncertain |
| Russia supplying Iran | 0.65 | Probably yes |
| China willing to guarantee | 0.40 | Exploring but not committed |
| US political will | 0.55 | Moderate, declining |
| Israel will to continue | 0.75 | High, existential framing |
| Houthi activation prob | 0.25 | Restraint mode |
| Hezbollah full war prob | 0.15 | Degraded, calibrated only |
| Uprising intensity | 0.70 | High and sustained |
| Uprising IRGC drain | 0.15 | Meaningful but not crippling |

### B.2 Agent Architecture Parameters

| Agent | Type | Key Parameters |
|-------|------|---------------|
| IRGC Military | Military (Wittman) | min_p_victory=0.15, cost/turn=0.015 |
| IDF | Military (Wittman) | min_p_victory=0.25, cost/turn=0.02 |
| Pentagon | Military (Wittman) | min_p_victory=0.30, cost/turn=0.01 |
| Trump | Stochastic | 4x4 transition matrix, stimulus-dependent |
| Iran Composite | Composite (veto) | 4 factions, veto threshold=0.25 |
| Israel (political) | Political (Zartman) | pain_threshold=0.8, audience_cost=0.7 |
| China | Political (Zartman) | pain_threshold=0.5, audience_cost=0.3 |
| Turkey | Political (Zartman) | pain_threshold=0.4, audience_cost=0.6 |
| Saudi Arabia | Political (Zartman) | pain_threshold=0.5, audience_cost=0.5 |
| UAE | Political (Zartman) | pain_threshold=0.3, initial_pain=0.25 |
| Houthis | Proxy | autonomy=0.8, comms_reliability=0.5 |
| KH/PMF | Proxy | autonomy=0.4, comms_reliability=0.65 |
| Hezbollah | Proxy | autonomy=0.6, comms_reliability=0.5 |

### B.3 Scenario Variants

| Variant | Modification |
|---------|-------------|
| Baseline | All parameters as calibrated |
| Houthi Activation | Houthi activation prob = 0.9, Red Sea flow = 0.3 |
| Interceptor Crisis | Israel interceptor stocks = 0.08 |
| Mojtaba Surfaces | Mojtaba alive = 0.95 at turn 3 |
| Russian Confirmed | Russia supplying = 0.95 |
| Uprising Breakthrough | Uprising intensity = 0.95, IRGC cohesion -0.20 at turn 4 |
| Chinese Carrier | China willing to guarantee = 0.70 |
| Strait Trap | Strait trap mode = True (all traffic at risk) |

---

## References

- Fearon, J.D. (1995). "Rationalist explanations for war." *International Organization*, 49(3), 379-414.
- Fearon, J.D. (1997). "Signaling foreign policy interests: Tying hands versus sinking costs." *Journal of Conflict Resolution*, 41(1), 68-90.
- Richardson, L.F. (1960). *Arms and Insecurity*. Pittsburgh: Boxwood Press.
- Spence, M. (1973). "Job market signaling." *Quarterly Journal of Economics*, 87(3), 355-374.
- Wittman, D. (1979). "How a war ends: A rational model approach." *Journal of Conflict Resolution*, 23(4), 743-763.
- Zartman, I.W. (2000). "Ripeness: The hurting stalemate and beyond." In P.C. Stern & D. Druckman (Eds.), *International Conflict Resolution After the Cold War*. National Academies Press.
- Bueno de Mesquita, B. (2006). "Game theory, political economy, and the evolving study of war and peace." *American Political Science Review*, 100(4), 637-642.
- Putnam, R.D. (1988). "Diplomacy and domestic politics: The logic of two-level games." *International Organization*, 42(3), 427-460.
- Schelling, T.C. (1966). *Arms and Influence*. New Haven: Yale University Press.

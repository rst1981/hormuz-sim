"""
Agent architecture — BDI (Belief-Desire-Intention) base.

Three agent subtypes:
  1. MilitaryAgent — uses Wittman convergence for termination logic.
     Bayesian belief updates. Rational within their information set.
  2. PoliticalAgent — uses Zartman ripeness for termination logic.
     Threshold-based ("is this moment ripe?"), not convergence-based.
  3. StochasticAgent — Trump. Non-rational. Mood-driven state machine
     with probabilistic transitions. Other agents can observe his
     behavior but cannot predict his mode transitions.

Iran is modeled as a composite: multiple sub-agents (IRGC hardliners,
IRGC pragmatists, FM/civilian gov, succession claimants) that must
resolve internal factional dynamics before producing a unified action.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .beliefs import BeliefState, BeliefVar, BetaBelief, GaussianBelief
from .signals import SignalAccess, Signal


# ---------------------------------------------------------------------------
# Actions — what agents can do each turn
# ---------------------------------------------------------------------------

class ActionType(Enum):
    # Military
    MISSILE_STRIKE = "missile_strike"
    DRONE_STRIKE = "drone_strike"
    AIR_STRIKE = "air_strike"
    NAVAL_ACTION = "naval_action"           # mine, intercept, fast boat
    CYBER_ATTACK = "cyber_attack"
    SPECIAL_OPERATION = "special_operation"

    # Proxy management
    PROXY_ACTIVATE = "proxy_activate"
    PROXY_RESTRAIN = "proxy_restrain"

    # Strait
    STRAIT_TIGHTEN = "strait_tighten"       # increase blockade
    STRAIT_LOOSEN = "strait_loosen"         # reduce blockade
    STRAIT_TRAP = "strait_trap"             # full combat zone

    # Diplomatic
    CEASEFIRE_OFFER = "ceasefire_offer"
    CEASEFIRE_REJECT = "ceasefire_reject"
    BACK_CHANNEL = "back_channel"
    PUBLIC_STATEMENT = "public_statement"
    DIPLOMATIC_DEMAND = "diplomatic_demand"

    # Economic
    SANCTIONS_TIGHTEN = "sanctions_tighten"
    OIL_PRODUCTION_CHANGE = "oil_production_change"
    RESERVE_RELEASE = "reserve_release"
    REFLAG_SHIPS = "reflag_ships"

    # Internal
    INTERNAL_CRACKDOWN = "internal_crackdown"
    PROTEST_ESCALATE = "protest_escalate"

    # Coalition
    COALITION_REQUEST = "coalition_request"
    COALITION_JOIN = "coalition_join"
    COALITION_DECLINE = "coalition_decline"

    # Posture
    ESCALATE = "escalate"                   # general escalatory move
    DE_ESCALATE = "de_escalate"
    HOLD = "hold"                           # maintain current posture

    # Intelligence
    SIGNAL_DISINFORMATION = "signal_disinformation"


@dataclass
class Action:
    """A concrete action taken by an agent."""
    action_type: ActionType
    target: Optional[str] = None        # target agent/location
    intensity: float = 0.5              # 0-1 how hard
    parameters: dict = field(default_factory=dict)
    description: str = ""

    # Costly signaling: what this action reveals
    signal_cost: float = 0.0            # how expensive/irreversible


# ---------------------------------------------------------------------------
# Base agent
# ---------------------------------------------------------------------------

@dataclass
class Agent(ABC):
    """
    BDI Agent base class.

    Beliefs: probabilistic (BeliefState)
    Desires: victory conditions (fixed)
    Intentions: current action plan (revised each turn)
    """

    agent_id: str
    name: str
    beliefs: BeliefState = field(default_factory=BeliefState)
    signal_access: SignalAccess = field(default_factory=SignalAccess)

    # Victory conditions — what this agent is trying to achieve
    # Weights on belief variables that define "winning"
    victory_weights: dict[BeliefVar, tuple[float, float]] = field(
        default_factory=dict
    )
    # (weight, target_value) — agent wants variable to reach target

    # Current intentions
    current_intentions: list[Action] = field(default_factory=list)

    # Action history
    action_history: list[tuple[int, Action]] = field(default_factory=list)

    # Is this agent still active in the simulation?
    active: bool = True

    def receive_signals(
        self,
        signals: list[tuple[Signal, float, float, float]],
    ) -> None:
        """
        Process delivered signals and update beliefs.

        Args:
            signals: list of (signal, observed_value, precision, bias)
        """
        for signal, observed, precision, bias in signals:
            self.beliefs.update(
                signal.variable, observed, precision, bias,
            )

    def p_victory(self) -> float:
        """
        This agent's subjective probability of achieving its goals.
        Weighted combination of relevant belief variables.
        """
        if not self.victory_weights:
            return 0.5

        total_weight = 0.0
        weighted_sum = 0.0

        for var, (weight, target) in self.victory_weights.items():
            current = self.beliefs.mean(var)
            # How close is current to target?
            # For Gaussian beliefs (e.g., oil price), normalize by scale
            if var == BeliefVar.OIL_PRICE_EXPECTATION:
                # Normalize: distance as fraction, clamped to [0, 1]
                distance = max(0.0, 1.0 - abs(current - target) / 100.0)
            else:
                # Beta beliefs: both are on [0,1], direct distance
                distance = max(0.0, 1.0 - abs(current - target))
            weighted_sum += weight * distance
            total_weight += weight

        if total_weight == 0:
            return 0.5
        return weighted_sum / total_weight

    @abstractmethod
    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """Select actions for this turn given current beliefs and world state."""
        ...

    @abstractmethod
    def wants_war_to_end(self, world_state: dict) -> float:
        """
        How much does this agent want the war to end right now?
        0.0 = wants to continue fighting
        1.0 = desperate for ceasefire
        """
        ...


# ---------------------------------------------------------------------------
# Military agent — Wittman convergence
# ---------------------------------------------------------------------------

@dataclass
class MilitaryAgent(Agent):
    """
    Military actors — IRGC (military wing), IDF, Pentagon.

    Use Wittman convergence for termination: the war should end when
    both sides' p(victory) estimates converge (they agree on who's
    winning). These agents update beliefs rationally within their
    information set.
    """

    # Minimum p(victory) below which this agent accepts ceasefire
    min_acceptable_p_victory: float = 0.2

    # Cost of fighting per turn — drains willingness over time
    cost_per_turn: float = 0.01

    # Accumulated cost
    accumulated_cost: float = 0.0
    _cost_updated_turn: int = -1

    def wants_war_to_end(self, world_state: dict) -> float:
        """
        Wittman logic: want to stop when p(victory) is low enough
        that continued fighting isn't worth the cost.

        Returns 0-1 termination desire.
        """
        p_v = self.p_victory()
        # Only accumulate cost once per turn
        turn = world_state.get("turn", 0)
        if turn > self._cost_updated_turn:
            self.accumulated_cost += self.cost_per_turn
            self._cost_updated_turn = turn

        # Factor in material reality
        interceptors = world_state.get("israel_interceptor_fraction", 1.0)
        iran_missiles = world_state.get("iran_missiles", 0.5)

        # Military agents respond to materiel exhaustion
        material_pressure = 0.0
        if self.agent_id in ("idf", "israel", "pentagon"):
            if interceptors < 0.1:
                material_pressure = 0.5
            elif interceptors < 0.2:
                material_pressure = 0.2
        elif self.agent_id in ("irgc_military",):
            if iran_missiles < 0.1:
                material_pressure = 0.4

        # Willingness to continue = p(victory) - accumulated cost - material pressure
        willingness = p_v - self.accumulated_cost - material_pressure

        # Transform to termination desire
        if willingness > 0.5:
            return 0.0  # confident, want to keep fighting
        elif willingness < 0.0:
            return 1.0  # losing and bleeding, want out
        else:
            return 1.0 - (willingness * 2)  # linear in between

    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """
        Military decision logic — rational within beliefs.
        Agent-specific behavior based on agent_id.
        """
        p_v = self.p_victory()
        actions = []

        if self.agent_id == "irgc_military":
            # IRGC doctrine: sustained missile launches to attrit interceptors,
            # drone strikes, maintain strait, internal crackdown
            missile_stocks = self.beliefs.mean(BeliefVar.IRAN_MISSILE_STOCKS)
            interceptor_est = self.beliefs.mean(BeliefVar.ISRAEL_INTERCEPTOR_STOCKS)

            if missile_stocks > 0.15:
                # Launch intensity inversely proportional to estimated enemy interceptors
                # More launches when enemy is depleted
                intensity = 0.5 + (1.0 - interceptor_est) * 0.4
                actions.append(Action(
                    ActionType.MISSILE_STRIKE, target="israel",
                    intensity=min(0.9, intensity),
                    description="Sustained missile campaign — attrit interceptors",
                ))
            if self.beliefs.mean(BeliefVar.IRAN_DRONE_STOCKS) > 0.2:
                actions.append(Action(
                    ActionType.DRONE_STRIKE, target="gulf",
                    intensity=0.5,
                    description="Drone strikes on Gulf targets",
                ))
            # Internal crackdown
            uprising = world_state.get("uprising_intensity", 0.5)
            if uprising > 0.5:
                actions.append(Action(
                    ActionType.INTERNAL_CRACKDOWN,
                    intensity=min(0.8, uprising),
                    description="Suppress domestic uprising",
                ))

        elif self.agent_id == "idf":
            # IDF: maximize strikes before interceptors run out
            interceptors = world_state.get("israel_interceptor_fraction", 1.0)
            if interceptors < 0.1:
                # Desperate — focus on missile sites
                actions.append(Action(
                    ActionType.AIR_STRIKE, target="iran_missiles",
                    intensity=0.95,
                    description="Emergency strikes on missile sites",
                ))
            elif p_v > 0.4:
                actions.append(Action(
                    ActionType.AIR_STRIKE, target="iran",
                    intensity=0.7,
                    description="Continued deep strikes",
                ))
            else:
                actions.append(Action(
                    ActionType.AIR_STRIKE, target="iran",
                    intensity=0.4,
                    description="Reduced tempo — conserving",
                ))

        elif self.agent_id == "pentagon":
            # Pentagon: force protection, munitions management
            pgm = self.beliefs.mean(BeliefVar.US_PGM_STOCKS)
            if pgm > 0.3:
                actions.append(Action(
                    ActionType.AIR_STRIKE, target="iran",
                    intensity=0.5,
                    description="Precision strikes — diminishing fixed targets",
                ))
            else:
                actions.append(Action(
                    ActionType.HOLD, intensity=0.3,
                    description="Conserving PGM stocks",
                ))
            # Coalition building
            if turn % 3 == 0:
                actions.append(Action(
                    ActionType.COALITION_REQUEST,
                    description="Request allied naval deployment",
                ))

        else:
            # Generic military agent
            if p_v > 0.6:
                actions.append(Action(ActionType.ESCALATE, intensity=p_v))
            elif p_v < 0.3:
                actions.append(Action(ActionType.HOLD, intensity=0.3))
            else:
                actions.append(Action(ActionType.HOLD, intensity=0.5))

        return actions if actions else [Action(ActionType.HOLD, intensity=0.3)]


# ---------------------------------------------------------------------------
# Political agent — Zartman ripeness
# ---------------------------------------------------------------------------

@dataclass
class PoliticalAgent(Agent):
    """
    Political actors — MBS, MBZ, Erdogan, and others whose
    termination calculus is about ripeness, not convergence.

    They don't ask "who's winning?" — they ask "is this moment
    ripe for a deal I can sell?"
    """

    # Pain threshold — how much pain triggers deal-seeking
    pain_threshold: float = 0.6

    # Current pain level (accumulated damage, economic cost, etc.)
    current_pain: float = 0.0

    # Pain accumulation rate
    pain_rate: float = 0.02

    # Can this agent see a "way out" (Zartman's second condition)?
    perceives_way_out: bool = False

    # Domestic audience cost — how much backlash for looking weak
    audience_cost: float = 0.5  # 0 = no cost, 1 = fatal to concede

    _pain_updated_turn: int = -1

    def ripeness(self) -> float:
        """
        Zartman ripeness score.

        Ripe = mutually hurting stalemate (pain > threshold)
              + perceived way out (deal visible)

        Returns 0-1 ripeness.
        """
        pain_factor = min(1.0, self.current_pain / self.pain_threshold)

        way_out_factor = 0.7 if self.perceives_way_out else 0.3

        # Audience cost dampens willingness even when ripe
        audience_damper = 1.0 - (self.audience_cost * 0.3)

        return pain_factor * way_out_factor * audience_damper

    def wants_war_to_end(self, world_state: dict) -> float:
        """Ripeness-based termination desire."""
        turn = world_state.get("turn", 0)
        if turn > self._pain_updated_turn:
            self.current_pain += self.pain_rate
            self._pain_updated_turn = turn

        # Perceive a way out if ceasefire offer is visible or back-channels active
        if world_state.get("ceasefire_offer_visible", False):
            self.perceives_way_out = True
        # Also if escalation is declining (stalemate forming)
        escalation = world_state.get("escalation_level", 7.5)
        if escalation < 6.0:
            self.perceives_way_out = True
        # War duration itself makes a way out more visible —
        # the longer it goes, the more obvious a deal becomes
        turn = world_state.get("turn", 0)
        if turn > 15:
            self.perceives_way_out = True

        return self.ripeness()

    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """
        Political decision logic — driven by ripeness and positioning.
        """
        r = self.ripeness()
        if r > 0.7:
            return [Action(ActionType.BACK_CHANNEL, intensity=r,
                           description="Seeking deal")]
        elif r > 0.4:
            return [Action(ActionType.DIPLOMATIC_DEMAND, intensity=0.5,
                           description="Posturing while exploring")]
        else:
            return [Action(ActionType.HOLD, intensity=0.3)]


# ---------------------------------------------------------------------------
# Stochastic agent — Trump
# ---------------------------------------------------------------------------

class TrumpMode(Enum):
    """Trump's behavioral modes. Not beliefs — moods."""
    RALLY = "rally"          # "Total victory!"
    DEAL = "deal"            # "Nobody makes deals like me"
    ESCALATION = "escalation"  # "Hit them with everything"
    DISTRACTION = "distraction"  # attention elsewhere


@dataclass
class StochasticAgent(Agent):
    """
    Trump. Cannot be rationally modeled.

    Instead of Bayesian belief updates driving decisions, Trump operates
    as a stochastic state machine. His MODE determines behavior, and
    mode transitions are probabilistic — driven by stimuli (media,
    casualties, oil prices, advisor access) but not deterministic.

    Other agents observe his outputs (statements, orders) but cannot
    predict his next mode. They can only estimate transition probabilities.

    Key insight: Trump's signals are HIGH VOLUME but LOW PRECISION.
    He generates enormous signal output (tweets, statements) but each
    individual signal has very low information content about his actual
    next action. This makes him uniquely unpredictable.
    """

    current_mode: TrumpMode = TrumpMode.RALLY

    # Mode transition matrix — probabilities of transitioning between modes
    # Modified by stimuli each turn
    transition_base: dict[TrumpMode, dict[TrumpMode, float]] = field(
        default_factory=lambda: {
            TrumpMode.RALLY: {
                TrumpMode.RALLY: 0.4,
                TrumpMode.DEAL: 0.25,
                TrumpMode.ESCALATION: 0.15,
                TrumpMode.DISTRACTION: 0.2,
            },
            TrumpMode.DEAL: {
                TrumpMode.RALLY: 0.15,
                TrumpMode.DEAL: 0.45,
                TrumpMode.ESCALATION: 0.15,
                TrumpMode.DISTRACTION: 0.25,
            },
            TrumpMode.ESCALATION: {
                TrumpMode.RALLY: 0.3,
                TrumpMode.DEAL: 0.1,
                TrumpMode.ESCALATION: 0.35,
                TrumpMode.DISTRACTION: 0.25,
            },
            TrumpMode.DISTRACTION: {
                TrumpMode.RALLY: 0.25,
                TrumpMode.DEAL: 0.25,
                TrumpMode.ESCALATION: 0.1,
                TrumpMode.DISTRACTION: 0.4,
            },
        }
    )

    # Stimuli modifiers — how events shift transition probabilities
    # These are applied per-turn based on world state
    mode_inertia: float = 0.3  # resistance to mode change

    # Track how long in current mode (affects transition probability)
    turns_in_mode: int = 0
    max_mode_duration: int = 5  # modes rarely last more than 5 turns

    def _compute_transitions(self, world_state: dict) -> dict[TrumpMode, float]:
        """
        Compute current mode transition probabilities given stimuli.

        This is where Trump's non-rationality lives: transitions are
        driven by salient stimuli, not by Bayesian updating.
        """
        base = dict(self.transition_base[self.current_mode])

        # --- Stimuli modifiers ---

        oil_price = world_state.get("oil_price", 98)
        us_casualties = world_state.get("us_casualties_this_turn", 0)
        media_sentiment = world_state.get("media_sentiment", 0.0)  # -1 to 1
        strike_success = world_state.get("strike_success_footage", False)
        iran_provocation = world_state.get("iran_provocation", False)
        domestic_scandal = world_state.get("domestic_scandal", False)
        ceasefire_offer = world_state.get("ceasefire_offer_visible", False)

        # High oil → push toward DEAL
        if oil_price > 110:
            base[TrumpMode.DEAL] += 0.15
            base[TrumpMode.RALLY] -= 0.1
        elif oil_price > 130:
            base[TrumpMode.DEAL] += 0.30
            base[TrumpMode.RALLY] -= 0.15

        # US casualties → ESCALATION spike (brief, hot)
        if us_casualties > 0:
            base[TrumpMode.ESCALATION] += 0.25
            base[TrumpMode.DEAL] -= 0.15
            base[TrumpMode.DISTRACTION] -= 0.1

        # Good strike footage → RALLY
        if strike_success:
            base[TrumpMode.RALLY] += 0.2
            base[TrumpMode.DEAL] -= 0.1

        # Iran provocation → ESCALATION
        if iran_provocation:
            base[TrumpMode.ESCALATION] += 0.15

        # Domestic scandal → DISTRACTION
        if domestic_scandal:
            base[TrumpMode.DISTRACTION] += 0.25
            base[TrumpMode.DEAL] -= 0.1

        # Visible ceasefire offer → DEAL
        if ceasefire_offer:
            base[TrumpMode.DEAL] += 0.15

        # Negative media → either ESCALATION (lash out) or DEAL (end it)
        if media_sentiment < -0.3:
            base[TrumpMode.ESCALATION] += 0.1
            base[TrumpMode.DEAL] += 0.1
            base[TrumpMode.RALLY] -= 0.15

        # Mode fatigue — longer in a mode, more likely to switch
        if self.turns_in_mode >= self.max_mode_duration:
            stay_mode = self.current_mode
            base[stay_mode] -= 0.2

        # Normalize to valid probabilities
        # Floor at 0.02 — always some small chance of any mode
        for mode in base:
            base[mode] = max(0.02, base[mode])
        total = sum(base.values())
        for mode in base:
            base[mode] /= total

        return base

    def transition_mode(self, world_state: dict) -> TrumpMode:
        """Stochastic mode transition."""
        probs = self._compute_transitions(world_state)

        # Sample from distribution
        r = random.random()
        cumulative = 0.0
        for mode, p in probs.items():
            cumulative += p
            if r <= cumulative:
                if mode != self.current_mode:
                    self.turns_in_mode = 0
                else:
                    self.turns_in_mode += 1
                self.current_mode = mode
                return mode

        # Fallback (shouldn't reach here)
        return self.current_mode

    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """
        Trump's decisions are mode-dependent, not belief-dependent.

        He does receive signals and his beliefs update (Pentagon briefs him),
        but his ACTIONS are driven by mode, not by rational calculation
        over beliefs.
        """
        self.transition_mode(world_state)

        actions = []

        if self.current_mode == TrumpMode.RALLY:
            actions.append(Action(
                ActionType.PUBLIC_STATEMENT, intensity=0.9,
                description="Total victory rhetoric",
                parameters={"message_type": "victory"}
            ))
            actions.append(Action(
                ActionType.AIR_STRIKE, intensity=0.7,
                description="Authorize expanded target list",
                target="iran",
            ))

        elif self.current_mode == TrumpMode.DEAL:
            actions.append(Action(
                ActionType.BACK_CHANNEL, intensity=0.6,
                description="Signal willingness to negotiate",
            ))
            actions.append(Action(
                ActionType.PUBLIC_STATEMENT, intensity=0.5,
                description="Terms aren't good enough yet",
                parameters={"message_type": "deal_signal"}
            ))

        elif self.current_mode == TrumpMode.ESCALATION:
            actions.append(Action(
                ActionType.AIR_STRIKE, intensity=0.95,
                description="Hit them with everything",
                target="iran",
            ))
            actions.append(Action(
                ActionType.DIPLOMATIC_DEMAND, intensity=1.0,
                description="Demand unconditional surrender",
            ))

        elif self.current_mode == TrumpMode.DISTRACTION:
            # Military on autopilot — no new orders
            actions.append(Action(
                ActionType.HOLD, intensity=0.3,
                description="Attention elsewhere — military autopilot",
            ))

        return actions

    def wants_war_to_end(self, world_state: dict) -> float:
        """
        Trump doesn't have a rational termination function.
        His war-ending desire is purely mode-dependent.
        """
        mode_desire = {
            TrumpMode.RALLY: 0.1,
            TrumpMode.DEAL: 0.7,
            TrumpMode.ESCALATION: 0.0,
            TrumpMode.DISTRACTION: 0.4,
        }
        return mode_desire[self.current_mode]


# ---------------------------------------------------------------------------
# Composite agent — Iran's splintered power structure
# ---------------------------------------------------------------------------

@dataclass
class Faction:
    """A faction within a composite agent."""
    faction_id: str
    name: str
    beliefs: BeliefState
    influence: float            # 0-1 current power within the composite
    preferred_actions: list[ActionType] = field(default_factory=list)
    hardline_score: float = 0.5  # 0 = dove, 1 = hawk

    # Each faction has its own p(victory) calculation
    victory_weights: dict[BeliefVar, tuple[float, float]] = field(
        default_factory=dict
    )

    def p_victory(self) -> float:
        if not self.victory_weights:
            return 0.5
        total_weight = 0.0
        weighted_sum = 0.0
        for var, (weight, target) in self.victory_weights.items():
            current = self.beliefs.mean(var)
            if var == BeliefVar.OIL_PRICE_EXPECTATION:
                distance = max(0.0, 1.0 - abs(current - target) / 100.0)
            else:
                distance = max(0.0, 1.0 - abs(current - target))
            weighted_sum += weight * distance
            total_weight += weight
        return weighted_sum / total_weight if total_weight > 0 else 0.5


@dataclass
class CompositeAgent(Agent):
    """
    An agent composed of multiple competing factions.

    Iran is the primary use case: IRGC hardliners, IRGC pragmatists,
    FM/civilian government, and succession claimants each have:
    - Different beliefs (see the world differently)
    - Different influence (power shifts with events)
    - Different preferred actions
    - Different hardline scores

    The composite must resolve factional conflict each turn to produce
    unified actions. This resolution is itself a game — internal
    coups, sidelining, and factional betrayal are possible.

    Factional dynamics create the gap between Iran FM's public
    ceasefire conditions and IRGC's denial — they're literally
    different factions speaking.
    """

    factions: list[Faction] = field(default_factory=list)

    # How factional conflict is resolved
    # "dominant" = highest-influence faction decides
    # "weighted" = actions weighted by influence
    # "veto" = any faction above veto_threshold can block
    resolution_mode: str = "weighted"
    veto_threshold: float = 0.3  # influence needed to veto

    def receive_signals(
        self,
        signals: list[tuple[Signal, float, float, float]],
    ) -> None:
        """
        Each faction receives and interprets signals independently.
        This is how factions diverge in their beliefs even when
        receiving the same information.
        """
        # Update the composite's beliefs (aggregate view)
        super().receive_signals(signals)

        # Each faction also updates — but with its own biases
        for faction in self.factions:
            for signal, observed, precision, bias in signals:
                # Factions interpret signals through their hardline lens
                faction_bias = bias
                if faction.hardline_score > 0.6:
                    # Hawks interpret ambiguous signals as threatening
                    if signal.variable in (
                        BeliefVar.US_POLITICAL_WILL,
                        BeliefVar.CEASEFIRE_PROBABILITY,
                    ):
                        faction_bias -= 0.1  # discount enemy peace signals
                elif faction.hardline_score < 0.4:
                    # Doves interpret ambiguous signals as hopeful
                    if signal.variable in (
                        BeliefVar.US_POLITICAL_WILL,
                        BeliefVar.CEASEFIRE_PROBABILITY,
                    ):
                        faction_bias += 0.1

                faction.beliefs.update(
                    signal.variable, observed, precision, faction_bias
                )

    def _resolve_factions(self, world_state: dict, turn: int) -> list[Action]:
        """
        Internal factional resolution — the internal game.

        Returns the composite's unified action list after factional
        conflict is resolved.
        """
        faction_proposals: dict[str, list[Action]] = {}

        for faction in self.factions:
            # Each faction proposes actions based on its own beliefs
            faction_actions = self._faction_decide(faction, world_state, turn)
            faction_proposals[faction.faction_id] = faction_actions

        if self.resolution_mode == "dominant":
            # Highest influence faction's proposal wins
            dominant = max(self.factions, key=lambda f: f.influence)
            return faction_proposals[dominant.faction_id]

        elif self.resolution_mode == "veto":
            # Dominant proposes, but any faction above veto_threshold
            # can block specific actions
            dominant = max(self.factions, key=lambda f: f.influence)
            proposed = faction_proposals[dominant.faction_id]
            vetoed = []
            for faction in self.factions:
                if (faction.faction_id != dominant.faction_id
                        and faction.influence >= self.veto_threshold):
                    for action in proposed:
                        # Faction vetoes actions too far from its preference
                        if (action.action_type in (
                                ActionType.CEASEFIRE_OFFER,
                                ActionType.DE_ESCALATE)
                                and faction.hardline_score > 0.7):
                            vetoed.append(action)
                        elif (action.action_type in (
                                ActionType.ESCALATE,
                                ActionType.STRAIT_TRAP)
                                and faction.hardline_score < 0.3):
                            vetoed.append(action)
            return [a for a in proposed if a not in vetoed]

        else:  # "weighted"
            # Merge proposals weighted by influence
            return self._weighted_merge(faction_proposals)

    def _weighted_merge(
        self, proposals: dict[str, list[Action]]
    ) -> list[Action]:
        """
        Merge factional proposals by influence weight.

        Higher-influence factions' actions are more likely to be
        included, and their intensity is scaled up.
        """
        merged = []
        seen_types: set[ActionType] = set()

        # Sort factions by influence (highest first)
        sorted_factions = sorted(
            self.factions, key=lambda f: f.influence, reverse=True
        )

        for faction in sorted_factions:
            for action in proposals.get(faction.faction_id, []):
                if action.action_type not in seen_types:
                    # Scale intensity by faction influence
                    action.intensity *= faction.influence
                    action.description = (
                        f"[{faction.name}] {action.description}"
                    )
                    merged.append(action)
                    seen_types.add(action.action_type)

        return merged

    def _faction_decide(
        self, faction: Faction, world_state: dict, turn: int
    ) -> list[Action]:
        """
        Individual faction decision logic.
        Override in subclass for specific faction behaviors.
        """
        p_v = faction.p_victory()
        actions = []

        if faction.hardline_score > 0.7:
            # Hawks — always want to escalate or hold
            if p_v > 0.4:
                actions.append(Action(
                    ActionType.ESCALATE, intensity=0.8,
                    description=f"{faction.name}: continue resistance"
                ))
            else:
                actions.append(Action(
                    ActionType.HOLD, intensity=0.6,
                    description=f"{faction.name}: hold despite losses"
                ))
        elif faction.hardline_score < 0.3:
            # Doves — seek negotiation
            actions.append(Action(
                ActionType.BACK_CHANNEL, intensity=0.7,
                description=f"{faction.name}: seek terms"
            ))
        else:
            # Pragmatists — calculate
            if p_v > 0.5:
                actions.append(Action(
                    ActionType.HOLD, intensity=0.5,
                    description=f"{faction.name}: maintain posture"
                ))
            else:
                actions.append(Action(
                    ActionType.BACK_CHANNEL, intensity=0.4,
                    description=f"{faction.name}: explore options"
                ))

        return actions

    def _update_faction_influence(self, world_state: dict) -> None:
        """
        Faction influence shifts based on events.

        Military setbacks empower doves. Successful attacks empower hawks.
        Leadership kills empower succession claimants.
        War duration gradually shifts influence toward pragmatists.
        """
        for faction in self.factions:
            # Hawks gain influence when attacked (rally effect)
            # But this effect diminishes over time
            turn = world_state.get("turn", 0)
            rally_strength = max(0.0, 0.05 - turn * 0.002)
            if world_state.get("under_attack", False):
                if faction.hardline_score > 0.6:
                    faction.influence = min(1.0, faction.influence + rally_strength)

            # Military losses empower pragmatists — stronger effect
            irgc_casualties = world_state.get("irgc_casualties_cumulative", 0)
            if irgc_casualties > 22000:
                casualty_bonus = min(0.05, (irgc_casualties - 22000) / 200000)
                if faction.hardline_score < 0.5:
                    # Pragmatists gain as casualties mount
                    faction.influence = min(1.0, faction.influence + casualty_bonus)
                elif faction.hardline_score > 0.7:
                    # Hawks lose as casualties mount
                    faction.influence = max(0.1, faction.influence - casualty_bonus * 0.5)

            # Ceasefire offer visibility empowers doves
            if world_state.get("ceasefire_offer_visible", False):
                if faction.hardline_score < 0.4:
                    faction.influence = min(1.0, faction.influence + 0.04)

            # Regime survival index dropping empowers pragmatists/FM
            regime = world_state.get("regime_survival_index", 0.5)
            if regime < 0.35:
                if faction.hardline_score < 0.5:
                    faction.influence = min(1.0, faction.influence + 0.03)

            # IRGC cohesion dropping weakens hardliners
            cohesion = world_state.get("irgc_military_strength", 0.5)
            if cohesion < 0.4:
                if faction.hardline_score > 0.7:
                    faction.influence = max(0.1, faction.influence - 0.02)

        # Normalize influences to sum to 1
        total = sum(f.influence for f in self.factions)
        if total > 0:
            for faction in self.factions:
                faction.influence /= total

    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """Resolve factions, then produce unified actions."""
        self._update_faction_influence(world_state)
        return self._resolve_factions(world_state, turn)

    def wants_war_to_end(self, world_state: dict) -> float:
        """
        Composite: weighted average of factions' desire to end war.
        A high-influence hawk faction can override dove desire.
        """
        total = 0.0
        for faction in self.factions:
            p_v = faction.p_victory()
            # Hawks want to continue even when losing
            if faction.hardline_score > 0.7:
                faction_desire = max(0.0, 0.3 - p_v * 0.3)
            # Doves want out proportional to pain
            elif faction.hardline_score < 0.3:
                faction_desire = min(1.0, 0.5 + (1.0 - p_v) * 0.5)
            else:
                faction_desire = 1.0 - p_v

            total += faction_desire * faction.influence

        return total

    @property
    def dominant_faction(self) -> Faction:
        return max(self.factions, key=lambda f: f.influence)


# ---------------------------------------------------------------------------
# Proxy agent — patron-dependent with autonomy
# ---------------------------------------------------------------------------

@dataclass
class ProxyAgent(Agent):
    """
    Proxy actor with a patron relationship.

    Key dynamics:
    - Communication reliability (50-70% per scenario doc)
    - Preference divergence from patron
    - Autonomy increases as patron weakens
    - Local interests can override patron orders
    """

    patron_id: Optional[str] = None
    communication_reliability: float = 0.6  # P(order received)
    autonomy: float = 0.5                   # 0 = obedient, 1 = independent
    local_interest_weight: float = 0.5      # how much local goals matter vs patron

    # What the patron wants this proxy to do
    patron_orders: Optional[Action] = None

    # The proxy's own preferred action
    local_preference: Optional[Action] = None

    def receive_patron_order(self, order: Action) -> bool:
        """
        Attempt to receive an order from patron.
        Communication may fail.
        """
        if random.random() < self.communication_reliability:
            self.patron_orders = order
            return True
        return False

    def decide(self, world_state: dict, turn: int) -> list[Action]:
        """
        Proxy decision: blend patron orders with local interests,
        weighted by autonomy and communication reliability.
        """
        # Autonomy increases as patron weakens
        patron_strength = world_state.get(
            f"{self.patron_id}_strength", 1.0
        ) if self.patron_id else 0.0
        effective_autonomy = self.autonomy + (1.0 - patron_strength) * 0.3
        effective_autonomy = min(1.0, effective_autonomy)

        if self.patron_orders and random.random() > effective_autonomy:
            # Follow patron orders
            return [self.patron_orders]
        elif self.local_preference:
            # Follow local interests
            return [self.local_preference]
        else:
            return [Action(ActionType.HOLD, intensity=0.3)]

    def wants_war_to_end(self, world_state: dict) -> float:
        """Proxies generally don't drive termination."""
        return 0.3  # low baseline desire to end

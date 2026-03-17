"""
Simulation engine — the main loop.

Turn sequence (each turn = ~2 days):
  1. OBSERVE: deliver signals to agents (imperfect, lagged, noisy)
  2. INTERNAL: composite agents resolve factional debates
  3. DECIDE: all agents select actions independently
  4. EXECUTE: actions resolve, generate new signals
  5. MARKET: oil market, shipping, insurance update
  6. ESCALATE: escalation level recomputed (emergent)
  7. TERMINATE: check termination conditions
  8. RANDOM: stochastic events
  9. REPORT: turn summary
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from .beliefs import BeliefVar, BetaBelief, GaussianBelief
from .signals import InfoEnvironment, Signal, SignalType, SignalAccess
from .agents import Agent, Action, ActionType, CompositeAgent, StochasticAgent, ProxyAgent
from .escalation import EscalationState
from .termination import TerminationState, TerminationOutcome
from .oil_market import OilMarket, InsuranceMarket
from .scenario import create_agents


# ---------------------------------------------------------------------------
# Ground truth — the actual state of the world
# ---------------------------------------------------------------------------

@dataclass
class GroundTruth:
    """
    The actual state of the world. Agents don't see this directly —
    they see noisy signals about it.
    """

    # Leadership
    mojtaba_alive: float = 0.5          # genuinely unknown even to us
    irgc_cohesion: float = 0.55

    # Military stocks (0-1 fraction remaining)
    iran_missile_stocks: float = 0.45
    iran_drone_stocks: float = 0.55
    israel_interceptor_stocks: float = 0.25   # critically low but not empty
    us_pgm_stocks: float = 0.6

    # Capability
    iran_nuclear_progress: float = 0.4
    iran_cyber_capability: float = 0.7       # intact, held back
    fordow_destroyed: float = 0.3            # probably not fully destroyed
    kharg_terminal_damaged: float = 0.6      # heavily struck but uncertain

    # External
    russia_supplying_iran: float = 0.65      # probably yes
    china_willing_to_guarantee: float = 0.4

    # Political
    us_political_will: float = 0.55
    israel_will_to_continue: float = 0.75

    # Proxy
    houthi_activation_prob: float = 0.25     # restraint mode
    hezbollah_full_war_prob: float = 0.15

    # Uprising
    uprising_intensity: float = 0.7
    uprising_irgc_drain: float = 0.15

    # Casualties
    irgc_casualties_cumulative: int = 21000
    uprising_casualties_cumulative: int = 60514

    # Regime survival composite index
    regime_survival_index: float = 0.45

    def to_dict(self) -> dict:
        """JSON-serializable representation."""
        return {
            "mojtaba_alive": self.mojtaba_alive,
            "irgc_cohesion": self.irgc_cohesion,
            "iran_missile_stocks": self.iran_missile_stocks,
            "iran_drone_stocks": self.iran_drone_stocks,
            "israel_interceptor_stocks": self.israel_interceptor_stocks,
            "us_pgm_stocks": self.us_pgm_stocks,
            "iran_nuclear_progress": self.iran_nuclear_progress,
            "iran_cyber_capability": self.iran_cyber_capability,
            "fordow_destroyed": self.fordow_destroyed,
            "kharg_terminal_damaged": self.kharg_terminal_damaged,
            "russia_supplying_iran": self.russia_supplying_iran,
            "china_willing_to_guarantee": self.china_willing_to_guarantee,
            "us_political_will": self.us_political_will,
            "israel_will_to_continue": self.israel_will_to_continue,
            "houthi_activation_prob": self.houthi_activation_prob,
            "hezbollah_full_war_prob": self.hezbollah_full_war_prob,
            "uprising_intensity": self.uprising_intensity,
            "uprising_irgc_drain": self.uprising_irgc_drain,
            "irgc_casualties_cumulative": self.irgc_casualties_cumulative,
            "uprising_casualties_cumulative": self.uprising_casualties_cumulative,
            "regime_survival_index": self.regime_survival_index,
        }

    def as_dict(self) -> dict[BeliefVar, float]:
        """Map to BeliefVar for comparison with agent beliefs."""
        return {
            BeliefVar.MOJTABA_ALIVE: self.mojtaba_alive,
            BeliefVar.IRGC_COHESION: self.irgc_cohesion,
            BeliefVar.IRAN_MISSILE_STOCKS: self.iran_missile_stocks,
            BeliefVar.IRAN_DRONE_STOCKS: self.iran_drone_stocks,
            BeliefVar.ISRAEL_INTERCEPTOR_STOCKS: self.israel_interceptor_stocks,
            BeliefVar.US_PGM_STOCKS: self.us_pgm_stocks,
            BeliefVar.IRAN_NUCLEAR_PROGRESS: self.iran_nuclear_progress,
            BeliefVar.IRAN_CYBER_CAPABILITY: self.iran_cyber_capability,
            BeliefVar.FORDOW_DESTROYED: self.fordow_destroyed,
            BeliefVar.KHARG_TERMINAL_DAMAGED: self.kharg_terminal_damaged,
            BeliefVar.RUSSIA_SUPPLYING_IRAN: self.russia_supplying_iran,
            BeliefVar.CHINA_WILLING_TO_GUARANTEE: self.china_willing_to_guarantee,
            BeliefVar.US_POLITICAL_WILL: self.us_political_will,
            BeliefVar.ISRAEL_WILL_TO_CONTINUE: self.israel_will_to_continue,
            BeliefVar.HOUTHI_ACTIVATION_PROB: self.houthi_activation_prob,
            BeliefVar.HEZBOLLAH_FULL_WAR_PROB: self.hezbollah_full_war_prob,
            BeliefVar.UPRISING_INTENSITY: self.uprising_intensity,
            BeliefVar.UPRISING_IRGC_DRAIN: self.uprising_irgc_drain,
        }


# ---------------------------------------------------------------------------
# Random events
# ---------------------------------------------------------------------------

@dataclass
class RandomEvent:
    name: str
    probability: float
    effects: dict  # keys are ground truth fields to modify
    signals: list[Signal] = field(default_factory=list)
    description: str = ""


def generate_random_events(turn: int, ground_truth: GroundTruth) -> list[RandomEvent]:
    """Define possible random events with probabilities per turn."""
    events = [
        RandomEvent(
            name="mojtaba_surfaces",
            probability=0.03,
            effects={"mojtaba_alive": 0.95},
            description="Mojtaba Khamenei surfaces publicly",
        ),
        RandomEvent(
            name="mojtaba_confirmed_dead",
            probability=0.02,
            effects={"mojtaba_alive": 0.05},
            description="Mojtaba Khamenei confirmed dead",
        ),
        RandomEvent(
            name="chinese_vessel_hit",
            probability=0.02,
            effects={"china_willing_to_guarantee": -0.2},
            description="Accidental strike on Chinese-flagged vessel",
        ),
        RandomEvent(
            name="interceptor_stockpile_critical",
            probability=0.05 if ground_truth.israel_interceptor_stocks < 0.15 else 0.01,
            effects={"israel_interceptor_stocks": -0.1},
            description="Israeli interceptor stocks hit critical low",
        ),
        RandomEvent(
            name="mass_casualty_gulf",
            probability=0.04,
            effects={"regime_survival_index": -0.05},
            description="Iranian missile hits populated Gulf city center",
        ),
        RandomEvent(
            name="us_aircraft_lost",
            probability=0.03,
            effects={"us_political_will": -0.1},
            description="US aircraft lost with crew casualties",
        ),
        RandomEvent(
            name="cyber_attack_gulf",
            probability=0.03,
            effects={"iran_cyber_capability": -0.3},
            description="IRGC cyber attack on Gulf desalination plant",
        ),
        RandomEvent(
            name="russian_supply_exposed",
            probability=0.04,
            effects={"russia_supplying_iran": 0.95},
            description="Russian supply ship intercepted — co-belligerency exposed",
        ),
        RandomEvent(
            name="turkey_hit_casualties",
            probability=0.02,
            effects={},  # handled specially — Article 5
            description="Turkish base hit again WITH casualties",
        ),
        RandomEvent(
            name="houthi_activate",
            probability=0.05 if ground_truth.houthi_activation_prob > 0.4 else 0.02,
            effects={"houthi_activation_prob": 0.9},
            description="Houthis begin Red Sea attacks",
        ),
        RandomEvent(
            name="nuclear_signal",
            probability=0.02,
            effects={"iran_nuclear_progress": 0.8},
            description="Iranian nuclear breakout signal detected",
        ),
        RandomEvent(
            name="uprising_breakthrough",
            probability=0.03 if ground_truth.uprising_intensity > 0.7 else 0.01,
            effects={"uprising_intensity": 0.9, "irgc_cohesion": -0.15},
            description="Major Iranian city uprising overwhelms IRGC control",
        ),
        RandomEvent(
            name="friendly_fire",
            probability=0.02,
            effects={"us_political_will": -0.05},
            description="Coalition friendly fire incident",
        ),
        RandomEvent(
            name="backchannel_leak",
            probability=0.03,
            effects={},
            description="Intelligence leak reveals back-channel deal terms",
        ),
        RandomEvent(
            name="kharg_confirmed_destroyed",
            probability=0.04 if ground_truth.kharg_terminal_damaged > 0.5 else 0.01,
            effects={"kharg_terminal_damaged": 0.95},
            description="Kharg Island oil terminal confirmed destroyed",
        ),
    ]
    return events


def resolve_random_events(
    turn: int,
    ground_truth: GroundTruth,
    info_env: InfoEnvironment,
) -> list[RandomEvent]:
    """Roll for random events and apply effects."""
    possible = generate_random_events(turn, ground_truth)
    occurred = []

    for event in possible:
        if random.random() < event.probability:
            # Apply effects to ground truth
            for attr, value in event.effects.items():
                current = getattr(ground_truth, attr, None)
                if current is not None:
                    if value < 0:
                        # Negative = relative decrease
                        setattr(ground_truth, attr, max(0.0, current + value))
                    elif value > 0.8:
                        # High absolute values = set directly
                        setattr(ground_truth, attr, value)
                    else:
                        # Moderate = blend toward value
                        setattr(ground_truth, attr, current * 0.5 + value * 0.5)

            # Generate signal about the event
            for var, value in event.effects.items():
                bvar = _attr_to_belief_var(var)
                if bvar:
                    signal = Signal(
                        variable=bvar,
                        true_value=getattr(ground_truth, var, 0.5),
                        signal_type=SignalType.MILITARY_ACTION,
                        precision=0.7,
                        description=event.description,
                    )
                    info_env.emit_signal(signal, turn)

            occurred.append(event)

    return occurred


def _attr_to_belief_var(attr: str) -> Optional[BeliefVar]:
    """Map ground truth attribute names to BeliefVar enum."""
    mapping = {
        "mojtaba_alive": BeliefVar.MOJTABA_ALIVE,
        "irgc_cohesion": BeliefVar.IRGC_COHESION,
        "iran_missile_stocks": BeliefVar.IRAN_MISSILE_STOCKS,
        "iran_drone_stocks": BeliefVar.IRAN_DRONE_STOCKS,
        "israel_interceptor_stocks": BeliefVar.ISRAEL_INTERCEPTOR_STOCKS,
        "us_pgm_stocks": BeliefVar.US_PGM_STOCKS,
        "iran_nuclear_progress": BeliefVar.IRAN_NUCLEAR_PROGRESS,
        "iran_cyber_capability": BeliefVar.IRAN_CYBER_CAPABILITY,
        "fordow_destroyed": BeliefVar.FORDOW_DESTROYED,
        "kharg_terminal_damaged": BeliefVar.KHARG_TERMINAL_DAMAGED,
        "russia_supplying_iran": BeliefVar.RUSSIA_SUPPLYING_IRAN,
        "china_willing_to_guarantee": BeliefVar.CHINA_WILLING_TO_GUARANTEE,
        "us_political_will": BeliefVar.US_POLITICAL_WILL,
        "israel_will_to_continue": BeliefVar.ISRAEL_WILL_TO_CONTINUE,
        "houthi_activation_prob": BeliefVar.HOUTHI_ACTIVATION_PROB,
        "hezbollah_full_war_prob": BeliefVar.HEZBOLLAH_FULL_WAR_PROB,
        "uprising_intensity": BeliefVar.UPRISING_INTENSITY,
        "uprising_irgc_drain": BeliefVar.UPRISING_IRGC_DRAIN,
        "regime_survival_index": BeliefVar.REGIME_SURVIVAL_PROB,
    }
    return mapping.get(attr)


# ---------------------------------------------------------------------------
# World state — the aggregate view passed to agents
# ---------------------------------------------------------------------------

def build_world_state(
    ground_truth: GroundTruth,
    oil_market: OilMarket,
    escalation: EscalationState,
    turn: int,
    day: int | None = None,
) -> dict:
    """Build the world state dict from current conditions."""
    return {
        "turn": turn,
        "day": day if day is not None else 18 + turn * 2,
        "oil_price": oil_market.price,
        "escalation_level": escalation.level,
        "escalation_phase": escalation.phase,
        "strait_flow": oil_market.strait.overall_flow,
        "red_sea_flow": oil_market.red_sea.flow,
        "israel_interceptor_fraction": ground_truth.israel_interceptor_stocks,
        "regime_survival_index": ground_truth.regime_survival_index,
        "irgc_casualties_cumulative": ground_truth.irgc_casualties_cumulative,
        "uprising_casualties_cumulative": ground_truth.uprising_casualties_cumulative,
        "under_attack": True,  # war is ongoing
        "ceasefire_offer_visible": False,  # updated by agent actions
        "us_casualties_this_turn": 0,
        "strike_success_footage": False,
        "iran_provocation": False,
        "domestic_scandal": random.random() < 0.1,  # 10% chance per turn
        "media_sentiment": random.gauss(0, 0.3),
        "us_support_to_israel": ground_truth.us_political_will,
        "iran_missiles": ground_truth.iran_missile_stocks,
        "irgc_military_strength": ground_truth.irgc_cohesion,
    }


# ---------------------------------------------------------------------------
# Action resolution — translate actions into ground truth changes
# ---------------------------------------------------------------------------

def resolve_actions(
    all_actions: list[tuple[str, Action]],
    ground_truth: GroundTruth,
    oil_market: OilMarket,
    info_env: InfoEnvironment,
    world_state: dict,
    turn: int,
) -> None:
    """
    Resolve all agent actions for this turn.
    Modify ground truth, generate signals.
    """
    for agent_id, action in all_actions:
        if action.action_type == ActionType.MISSILE_STRIKE:
            _resolve_missile_strike(agent_id, action, ground_truth, info_env, turn)
        elif action.action_type == ActionType.AIR_STRIKE:
            _resolve_air_strike(agent_id, action, ground_truth, info_env, turn)
        elif action.action_type == ActionType.DRONE_STRIKE:
            _resolve_drone_strike(agent_id, action, ground_truth, info_env, turn)
        elif action.action_type == ActionType.STRAIT_TIGHTEN:
            oil_market.strait.western_flow = max(0.0, oil_market.strait.western_flow - 0.1)
            oil_market.strait.gulf_state_flow = max(0.0, oil_market.strait.gulf_state_flow - 0.1)
        elif action.action_type == ActionType.STRAIT_LOOSEN:
            oil_market.strait.western_flow = min(1.0, oil_market.strait.western_flow + 0.1)
        elif action.action_type == ActionType.STRAIT_TRAP:
            oil_market.strait.trap_mode = True
        elif action.action_type == ActionType.PROXY_ACTIVATE:
            if action.target == "houthis":
                ground_truth.houthi_activation_prob = min(
                    1.0, ground_truth.houthi_activation_prob + 0.3
                )
                if ground_truth.houthi_activation_prob > 0.7:
                    oil_market.red_sea.activate_houthis()
        elif action.action_type == ActionType.CEASEFIRE_OFFER:
            world_state["ceasefire_offer_visible"] = True
            info_env.emit_signal(Signal(
                variable=BeliefVar.CEASEFIRE_PROBABILITY,
                true_value=0.5,
                signal_type=SignalType.DIPLOMATIC_ACTION,
                description=f"{agent_id} offers ceasefire",
            ), turn)
        elif action.action_type == ActionType.BACK_CHANNEL:
            # Subtle signal — only some agents see it
            info_env.emit_signal(Signal(
                variable=BeliefVar.CEASEFIRE_PROBABILITY,
                true_value=0.4,
                signal_type=SignalType.DIPLOMATIC_ACTION,
                precision=0.3,  # less visible than public offer
                recipients=_backchannel_recipients(agent_id),
                description=f"{agent_id} back-channel signal",
            ), turn)
        elif action.action_type == ActionType.INTERNAL_CRACKDOWN:
            ground_truth.uprising_intensity = max(
                0.1, ground_truth.uprising_intensity - action.intensity * 0.05
            )
            ground_truth.uprising_irgc_drain = min(
                0.4, ground_truth.uprising_irgc_drain + 0.02
            )
        elif action.action_type == ActionType.PROTEST_ESCALATE:
            ground_truth.uprising_intensity = min(
                1.0, ground_truth.uprising_intensity + action.intensity * 0.03
            )
            ground_truth.uprising_casualties_cumulative += int(
                action.intensity * 500
            )
        elif action.action_type == ActionType.PUBLIC_STATEMENT:
            _resolve_public_statement(agent_id, action, info_env, turn)


def _resolve_missile_strike(
    agent_id: str, action: Action,
    gt: GroundTruth, info_env: InfoEnvironment, turn: int,
) -> None:
    """Iranian missile strikes — attrit Israeli interceptors."""
    if agent_id in ("irgc_military", "iran_composite"):
        # Each strike drains Iranian stocks and Israeli interceptors
        gt.iran_missile_stocks = max(0.0, gt.iran_missile_stocks - action.intensity * 0.015)
        gt.israel_interceptor_stocks = max(0.0, gt.israel_interceptor_stocks - action.intensity * 0.006)
        gt.irgc_cohesion = max(0.1, gt.irgc_cohesion - 0.005)  # operational cost

        # Signal: missile launch is visible to everyone
        info_env.emit_signal(Signal(
            variable=BeliefVar.IRAN_MISSILE_STOCKS,
            true_value=gt.iran_missile_stocks,
            signal_type=SignalType.MILITARY_ACTION,
            precision=0.4,  # observers can't count exact stocks
            description="Iranian missile launch",
        ), turn)
        info_env.emit_signal(Signal(
            variable=BeliefVar.ISRAEL_INTERCEPTOR_STOCKS,
            true_value=gt.israel_interceptor_stocks,
            signal_type=SignalType.MILITARY_ACTION,
            precision=0.3,  # interceptions visible but stock unknown
            description="Interceptor engagement",
        ), turn)


def _resolve_air_strike(
    agent_id: str, action: Action,
    gt: GroundTruth, info_env: InfoEnvironment, turn: int,
) -> None:
    """US/Israeli air strikes — degrade Iranian capabilities."""
    if agent_id in ("us_trump", "pentagon", "idf", "israel"):
        gt.us_pgm_stocks = max(0.0, gt.us_pgm_stocks - action.intensity * 0.02)
        gt.irgc_cohesion = max(0.1, gt.irgc_cohesion - action.intensity * 0.03)
        gt.irgc_casualties_cumulative += int(action.intensity * 300)

        # Probabilistic target destruction
        if random.random() < action.intensity * 0.3:
            gt.iran_missile_stocks = max(0.0, gt.iran_missile_stocks - 0.05)
        if random.random() < action.intensity * 0.2:
            gt.iran_drone_stocks = max(0.0, gt.iran_drone_stocks - 0.05)
        if random.random() < action.intensity * 0.1:
            gt.fordow_destroyed = min(1.0, gt.fordow_destroyed + 0.1)

        # Signal: strike is high-visibility
        info_env.emit_signal(Signal(
            variable=BeliefVar.IRGC_COHESION,
            true_value=gt.irgc_cohesion,
            signal_type=SignalType.MILITARY_ACTION,
            description=f"{agent_id} air strike on Iran",
        ), turn)

        # Satellite imagery — lagged
        info_env.emit_signal(Signal(
            variable=BeliefVar.IRAN_MISSILE_STOCKS,
            true_value=gt.iran_missile_stocks,
            signal_type=SignalType.SATELLITE_IMAGERY,
            lag=1,  # ~2 days in turn-time (less than 3 real days)
            precision=0.7,
            description="BDA satellite imagery",
        ), turn)


def _resolve_drone_strike(
    agent_id: str, action: Action,
    gt: GroundTruth, info_env: InfoEnvironment, turn: int,
) -> None:
    """Drone strikes — lower cost but lower impact."""
    if agent_id in ("irgc_military", "iran_composite", "kh_pmf"):
        gt.iran_drone_stocks = max(0.0, gt.iran_drone_stocks - action.intensity * 0.01)
        # Possible US casualties from proxy drones
        if agent_id == "kh_pmf" and random.random() < action.intensity * 0.15:
            gt.us_political_will = max(0.1, gt.us_political_will - 0.05)
            info_env.emit_signal(Signal(
                variable=BeliefVar.US_POLITICAL_WILL,
                true_value=gt.us_political_will,
                signal_type=SignalType.CASUALTY_REPORT,
                description="US casualties from proxy drone attack",
            ), turn)


def _resolve_public_statement(
    agent_id: str, action: Action,
    info_env: InfoEnvironment, turn: int,
) -> None:
    """Public statements — cheap talk, low precision, high volume."""
    msg_type = action.parameters.get("message_type", "generic")
    if msg_type == "victory":
        info_env.emit_signal(Signal(
            variable=BeliefVar.US_POLITICAL_WILL,
            true_value=0.8,  # projects strength
            signal_type=SignalType.PUBLIC_STATEMENT,
            bias=0.3,  # inflated
            description=f"{agent_id}: victory rhetoric",
        ), turn)
    elif msg_type == "deal_signal":
        info_env.emit_signal(Signal(
            variable=BeliefVar.CEASEFIRE_PROBABILITY,
            true_value=0.4,
            signal_type=SignalType.PUBLIC_STATEMENT,
            description=f"{agent_id}: deal signaling",
        ), turn)


def _backchannel_recipients(agent_id: str) -> list[str]:
    """Who can see back-channel signals from a given agent."""
    channels = {
        "us_trump": ["iran_composite", "china", "turkey"],
        "iran_composite": ["us_trump", "china", "turkey", "russia"],
        "china": ["us_trump", "iran_composite", "saudi"],
        "turkey": ["us_trump", "iran_composite", "china"],
        "saudi": ["iran_composite", "china", "uae"],
        "uae": ["iran_composite", "saudi", "china"],
    }
    return channels.get(agent_id, [])


# ---------------------------------------------------------------------------
# Ground truth drift — the world changes even without agent actions
# ---------------------------------------------------------------------------

def drift_ground_truth(gt: GroundTruth, turn: int) -> None:
    """
    Natural drift in ground truth each turn.
    Stocks deplete, fatigue accumulates, uprising evolves.
    """
    # Interceptors drain slightly from ongoing Iranian launches
    gt.israel_interceptor_stocks = max(
        0.0, gt.israel_interceptor_stocks - 0.002
    )

    # Emergency interceptor resupply — $825M procurement
    # Starts arriving around turn 15 (~30 days), ramps up
    if turn >= 15:
        resupply_rate = min(0.008, (turn - 15) * 0.001)
        gt.israel_interceptor_stocks = min(
            0.8, gt.israel_interceptor_stocks + resupply_rate
        )

    # Iran's missile stocks slowly deplete
    gt.iran_missile_stocks = max(0.0, gt.iran_missile_stocks - 0.003)

    # But drone production continues (underground facilities)
    gt.iran_drone_stocks = min(1.0, gt.iran_drone_stocks + 0.01)

    # Russian resupply (if happening) offsets some depletion
    if gt.russia_supplying_iran > 0.5:
        gt.iran_drone_stocks = min(1.0, gt.iran_drone_stocks + 0.005)
        gt.iran_missile_stocks = min(1.0, gt.iran_missile_stocks + 0.002)

    # IRGC cohesion slowly degrades under sustained pressure
    gt.irgc_cohesion = max(0.1, gt.irgc_cohesion - 0.005)

    # Uprising casualties continue
    gt.uprising_casualties_cumulative += random.randint(100, 500)

    # Regime survival index is composite
    gt.regime_survival_index = (
        gt.irgc_cohesion * 0.4
        + gt.iran_missile_stocks * 0.2
        + (1.0 - gt.uprising_intensity) * 0.2
        + gt.mojtaba_alive * 0.1
        + (1.0 - gt.uprising_irgc_drain) * 0.1
    )

    # US political will slowly declines
    gt.us_political_will = max(0.1, gt.us_political_will - 0.003)


# ---------------------------------------------------------------------------
# Turn report
# ---------------------------------------------------------------------------

@dataclass
class TurnReport:
    turn: int
    day: int
    actions: list[tuple[str, Action]]
    random_events: list[RandomEvent]
    oil_price: float
    escalation_level: float
    escalation_phase: str
    termination_status: str
    trump_mode: str
    iran_dominant_faction: str
    key_metrics: dict
    miscalculation_events: list[str]

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "day": self.day,
            "actions": [
                {"agent_id": aid, "action": a.to_dict()}
                for aid, a in self.actions
            ],
            "random_events": [
                {"name": e.name, "description": e.description}
                for e in self.random_events
            ],
            "oil_price": self.oil_price,
            "escalation_level": self.escalation_level,
            "escalation_phase": self.escalation_phase,
            "termination_status": self.termination_status,
            "trump_mode": self.trump_mode,
            "iran_dominant_faction": self.iran_dominant_faction,
            "key_metrics": self.key_metrics,
            "miscalculation_events": self.miscalculation_events,
        }

    def summary(self) -> str:
        lines = [
            f"=== Turn {self.turn} (Day {self.day}) ===",
            f"  Oil: ${self.oil_price:.1f}  Escalation: {self.escalation_level:.2f} ({self.escalation_phase})",
            f"  Trump mode: {self.trump_mode}  Iran dominant: {self.iran_dominant_faction}",
            f"  Status: {self.termination_status}",
        ]

        if self.random_events:
            lines.append("  Random events:")
            for e in self.random_events:
                lines.append(f"    * {e.description}")

        if self.miscalculation_events:
            lines.append("  Miscalculations:")
            for m in self.miscalculation_events[:3]:
                lines.append(f"    ! {m}")

        key_actions = [
            (aid, a) for aid, a in self.actions
            if a.action_type not in (ActionType.HOLD, ActionType.PUBLIC_STATEMENT)
        ]
        if key_actions:
            lines.append("  Key actions:")
            for aid, a in key_actions[:5]:
                lines.append(f"    > {aid}: {a.description or a.action_type.value}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

@dataclass
class Simulation:
    """The main simulation engine."""

    agents: dict[str, Agent] = field(default_factory=dict)
    ground_truth: GroundTruth = field(default_factory=GroundTruth)
    info_env: InfoEnvironment = field(default_factory=InfoEnvironment)
    oil_market: OilMarket = field(default_factory=OilMarket)
    insurance: InsuranceMarket = field(default_factory=InsuranceMarket)
    escalation: EscalationState = field(default_factory=EscalationState)
    termination: TerminationState = field(default_factory=TerminationState)

    turn: int = 0
    reports: list[TurnReport] = field(default_factory=list)

    # Variant configuration
    variant: str = "baseline"

    # Date anchoring
    start_day: int = 18  # Day of war when simulation begins
    start_date: str = "2026-03-15"  # Calendar date for turn 0

    @property
    def day(self) -> int:
        """Current day of war."""
        return self.start_day + self.turn * 2

    @property
    def calendar_date(self) -> str:
        """Current calendar date (ISO format)."""
        from datetime import date, timedelta
        base = date.fromisoformat(self.start_date)
        return (base + timedelta(days=self.turn * 2)).isoformat()

    def setup(
        self,
        variant: str = "baseline",
        max_turns: int = 120,
        start_day: int = 18,
        start_date: str = "2026-03-15",
    ) -> None:
        """Initialize the simulation with all agents and starting state."""
        self.variant = variant
        self.start_day = start_day
        self.start_date = start_date
        self.agents = create_agents()
        self.ground_truth = GroundTruth()
        self.info_env = InfoEnvironment()
        self.oil_market = OilMarket()
        self.insurance = InsuranceMarket()
        self.escalation = EscalationState()
        self.termination = TerminationState(max_turns=max_turns)
        self.turn = 0
        self.reports = []

        # Apply variant modifications
        self._apply_variant(variant)

    def _apply_variant(self, variant: str) -> None:
        """Apply scenario variant modifications."""
        if variant == "houthi_activation":
            self.ground_truth.houthi_activation_prob = 0.9
            self.oil_market.red_sea.activate_houthis()
        elif variant == "interceptor_crisis":
            self.ground_truth.israel_interceptor_stocks = 0.08
        elif variant == "mojtaba_surfaces":
            # Will trigger on turn 3
            pass
        elif variant == "russian_confirmed":
            self.ground_truth.russia_supplying_iran = 0.95
        elif variant == "uprising_breakthrough":
            # Will trigger on turn 4
            pass
        elif variant == "chinese_carrier":
            self.ground_truth.china_willing_to_guarantee = 0.7
        elif variant == "strait_trap":
            self.oil_market.strait.trap_mode = True

    def step(self) -> TurnReport:
        """Execute one turn of the simulation."""
        self.turn += 1

        # 1. Build world state
        world_state = build_world_state(
            self.ground_truth, self.oil_market, self.escalation, self.turn,
            day=self.day,
        )

        # 2. Generate ambient signals from ground truth
        self._emit_ambient_signals()

        # 3. Deliver signals to agents
        agent_access = {
            aid: (agent, agent.signal_access)
            for aid, agent in self.agents.items()
        }
        deliveries = self.info_env.deliver_signals(self.turn, agent_access)

        # 4. Agents receive signals and update beliefs
        for agent_id, signals in deliveries.items():
            if agent_id in self.agents:
                self.agents[agent_id].receive_signals(signals)

        # 5. All agents decide independently
        all_actions: list[tuple[str, Action]] = []
        for agent_id, agent in self.agents.items():
            if not agent.active:
                continue
            actions = agent.decide(world_state, self.turn)
            for action in actions:
                all_actions.append((agent_id, action))
                agent.action_history.append((self.turn, action))

        # 6. Resolve actions
        resolve_actions(
            all_actions, self.ground_truth, self.oil_market,
            self.info_env, world_state, self.turn,
        )

        # 7. Natural drift
        drift_ground_truth(self.ground_truth, self.turn)

        # 8. Update oil market
        # Market ceasefire probability is a blend of:
        # - inverse of escalation (lower escalation = higher ceasefire chance)
        # - regime survival (if regime collapsing, war ends differently)
        # - back-channel activity
        esc_norm = max(0, 1.0 - self.escalation.level / 10.0)
        self.oil_market.ceasefire_probability = (
            esc_norm * 0.4
            + (1.0 - self.ground_truth.regime_survival_index) * 0.3
            + 0.3 * world_state.get("ceasefire_offer_visible", False)
        )
        self.oil_market.update(world_state)
        self.insurance.update(self.oil_market.strait)

        # 9. Update escalation (emergent)
        self.escalation.update(
            all_actions, self.agents, self.ground_truth.as_dict()
        )

        # 10. Random events
        random_events = resolve_random_events(
            self.turn, self.ground_truth, self.info_env
        )

        # Apply variant-specific triggers
        if self.variant == "mojtaba_surfaces" and self.turn == 3:
            self.ground_truth.mojtaba_alive = 0.95
            random_events.append(RandomEvent(
                name="variant_mojtaba", probability=1.0,
                effects={}, description="[VARIANT] Mojtaba Khamenei surfaces and calls for ceasefire",
            ))
        if self.variant == "uprising_breakthrough" and self.turn == 4:
            self.ground_truth.uprising_intensity = 0.95
            self.ground_truth.irgc_cohesion -= 0.2
            random_events.append(RandomEvent(
                name="variant_uprising", probability=1.0,
                effects={}, description="[VARIANT] Major city uprising overwhelms IRGC",
            ))

        # 11. Check termination
        outcome = self.termination.check_termination(
            self.agents, world_state, self.turn
        )

        # 12. Build report
        trump = self.agents.get("us_trump")
        trump_mode = trump.current_mode.value if isinstance(trump, StochasticAgent) else "unknown"

        iran = self.agents.get("iran_composite")
        iran_faction = (
            iran.dominant_faction.name
            if isinstance(iran, CompositeAgent) else "unknown"
        )

        report = TurnReport(
            turn=self.turn,
            day=self.day,
            actions=all_actions,
            random_events=random_events,
            oil_price=self.oil_market.price,
            escalation_level=self.escalation.level,
            escalation_phase=self.escalation.phase,
            termination_status=outcome.value,
            trump_mode=trump_mode,
            iran_dominant_faction=iran_faction,
            key_metrics={
                "iran_missiles": self.ground_truth.iran_missile_stocks,
                "israel_interceptors": self.ground_truth.israel_interceptor_stocks,
                "irgc_cohesion": self.ground_truth.irgc_cohesion,
                "uprising_intensity": self.ground_truth.uprising_intensity,
                "regime_survival": self.ground_truth.regime_survival_index,
                "strait_flow": self.oil_market.strait.overall_flow,
                "us_political_will": self.ground_truth.us_political_will,
                "ceasefire_prob": self.oil_market.ceasefire_probability,
            },
            miscalculation_events=list(self.escalation.miscalculation_events),
        )

        self.reports.append(report)
        return report

    def _emit_ambient_signals(self) -> None:
        """Emit background signals about world state each turn."""
        gt = self.ground_truth

        # Oil price is visible to everyone (economic data)
        self.info_env.emit_signal(Signal(
            variable=BeliefVar.OIL_PRICE_EXPECTATION,
            true_value=self.oil_market.price,
            signal_type=SignalType.ECONOMIC_DATA,
            precision=0.9,
            description="Oil market price",
        ), self.turn)

        # Uprising intensity — filtered through internet degradation
        self.info_env.emit_signal(Signal(
            variable=BeliefVar.UPRISING_INTENSITY,
            true_value=gt.uprising_intensity,
            signal_type=SignalType.SOCIAL_MEDIA,
            precision=0.3,
            description="Uprising activity on social media",
        ), self.turn)

        # IRGC status — noisy military intelligence
        self.info_env.emit_signal(Signal(
            variable=BeliefVar.IRGC_COHESION,
            true_value=gt.irgc_cohesion,
            signal_type=SignalType.SIGINT,
            precision=0.4,
            description="IRGC organizational status assessment",
        ), self.turn)

    def run(self, max_turns: int = 120, verbose: bool = True) -> TerminationOutcome:
        """Run the simulation to completion."""
        for _ in range(max_turns):
            report = self.step()

            if verbose:
                print(report.summary())
                print()

            if report.termination_status != "continuing":
                break

        return self.termination.outcome

    def to_dict(self) -> dict:
        """Full simulation state as JSON-serializable dict."""
        return {
            "turn": self.turn,
            "day": self.day,
            "calendar_date": self.calendar_date,
            "start_day": self.start_day,
            "start_date": self.start_date,
            "variant": self.variant,
            "ground_truth": self.ground_truth.to_dict(),
            "agents": {aid: a.to_dict() for aid, a in self.agents.items()},
            "oil_market": self.oil_market.to_dict(),
            "escalation": self.escalation.to_dict(),
            "termination": self.termination.to_dict(),
            "insurance": self.insurance.to_dict(),
        }

    def get_metrics_csv(self) -> str:
        """Export all turn metrics as CSV."""
        if not self.reports:
            return ""

        # Header from first report's metrics
        metric_keys = list(self.reports[0].key_metrics.keys())
        header = ["turn", "day", "oil_price", "escalation", "trump_mode",
                  "iran_faction", "status"] + metric_keys

        lines = [",".join(header)]
        for r in self.reports:
            row = [
                str(r.turn), str(r.day), f"{r.oil_price:.1f}",
                f"{r.escalation_level:.2f}", r.trump_mode,
                r.iran_dominant_faction, r.termination_status,
            ] + [f"{r.key_metrics.get(k, 0):.4f}" for k in metric_keys]
            lines.append(",".join(row))

        return "\n".join(lines)

"""
Scenario setup — instantiate all agents with Day 18 initial conditions.

This module creates the full agent ecosystem described in the scenario
document, with calibrated priors, signal access, and victory conditions.
"""

from __future__ import annotations

from .beliefs import BeliefState, BeliefVar, BetaBelief, GaussianBelief
from .signals import SignalAccess, SignalType
from .agents import (
    Agent, MilitaryAgent, PoliticalAgent, StochasticAgent,
    CompositeAgent, ProxyAgent, Faction, TrumpMode,
)


def create_agents() -> dict[str, Agent]:
    """Create all agents with Day 18 calibration."""
    agents = {}

    # ---------------------------------------------------------------
    # IRAN COMPOSITE — splintered power structure
    # ---------------------------------------------------------------
    iran = _create_iran_composite()
    agents["iran_composite"] = iran

    # IRGC military wing (separate for Wittman convergence tracking)
    agents["irgc_military"] = _create_irgc_military()

    # ---------------------------------------------------------------
    # TRUMP — stochastic
    # ---------------------------------------------------------------
    agents["us_trump"] = _create_trump()

    # PENTAGON — military rational
    agents["pentagon"] = _create_pentagon()

    # ---------------------------------------------------------------
    # ISRAEL
    # ---------------------------------------------------------------
    agents["israel"] = _create_israel()
    agents["idf"] = _create_idf()

    # ---------------------------------------------------------------
    # REGIONAL POLITICAL ACTORS
    # ---------------------------------------------------------------
    agents["china"] = _create_china()
    agents["india"] = _create_india()
    agents["russia"] = _create_russia()
    agents["turkey"] = _create_turkey()
    agents["saudi"] = _create_saudi()
    agents["uae"] = _create_uae()
    agents["bahrain_kuwait"] = _create_bahrain_kuwait()

    # ---------------------------------------------------------------
    # PROXIES
    # ---------------------------------------------------------------
    agents["houthis"] = _create_houthis()
    agents["kh_pmf"] = _create_kh()
    agents["hezbollah"] = _create_hezbollah()
    agents["pkk_pjak"] = _create_pkk()

    # ---------------------------------------------------------------
    # NON-STATE
    # ---------------------------------------------------------------
    agents["uprising"] = _create_uprising()

    return agents


# ---------------------------------------------------------------------------
# Iran composite with factions
# ---------------------------------------------------------------------------

def _create_iran_composite() -> CompositeAgent:
    """Iran as splintered power structure."""

    # Faction 1: IRGC Hardliners (currently dominant)
    hardliner_beliefs = BeliefState()
    hardliner_beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(6, 4)  # 0.6
    hardliner_beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(3, 7)     # 0.3 (they think US will tire)
    hardliner_beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(5, 5)   # 0.5
    hardliner_beliefs.beliefs[BeliefVar.ISRAEL_INTERCEPTOR_STOCKS] = BetaBelief(3, 7)  # 0.3 (they know Israel is low)
    hardliner_beliefs.hard_priors[BeliefVar.REGIME_SURVIVAL_PROB] = (0.3, 1.0)    # can't accept regime death

    hardliners = Faction(
        faction_id="irgc_hardliners",
        name="IRGC Hardliners",
        beliefs=hardliner_beliefs,
        influence=0.45,
        hardline_score=0.9,
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (1.0, 1.0),
            BeliefVar.IRGC_COHESION: (0.8, 1.0),
            BeliefVar.US_POLITICAL_WILL: (0.6, 0.0),  # want US to lose will
        },
    )

    # Faction 2: IRGC Pragmatists
    pragmatist_beliefs = BeliefState()
    pragmatist_beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)   # 0.4
    pragmatist_beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(5, 5)      # 0.5
    pragmatist_beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(4, 6)    # 0.4 (more realistic)
    pragmatist_beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(3, 7)  # 0.3

    pragmatists = Faction(
        faction_id="irgc_pragmatists",
        name="IRGC Pragmatists",
        beliefs=pragmatist_beliefs,
        influence=0.25,
        hardline_score=0.5,
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (1.0, 1.0),
            BeliefVar.IRGC_COHESION: (0.9, 0.8),  # willing to restructure slightly
            BeliefVar.CEASEFIRE_PROBABILITY: (0.5, 0.7),
        },
    )

    # Faction 3: FM / Civilian Government
    fm_beliefs = BeliefState()
    fm_beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(3, 7)       # 0.3 (pessimistic)
    fm_beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(5, 5)          # 0.5
    fm_beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(4, 6)      # 0.4 (more hopeful)
    fm_beliefs.beliefs[BeliefVar.CHINA_WILLING_TO_GUARANTEE] = BetaBelief(5, 5) # 0.5

    fm_civilian = Faction(
        faction_id="fm_civilian",
        name="FM / Civilian Gov",
        beliefs=fm_beliefs,
        influence=0.15,
        hardline_score=0.2,
        victory_weights={
            BeliefVar.CEASEFIRE_PROBABILITY: (1.0, 1.0),
            BeliefVar.REGIME_SURVIVAL_PROB: (0.8, 0.7),  # survival > purity
        },
    )

    # Faction 4: Succession claimants (Mojtaba's camp, if alive)
    succession_beliefs = BeliefState()
    succession_beliefs.beliefs[BeliefVar.MOJTABA_ALIVE] = BetaBelief(6, 4)     # 0.6 (they think he's alive)
    succession_beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(5, 5)  # 0.5
    succession_beliefs.beliefs[BeliefVar.IRGC_COHESION] = BetaBelief(4, 6)     # 0.4 (sees fractures)

    succession = Faction(
        faction_id="succession",
        name="Succession Claimants",
        beliefs=succession_beliefs,
        influence=0.15,
        hardline_score=0.6,  # moderate-hawk (need to prove legitimacy)
        victory_weights={
            BeliefVar.MOJTABA_ALIVE: (1.0, 1.0),
            BeliefVar.REGIME_SURVIVAL_PROB: (0.9, 1.0),
            BeliefVar.IRGC_COHESION: (0.7, 1.0),
        },
    )

    composite = CompositeAgent(
        agent_id="iran_composite",
        name="Iran (Composite)",
        beliefs=BeliefState(),
        signal_access=SignalAccess(
            source_trust={
                "us_trump": 0.2,
                "israel": 0.1,
                "china": 0.7,
                "russia": 0.6,
                "turkey": 0.5,
            },
            channel_quality={
                SignalType.SIGINT: 0.4,         # degraded
                SignalType.SATELLITE_IMAGERY: 0.3,  # limited access
                SignalType.MILITARY_ACTION: 0.7,  # see strikes on own territory
                SignalType.PUBLIC_STATEMENT: 0.8,
                SignalType.SOCIAL_MEDIA: 0.5,    # internet degraded
            },
            interpretation_bias={
                BeliefVar.US_POLITICAL_WILL: -0.1,  # assume US will tire
                BeliefVar.REGIME_SURVIVAL_PROB: 0.1,  # optimism bias
            },
        ),
        factions=[hardliners, pragmatists, fm_civilian, succession],
        resolution_mode="veto",  # hardliners can veto ceasefire
        veto_threshold=0.25,
    )

    return composite


def _create_irgc_military() -> MilitaryAgent:
    """IRGC as military-rational actor for Wittman convergence."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.ISRAEL_INTERCEPTOR_STOCKS] = BetaBelief(3, 7)
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.IRAN_DRONE_STOCKS] = BetaBelief(6, 4)
    beliefs.beliefs[BeliefVar.IRAN_CYBER_CAPABILITY] = BetaBelief(7, 3)
    beliefs.beliefs[BeliefVar.FORDOW_DESTROYED] = BetaBelief(3, 7)
    beliefs.hard_priors[BeliefVar.REGIME_SURVIVAL_PROB] = (0.25, 1.0)

    return MilitaryAgent(
        agent_id="irgc_military",
        name="IRGC Military Command",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.15, "israel": 0.1, "china": 0.6},
            channel_quality={
                SignalType.MILITARY_ACTION: 0.8,
                SignalType.SIGINT: 0.5,
                SignalType.SATELLITE_IMAGERY: 0.3,
            },
        ),
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (1.0, 1.0),
            BeliefVar.IRGC_COHESION: (0.8, 1.0),
            BeliefVar.ISRAEL_INTERCEPTOR_STOCKS: (0.6, 0.0),
            BeliefVar.US_POLITICAL_WILL: (0.5, 0.0),
        },
        min_acceptable_p_victory=0.15,  # will fight to the bitter end
        cost_per_turn=0.015,
    )


# ---------------------------------------------------------------------------
# Trump
# ---------------------------------------------------------------------------

def _create_trump() -> StochasticAgent:
    """Trump — stochastic mood-driven actor."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(3, 7)   # thinks Iran is losing
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(7, 3)      # thinks he's strong
    beliefs.beliefs[BeliefVar.OIL_PRICE_EXPECTATION] = GaussianBelief(98.0, 0.1)
    beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(3, 7)  # "terms not good enough"
    beliefs.beliefs[BeliefVar.MOJTABA_ALIVE] = BetaBelief(3, 7)          # claims he's dead

    return StochasticAgent(
        agent_id="us_trump",
        name="Trump",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={
                "iran_composite": 0.1,
                "israel": 0.7,
                "china": 0.3,
                "pentagon": 0.5,  # listens sometimes
            },
            channel_quality={
                SignalType.PUBLIC_STATEMENT: 1.0,  # loves media
                SignalType.MEDIA_REPORT: 1.0,
                SignalType.SOCIAL_MEDIA: 0.9,
                SignalType.SIGINT: 0.4,            # reads briefings sometimes
                SignalType.SATELLITE_IMAGERY: 0.5,
                SignalType.MILITARY_ACTION: 0.6,
            },
            interpretation_bias={
                BeliefVar.US_POLITICAL_WILL: 0.2,     # overestimates own strength
                BeliefVar.REGIME_SURVIVAL_PROB: -0.1,  # underestimates Iran
            },
        ),
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (0.5, 0.0),
            BeliefVar.OIL_PRICE_EXPECTATION: (0.3, 63.0),
            BeliefVar.CEASEFIRE_PROBABILITY: (0.2, 0.0),  # wants to win, not ceasefire
        },
        current_mode=TrumpMode.RALLY,  # Day 18: in rally mode
    )


def _create_pentagon() -> MilitaryAgent:
    """Pentagon — rational military actor."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.US_PGM_STOCKS] = BetaBelief(5, 5)     # drawing down
    beliefs.beliefs[BeliefVar.ISRAEL_INTERCEPTOR_STOCKS] = BetaBelief(2, 8)  # knows it's bad
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.RUSSIA_SUPPLYING_IRAN] = BetaBelief(5, 5)

    return MilitaryAgent(
        agent_id="pentagon",
        name="Pentagon",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={
                "israel": 0.8,
                "iran_composite": 0.2,
                "china": 0.4,
            },
            channel_quality={
                SignalType.SIGINT: 0.9,
                SignalType.SATELLITE_IMAGERY: 0.95,
                SignalType.MILITARY_ACTION: 0.9,
                SignalType.FORCE_DEPLOYMENT: 0.9,
            },
        ),
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (0.4, 0.0),
            BeliefVar.US_PGM_STOCKS: (0.3, 1.0),
            BeliefVar.IRAN_MISSILE_STOCKS: (0.3, 0.0),
        },
        min_acceptable_p_victory=0.3,
        cost_per_turn=0.01,
    )


# ---------------------------------------------------------------------------
# Israel
# ---------------------------------------------------------------------------

def _create_israel() -> PoliticalAgent:
    """Israel political leadership."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(3, 7)
    beliefs.beliefs[BeliefVar.ISRAEL_INTERCEPTOR_STOCKS] = BetaBelief(2, 8)
    beliefs.beliefs[BeliefVar.IRAN_NUCLEAR_PROGRESS] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(6, 4)
    beliefs.beliefs[BeliefVar.FORDOW_DESTROYED] = BetaBelief(4, 6)

    return PoliticalAgent(
        agent_id="israel",
        name="Israel",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.6, "pentagon": 0.8, "iran_composite": 0.1},
            channel_quality={
                SignalType.SIGINT: 0.85,
                SignalType.SATELLITE_IMAGERY: 0.9,
                SignalType.MILITARY_ACTION: 0.9,
            },
        ),
        victory_weights={
            BeliefVar.IRAN_NUCLEAR_PROGRESS: (1.0, 0.0),
            BeliefVar.REGIME_SURVIVAL_PROB: (0.8, 0.0),
            BeliefVar.ISRAEL_INTERCEPTOR_STOCKS: (0.9, 1.0),
        },
        pain_threshold=0.8,      # high — existential framing
        pain_rate=0.01,           # slow — absorbing cost well so far
        audience_cost=0.7,        # high — can't look weak
    )


def _create_idf() -> MilitaryAgent:
    """IDF — military rational."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.ISRAEL_INTERCEPTOR_STOCKS] = BetaBelief(2, 8)
    beliefs.beliefs[BeliefVar.FORDOW_DESTROYED] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(3, 7)

    return MilitaryAgent(
        agent_id="idf",
        name="IDF",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"pentagon": 0.9, "iran_composite": 0.1},
            channel_quality={
                SignalType.SIGINT: 0.9,
                SignalType.SATELLITE_IMAGERY: 0.9,
                SignalType.MILITARY_ACTION: 0.95,
            },
        ),
        victory_weights={
            BeliefVar.IRAN_NUCLEAR_PROGRESS: (1.0, 0.0),
            BeliefVar.IRAN_MISSILE_STOCKS: (0.8, 0.0),
            BeliefVar.ISRAEL_INTERCEPTOR_STOCKS: (0.9, 1.0),
        },
        min_acceptable_p_victory=0.25,
        cost_per_turn=0.02,  # interceptor drain = high cost
    )


# ---------------------------------------------------------------------------
# Regional actors
# ---------------------------------------------------------------------------

def _create_china() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.OIL_PRICE_EXPECTATION] = GaussianBelief(98.0, 0.1)
    beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.CHINA_WILLING_TO_GUARANTEE] = BetaBelief(6, 4)

    return PoliticalAgent(
        agent_id="china",
        name="China",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={
                "us_trump": 0.3, "iran_composite": 0.6,
                "russia": 0.5, "saudi": 0.5,
            },
            channel_quality={
                SignalType.ECONOMIC_DATA: 0.95,
                SignalType.DIPLOMATIC_ACTION: 0.8,
                SignalType.SIGINT: 0.7,
                SignalType.SATELLITE_IMAGERY: 0.8,
            },
        ),
        victory_weights={
            BeliefVar.OIL_PRICE_EXPECTATION: (0.4, 63.0),
            BeliefVar.US_POLITICAL_WILL: (0.3, 0.0),  # wants US to leave Gulf
            BeliefVar.CHINA_WILLING_TO_GUARANTEE: (0.3, 1.0),
        },
        pain_threshold=0.5,
        pain_rate=0.01,
        audience_cost=0.3,  # low — CCP doesn't face elections
    )


def _create_india() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.OIL_PRICE_EXPECTATION] = GaussianBelief(98.0, 0.1)

    return PoliticalAgent(
        agent_id="india",
        name="India",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.4, "china": 0.4, "iran_composite": 0.5},
            channel_quality={
                SignalType.ECONOMIC_DATA: 0.8,
                SignalType.DIPLOMATIC_ACTION: 0.7,
            },
        ),
        victory_weights={
            BeliefVar.OIL_PRICE_EXPECTATION: (0.7, 50.0),  # wants cheap oil
        },
        pain_threshold=0.9,  # very high — profiting from crisis
        pain_rate=0.005,
        audience_cost=0.4,
    )


def _create_russia() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.OIL_PRICE_EXPECTATION] = GaussianBelief(98.0, 0.1)
    beliefs.beliefs[BeliefVar.RUSSIA_SUPPLYING_IRAN] = BetaBelief(7, 3)  # knows the truth
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(4, 6)

    return PoliticalAgent(
        agent_id="russia",
        name="Russia",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"iran_composite": 0.7, "china": 0.6, "us_trump": 0.2},
            channel_quality={
                SignalType.SIGINT: 0.8,
                SignalType.MILITARY_ACTION: 0.7,
                SignalType.SATELLITE_IMAGERY: 0.7,
            },
        ),
        victory_weights={
            BeliefVar.OIL_PRICE_EXPECTATION: (0.4, 110.0),  # wants high oil
            BeliefVar.US_POLITICAL_WILL: (0.4, 0.0),         # wants US exhausted
        },
        pain_threshold=0.95,  # nearly immune — profiting
        pain_rate=0.002,
        audience_cost=0.2,
    )


def _create_turkey() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(4, 6)

    return PoliticalAgent(
        agent_id="turkey",
        name="Turkey",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={
                "us_trump": 0.5, "iran_composite": 0.5,
                "russia": 0.4, "israel": 0.3,
            },
            channel_quality={
                SignalType.DIPLOMATIC_ACTION: 0.9,
                SignalType.MILITARY_ACTION: 0.7,
                SignalType.SIGINT: 0.6,
            },
        ),
        victory_weights={
            BeliefVar.CEASEFIRE_PROBABILITY: (0.8, 1.0),  # wants to broker deal
        },
        pain_threshold=0.4,  # low — 3 missiles hit, sensitive
        pain_rate=0.02,
        audience_cost=0.6,
    )


def _create_saudi() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.OIL_PRICE_EXPECTATION] = GaussianBelief(98.0, 0.1)

    return PoliticalAgent(
        agent_id="saudi",
        name="Saudi Arabia",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.5, "china": 0.5, "iran_composite": 0.3},
            channel_quality={
                SignalType.ECONOMIC_DATA: 0.9,
                SignalType.DIPLOMATIC_ACTION: 0.8,
            },
        ),
        victory_weights={
            BeliefVar.US_POLITICAL_WILL: (0.5, 1.0),
            BeliefVar.OIL_PRICE_EXPECTATION: (0.3, 70.0),
            BeliefVar.REGIME_SURVIVAL_PROB: (0.2, 0.0),
        },
        pain_threshold=0.5,
        pain_rate=0.025,
        audience_cost=0.5,
    )


def _create_uae() -> PoliticalAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(4, 6)
    beliefs.beliefs[BeliefVar.US_POLITICAL_WILL] = BetaBelief(4, 6)

    return PoliticalAgent(
        agent_id="uae",
        name="UAE",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.5, "china": 0.5, "saudi": 0.7},
            channel_quality={
                SignalType.MILITARY_ACTION: 0.9,
                SignalType.ECONOMIC_DATA: 0.9,
            },
        ),
        victory_weights={
            BeliefVar.CEASEFIRE_PROBABILITY: (1.0, 1.0),
        },
        pain_threshold=0.3,  # very low — already struck, desperate
        current_pain=0.25,   # starts high
        pain_rate=0.04,      # fastest pain accumulation
        audience_cost=0.3,
    )


def _create_bahrain_kuwait() -> PoliticalAgent:
    beliefs = BeliefState()
    return PoliticalAgent(
        agent_id="bahrain_kuwait",
        name="Bahrain/Kuwait",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"us_trump": 0.5, "saudi": 0.7},
        ),
        victory_weights={
            BeliefVar.CEASEFIRE_PROBABILITY: (1.0, 1.0),
        },
        pain_threshold=0.25,
        current_pain=0.2,
        pain_rate=0.04,
        audience_cost=0.2,
    )


# ---------------------------------------------------------------------------
# Proxies
# ---------------------------------------------------------------------------

def _create_houthis() -> ProxyAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.HOUTHI_ACTIVATION_PROB] = BetaBelief(3, 7)  # restraint mode
    beliefs.beliefs[BeliefVar.CEASEFIRE_PROBABILITY] = BetaBelief(3, 7)

    return ProxyAgent(
        agent_id="houthis",
        name="Houthis (Ansar Allah)",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"iran_composite": 0.6, "us_trump": 0.1},
            channel_quality={
                SignalType.MILITARY_ACTION: 0.6,
                SignalType.PUBLIC_STATEMENT: 0.7,
            },
        ),
        patron_id="iran_composite",
        communication_reliability=0.5,
        autonomy=0.8,  # very high autonomy
        local_interest_weight=0.8,  # Yemen peace deal > Iranian proxy war
    )


def _create_kh() -> ProxyAgent:
    beliefs = BeliefState()
    return ProxyAgent(
        agent_id="kh_pmf",
        name="Kata'ib Hezbollah / PMF",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"iran_composite": 0.8, "us_trump": 0.1},
        ),
        patron_id="iran_composite",
        communication_reliability=0.65,
        autonomy=0.4,  # medium — high compliance
        local_interest_weight=0.4,
    )


def _create_hezbollah() -> ProxyAgent:
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.IRAN_MISSILE_STOCKS] = BetaBelief(4, 6)

    return ProxyAgent(
        agent_id="hezbollah",
        name="Hezbollah",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"iran_composite": 0.7, "israel": 0.2},
        ),
        patron_id="iran_composite",
        communication_reliability=0.5,  # supply lines disrupted
        autonomy=0.6,
        local_interest_weight=0.6,  # Lebanese politics matter
    )


def _create_pkk() -> ProxyAgent:
    beliefs = BeliefState()
    return ProxyAgent(
        agent_id="pkk_pjak",
        name="PKK/PJAK",
        beliefs=beliefs,
        signal_access=SignalAccess(default_trust=0.3),
        patron_id=None,  # no patron
        autonomy=1.0,    # fully autonomous
        local_interest_weight=1.0,
    )


# ---------------------------------------------------------------------------
# Non-state
# ---------------------------------------------------------------------------

def _create_uprising() -> PoliticalAgent:
    """Iranian domestic uprising as a political agent."""
    beliefs = BeliefState()
    beliefs.beliefs[BeliefVar.REGIME_SURVIVAL_PROB] = BetaBelief(3, 7)
    beliefs.beliefs[BeliefVar.IRGC_COHESION] = BetaBelief(5, 5)
    beliefs.beliefs[BeliefVar.UPRISING_INTENSITY] = BetaBelief(7, 3)

    return PoliticalAgent(
        agent_id="uprising",
        name="Iranian Uprising",
        beliefs=beliefs,
        signal_access=SignalAccess(
            source_trust={"iran_composite": 0.2, "us_trump": 0.3},
            channel_quality={
                SignalType.SOCIAL_MEDIA: 0.4,   # internet degraded
                SignalType.MILITARY_ACTION: 0.5,
            },
            interpretation_bias={
                BeliefVar.REGIME_SURVIVAL_PROB: -0.15,  # hopeful it's collapsing
            },
        ),
        victory_weights={
            BeliefVar.REGIME_SURVIVAL_PROB: (1.0, 0.0),  # want regime to fall
            BeliefVar.IRGC_COHESION: (0.8, 0.0),
            BeliefVar.UPRISING_INTENSITY: (0.5, 1.0),
        },
        pain_threshold=0.95,  # extremely high — 60k dead and still going
        pain_rate=0.005,
        audience_cost=0.0,    # nothing to lose
    )

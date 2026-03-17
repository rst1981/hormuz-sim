"""Parameter defaults and metadata endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/params", tags=["parameters"])

GROUND_TRUTH_PARAMS = [
    {"name": "mojtaba_alive", "type": "float", "default": 0.5, "min": 0, "max": 1,
     "description": "P(Mojtaba Khamenei is alive) — genuinely unknown"},
    {"name": "irgc_cohesion", "type": "float", "default": 0.55, "min": 0, "max": 1,
     "description": "IRGC organizational integrity (0=collapsed, 1=intact)"},
    {"name": "iran_missile_stocks", "type": "float", "default": 0.45, "min": 0, "max": 1,
     "description": "Iranian missile inventory fraction remaining"},
    {"name": "iran_drone_stocks", "type": "float", "default": 0.55, "min": 0, "max": 1,
     "description": "Iranian drone inventory fraction remaining"},
    {"name": "israel_interceptor_stocks", "type": "float", "default": 0.25, "min": 0, "max": 1,
     "description": "Israeli interceptor stocks — critically low but not empty"},
    {"name": "us_pgm_stocks", "type": "float", "default": 0.6, "min": 0, "max": 1,
     "description": "US precision-guided munitions fraction remaining"},
    {"name": "iran_nuclear_progress", "type": "float", "default": 0.4, "min": 0, "max": 1,
     "description": "Progress toward nuclear breakout (0-1)"},
    {"name": "iran_cyber_capability", "type": "float", "default": 0.7, "min": 0, "max": 1,
     "description": "Iranian cyber capability readiness (intact, held back)"},
    {"name": "fordow_destroyed", "type": "float", "default": 0.3, "min": 0, "max": 1,
     "description": "P(Fordow nuclear facility destroyed)"},
    {"name": "kharg_terminal_damaged", "type": "float", "default": 0.6, "min": 0, "max": 1,
     "description": "P(Kharg Island oil terminal destroyed)"},
    {"name": "russia_supplying_iran", "type": "float", "default": 0.65, "min": 0, "max": 1,
     "description": "P(Russia actively resupplying Iran)"},
    {"name": "china_willing_to_guarantee", "type": "float", "default": 0.4, "min": 0, "max": 1,
     "description": "P(China offers security guarantee to Iran)"},
    {"name": "us_political_will", "type": "float", "default": 0.55, "min": 0, "max": 1,
     "description": "US commitment to continue campaign (0-1)"},
    {"name": "israel_will_to_continue", "type": "float", "default": 0.75, "min": 0, "max": 1,
     "description": "Israeli willingness to continue fighting"},
    {"name": "houthi_activation_prob", "type": "float", "default": 0.25, "min": 0, "max": 1,
     "description": "P(Houthis begin Red Sea attacks)"},
    {"name": "hezbollah_full_war_prob", "type": "float", "default": 0.15, "min": 0, "max": 1,
     "description": "P(Hezbollah full war activation)"},
    {"name": "uprising_intensity", "type": "float", "default": 0.7, "min": 0, "max": 1,
     "description": "Current domestic uprising pressure on regime"},
    {"name": "uprising_irgc_drain", "type": "float", "default": 0.15, "min": 0, "max": 0.4,
     "description": "Fraction of IRGC forces tied down by uprising"},
    {"name": "irgc_casualties_cumulative", "type": "int", "default": 21000, "min": 0, "max": 100000,
     "description": "Cumulative IRGC casualties since Day 1"},
    {"name": "uprising_casualties_cumulative", "type": "int", "default": 60514, "min": 0, "max": 500000,
     "description": "Cumulative uprising civilian casualties"},
    {"name": "regime_survival_index", "type": "float", "default": 0.45, "min": 0, "max": 1,
     "description": "Composite regime survival index"},
]

OIL_MARKET_PARAMS = [
    {"name": "price", "type": "float", "default": 98.0, "min": 40, "max": 300,
     "description": "Current oil price $/barrel"},
    {"name": "base_price", "type": "float", "default": 63.0, "min": 40, "max": 150,
     "description": "Pre-war baseline oil price"},
    {"name": "war_risk_premium", "type": "float", "default": 35.0, "min": 0, "max": 100,
     "description": "War risk premium $/barrel"},
    {"name": "kharg_damaged", "type": "float", "default": 0.5, "min": 0, "max": 1,
     "description": "Kharg Island damage level (0=intact, 1=destroyed)"},
    {"name": "spr_releases", "type": "float", "default": 0.02, "min": 0, "max": 0.15,
     "description": "Strategic reserve release rate (fraction of disruption offset)"},
    {"name": "russian_backfill", "type": "float", "default": 0.03, "min": 0, "max": 0.1,
     "description": "Russian supply backfill fraction"},
    {"name": "ceasefire_probability", "type": "float", "default": 0.3, "min": 0, "max": 1,
     "description": "Market-implied ceasefire probability"},
]

ESCALATION_PARAMS = [
    {"name": "level", "type": "float", "default": 7.5, "min": 0, "max": 10,
     "description": "Starting escalation level (Day 18)"},
    {"name": "iran_grievance", "type": "float", "default": 0.8, "min": 0, "max": 2,
     "description": "Iran Richardson grievance parameter"},
    {"name": "iran_reactivity", "type": "float", "default": 0.6, "min": 0, "max": 2,
     "description": "Iran Richardson reactivity"},
    {"name": "iran_fatigue", "type": "float", "default": 0.1, "min": 0, "max": 1,
     "description": "Iran Richardson fatigue"},
    {"name": "us_israel_grievance", "type": "float", "default": 0.5, "min": 0, "max": 2,
     "description": "US/Israel Richardson grievance"},
    {"name": "us_israel_reactivity", "type": "float", "default": 0.5, "min": 0, "max": 2,
     "description": "US/Israel Richardson reactivity"},
    {"name": "us_israel_fatigue", "type": "float", "default": 0.05, "min": 0, "max": 1,
     "description": "US/Israel Richardson fatigue"},
]

TRUMP_TRANSITION_MATRIX = {
    "rally": {"rally": 0.4, "deal": 0.25, "escalation": 0.15, "distraction": 0.2},
    "deal": {"rally": 0.15, "deal": 0.45, "escalation": 0.15, "distraction": 0.25},
    "escalation": {"rally": 0.3, "deal": 0.1, "escalation": 0.35, "distraction": 0.25},
    "distraction": {"rally": 0.25, "deal": 0.25, "escalation": 0.1, "distraction": 0.4},
}


@router.get("/ground-truth/defaults")
def get_ground_truth_defaults():
    return GROUND_TRUTH_PARAMS


@router.get("/oil-market/defaults")
def get_oil_market_defaults():
    return OIL_MARKET_PARAMS


@router.get("/escalation/defaults")
def get_escalation_defaults():
    return ESCALATION_PARAMS


@router.get("/agents/defaults")
def get_agent_defaults():
    return {
        "agent_count": 18,
        "types": ["MilitaryAgent", "PoliticalAgent", "StochasticAgent", "CompositeAgent", "ProxyAgent"],
        "agents": [
            {"id": "irgc_military", "name": "IRGC Military Command", "type": "MilitaryAgent"},
            {"id": "idf", "name": "IDF", "type": "MilitaryAgent"},
            {"id": "pentagon", "name": "Pentagon", "type": "MilitaryAgent"},
            {"id": "us_trump", "name": "Trump", "type": "StochasticAgent"},
            {"id": "iran_composite", "name": "Iran (Composite)", "type": "CompositeAgent"},
            {"id": "iran_fm", "name": "Iran FM/Civilian", "type": "PoliticalAgent"},
            {"id": "saudi", "name": "Saudi Arabia (MBS)", "type": "PoliticalAgent"},
            {"id": "uae", "name": "UAE (MBZ)", "type": "PoliticalAgent"},
            {"id": "turkey", "name": "Turkey (Erdogan)", "type": "PoliticalAgent"},
            {"id": "china", "name": "China", "type": "PoliticalAgent"},
            {"id": "russia", "name": "Russia", "type": "PoliticalAgent"},
            {"id": "israel", "name": "Israel (Political)", "type": "PoliticalAgent"},
            {"id": "houthis", "name": "Houthis", "type": "ProxyAgent"},
            {"id": "hezbollah", "name": "Hezbollah", "type": "ProxyAgent"},
            {"id": "kh_pmf", "name": "Kata'ib Hezbollah/PMF", "type": "ProxyAgent"},
            {"id": "iraqi_gov", "name": "Iraqi Government", "type": "PoliticalAgent"},
            {"id": "eu", "name": "European Union", "type": "PoliticalAgent"},
            {"id": "india", "name": "India", "type": "PoliticalAgent"},
        ],
    }


@router.get("/trump/transition-matrix")
def get_trump_transition_matrix():
    return TRUMP_TRANSITION_MATRIX

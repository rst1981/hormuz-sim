"""Claude API analyzer — map scraped events to simulation parameter changes."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from api.config import settings

logger = logging.getLogger(__name__)


def _build_parameter_table(baseline: dict[str, dict[str, float]]) -> str:
    """Build a markdown table of all parameters with current baseline values."""
    from api.routers.parameters import (
        ESCALATION_PARAMS,
        GROUND_TRUTH_PARAMS,
        OIL_MARKET_PARAMS,
    )

    lines = ["| Category | Parameter | Current Value | Min | Max | Description |"]
    lines.append("|----------|-----------|--------------|-----|-----|-------------|")

    for p in GROUND_TRUTH_PARAMS:
        val = baseline.get("ground_truth", {}).get(p["name"], p["default"])
        lines.append(
            f"| ground_truth | {p['name']} | {val} | {p['min']} | {p['max']} | {p['description']} |"
        )
    for p in OIL_MARKET_PARAMS:
        val = baseline.get("oil_market", {}).get(p["name"], p["default"])
        lines.append(
            f"| oil_market | {p['name']} | {val} | {p['min']} | {p['max']} | {p['description']} |"
        )
    for p in ESCALATION_PARAMS:
        val = baseline.get("escalation", {}).get(p["name"], p["default"])
        lines.append(
            f"| escalation | {p['name']} | {val} | {p['min']} | {p['max']} | {p['description']} |"
        )

    return "\n".join(lines)


SYSTEM_PROMPT = """\
You are an aggressive intelligence analyst for a Strait of Hormuz crisis simulation (Operation Epic Fury).
The simulation models the Iran-Israel conflict starting from Day 18 of hostilities (Feb 25, 2026 = Day 1).

Your job: map EVERY news event to simulation parameter changes. Most events affect SOMETHING.
Be liberal in finding connections — the user will review your suggestions before applying them.

For each adjustment, provide:
1. "parameter": exact parameter name from the table below
2. "category": "ground_truth", "oil_market", or "escalation"
3. Either "delta" (incremental change) or "absolute" (set to exact value), not both
4. "reasoning": 1-2 sentence explanation connecting the event to the parameter

MAPPING GUIDE — use these connections aggressively:

**Military events** (strikes, attacks, interceptions, operations):
- Missile/drone strikes on Iran → iran_missile_stocks or iran_drone_stocks (delta -0.02 to -0.08)
- Israeli interceptions of missiles → israel_interceptor_stocks (delta -0.02 to -0.05)
- US munitions usage/resupply → us_pgm_stocks (delta -0.03 to -0.05, or + for resupply)
- Any military escalation → escalation.base_level (delta +0.1 to +0.5)
- IRGC casualties/leadership kills → irgc_cohesion (delta -0.03 to -0.08), irgc_casualties_cumulative (delta +0.01 to +0.05)
- Attacks on Fordow/nuclear sites → fordow_destroyed (delta +0.1 to +0.3)

**Maritime/Strait events** (shipping, Hormuz, Red Sea, Houthis):
- Houthi attacks on shipping → houthi_activation_prob (delta +0.05 to +0.15)
- Strait of Hormuz threats/mining → escalation.base_level (delta +0.2 to +0.5)
- Shipping disruptions → oil_market.war_risk_premium (delta +1 to +5)

**Oil & Economy** (prices, sanctions, infrastructure):
- Oil price mentions → oil_market.price (absolute value in $/barrel)
- Oil infrastructure damage (Kharg, pipelines) → kharg_terminal_damaged (delta +0.1 to +0.3)
- New sanctions → oil_market.war_risk_premium (delta +1 to +3)
- Infrastructure attacks (airports, ports) → oil_market.war_risk_premium (delta +0.5 to +2)

**Diplomacy & Politics**:
- Peace talks, ceasefire signals → escalation.ceasefire_weight (delta +0.05 to +0.15)
- US political support for Israel → us_political_will (delta +0.02 to +0.05)
- US political opposition/fatigue → us_political_will (delta -0.02 to -0.05)
- Chinese/Russian involvement → china_willing_to_guarantee or russia_supplying_iran (delta +0.03 to +0.10)
- Hezbollah involvement → hezbollah_full_war_prob (delta +0.03 to +0.10)

**Nuclear**:
- Enrichment progress → iran_nuclear_progress (delta +0.03 to +0.10)
- IAEA inspections/restrictions → iran_nuclear_progress (delta -0.02 to +0.02)

**Regional instability**:
- Attacks on Arab neighbors → escalation.base_level (delta +0.1 to +0.3)
- Protests in Iran → uprising_intensity (delta +0.02 to +0.08)
- Regime stability threats → regime_survival_index (delta -0.02 to -0.08)

IMPORTANT:
- Err on the side of SUGGESTING a change. The user will approve or reject.
- Most headlines should produce at least 1 parameter change
- A single event can affect MULTIPLE parameters (e.g., a strike depletes stocks AND raises escalation)
- For 0-1 range parameters, typical deltas: 0.02-0.10. For escalation.base_level (0-10 range): 0.1-0.5
- Use "absolute" for oil_market.price when a specific price is mentioned
- Return an empty array ONLY if the event is truly irrelevant (celebrity news, sports, etc.)

Respond with a JSON array of arrays. The outer array has one inner array per event (in order).
Each inner array contains the parameter changes for that event.

Example:
```json
[
  [
    {"parameter": "iran_drone_stocks", "category": "ground_truth", "delta": -0.05, "reasoning": "Israeli airstrike destroyed drone depot near Isfahan"},
    {"parameter": "israel_interceptor_stocks", "category": "ground_truth", "delta": -0.03, "reasoning": "Iron Dome intercepted 30+ drones, depleting interceptor reserves"},
    {"parameter": "base_level", "category": "escalation", "delta": 0.3, "reasoning": "Major escalation: direct strike on Iranian military infrastructure"}
  ],
  [
    {"parameter": "price", "category": "oil_market", "absolute": 98.50, "reasoning": "Brent crude surged to $98.50 on escalation fears"},
    {"parameter": "war_risk_premium", "category": "oil_market", "delta": 2.5, "reasoning": "Markets pricing in higher conflict risk after strikes"}
  ]
]
```

CURRENT PARAMETER TABLE:
{parameter_table}
"""


def _validate_changes(
    changes: list[dict], baseline: dict[str, dict[str, float]]
) -> list[dict]:
    """Validate and sanitize Claude's output against known parameters."""
    from api.routers.parameters import (
        ESCALATION_PARAMS,
        GROUND_TRUTH_PARAMS,
        OIL_MARKET_PARAMS,
    )

    # Build lookup of valid params with ranges
    valid: dict[str, dict[str, Any]] = {}
    for p in GROUND_TRUTH_PARAMS:
        valid[f"ground_truth.{p['name']}"] = p
    for p in OIL_MARKET_PARAMS:
        valid[f"oil_market.{p['name']}"] = p
    for p in ESCALATION_PARAMS:
        valid[f"escalation.{p['name']}"] = p

    validated = []
    for c in changes:
        param = c.get("parameter", "")
        cat = c.get("category", "")
        key = f"{cat}.{param}"

        if key not in valid:
            logger.warning(f"Analyzer returned unknown parameter: {key}, skipping")
            continue

        meta = valid[key]
        current = baseline.get(cat, {}).get(param, meta["default"])

        # Compute resulting value
        if c.get("absolute") is not None:
            result = c["absolute"]
        elif c.get("delta") is not None:
            result = current + c["delta"]
        else:
            logger.warning(f"No delta or absolute for {key}, skipping")
            continue

        # Clamp
        result = max(meta["min"], min(meta["max"], result))

        validated.append({
            "parameter": param,
            "category": cat,
            "delta": c.get("delta"),
            "absolute": c.get("absolute"),
            "reasoning": c.get("reasoning", ""),
        })

    return validated


async def analyze_events(
    events: list,  # list[ScrapedEvent]
    current_baseline: dict[str, dict[str, float]],
) -> list[list[dict]]:
    """Analyze scraped events using Claude API. Returns one list of changes per event."""
    param_table = _build_parameter_table(current_baseline)
    system = SYSTEM_PROMPT.replace("{parameter_table}", param_table)

    # Build user message with all events
    event_texts = []
    for i, ev in enumerate(events, 1):
        event_texts.append(
            f"## Event {i}\n"
            f"**Source:** {ev.source}\n"
            f"**Date:** {ev.event_date}\n"
            f"**Category:** {ev.category}\n"
            f"**Title:** {ev.title}\n"
            f"**Body:** {ev.body}\n"
        )

    user_msg = (
        "Analyze these real-world events and determine parameter adjustments.\n"
        "Respond with ONLY a JSON array of arrays (one per event).\n\n"
        + "\n---\n".join(event_texts)
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )

        # Extract JSON from response
        text = response.content[0].text.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # remove ```json line
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        raw_result = json.loads(text)

        if not isinstance(raw_result, list):
            logger.error(f"Expected array, got {type(raw_result)}")
            return [[] for _ in events]

        # Validate each event's changes
        results = []
        for i, event_changes in enumerate(raw_result):
            if not isinstance(event_changes, list):
                results.append([])
                continue
            validated = _validate_changes(event_changes, current_baseline)
            results.append(validated)

        # Pad if Claude returned fewer results than events
        while len(results) < len(events):
            results.append([])

        return results

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        return [[] for _ in events]
    except Exception as e:
        logger.exception(f"Claude API call failed: {e}")
        raise

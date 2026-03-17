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
You are an analyst for a Strait of Hormuz crisis simulation (Operation Epic Fury).
The simulation models the Iran conflict starting from Day 18 of hostilities (Feb 25, 2026 = Day 1).

Given real-world news events about Iran and the Middle East, determine if any simulation
parameters should be adjusted. For each adjustment, provide:

1. "parameter": exact parameter name from the table below
2. "category": "ground_truth", "oil_market", or "escalation"
3. Either "delta" (incremental change) or "absolute" (set to exact value), not both
4. "reasoning": 1-2 sentence explanation

Guidelines:
- Only suggest changes when events clearly and directly map to a simulation parameter
- For most parameters (0-1 range), keep deltas small: typically 0.01-0.10
- Multiple events reinforcing the same direction can justify larger deltas
- Use "absolute" (not delta) for oil_market.price — set it to the actual Brent crude $/barrel if mentioned in any article
- Use "absolute" for oil_market.base_price if pre-war reference price context is available
- If no events warrant parameter changes, return an empty array
- Do NOT invent events or extrapolate beyond what the news states

Respond with a JSON array of arrays. The outer array has one inner array per event (in order).
Each inner array contains the parameter changes for that event (can be empty []).

Example response:
```json
[
  [
    {"parameter": "iran_drone_stocks", "category": "ground_truth", "delta": -0.03, "reasoning": "Report confirms drone depot hit by airstrike"},
    {"parameter": "oil_market.price", "category": "oil_market", "absolute": 95.40, "reasoning": "Brent crude at $95.40/barrel per Reuters"}
  ],
  []
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

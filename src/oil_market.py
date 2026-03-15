"""
Oil market and economic model.

The oil market is a reactive system — it responds to agent decisions
with nonlinear dynamics. Price emerges from supply disruption,
strategic reserve drawdowns, re-flagging dynamics, and ceasefire
expectations.

Key insight from scenario: $98/barrel (not $300) because the selective
blockade means China/India still get oil. The market is pricing in
a ceasefire. If that expectation breaks, price spikes nonlinearly.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class StraitStatus:
    """Strait of Hormuz transit regime."""
    # Fraction of traffic permitted by flag
    chinese_flow: float = 1.0
    indian_flow: float = 1.0
    russian_flow: float = 0.9
    western_flow: float = 0.1       # mostly blocked
    gulf_state_flow: float = 0.1    # mostly blocked

    # Is strait in "trap" mode (combat zone, all traffic at risk)?
    trap_mode: bool = False

    # Reflagging queue — vessels switching to permitted flags
    reflagging_rate: float = 0.02   # fraction per turn

    @property
    def overall_flow(self) -> float:
        """Weighted average flow through strait."""
        if self.trap_mode:
            return 0.1  # near-total disruption

        # Weight by share of normal traffic
        weights = {
            "chinese": (self.chinese_flow, 0.15),
            "indian": (self.indian_flow, 0.10),
            "russian": (self.russian_flow, 0.05),
            "western": (self.western_flow, 0.40),
            "gulf": (self.gulf_state_flow, 0.30),
        }
        total_flow = sum(flow * share for flow, share in weights.values())
        return total_flow

    def apply_reflagging(self) -> None:
        """Each turn, some vessels re-flag to permitted registries."""
        # Western traffic recovers slightly as ships re-flag
        self.western_flow = min(
            1.0, self.western_flow + self.reflagging_rate
        )
        self.gulf_state_flow = min(
            1.0, self.gulf_state_flow + self.reflagging_rate * 0.5
        )


@dataclass
class RedSeaStatus:
    """Red Sea / Bab el-Mandeb status."""
    houthi_active: bool = False
    flow: float = 1.0              # 1.0 = normal, 0 = blocked

    def activate_houthis(self) -> None:
        self.houthi_active = True
        self.flow = 0.3

    @property
    def suez_revenue_fraction(self) -> float:
        """Egypt's Suez Canal revenue as fraction of normal."""
        return self.flow


@dataclass
class OilMarket:
    """
    Oil market model.

    Price is driven by:
    1. Supply disruption (strait flow, Kharg status, Red Sea)
    2. Demand-side offsets (reserves, Russian backfill, reduced demand)
    3. Ceasefire expectation (market forward-looking)
    4. Panic multiplier (nonlinear at high disruption)
    """

    # Current price
    price: float = 98.0

    # Base price (pre-war)
    base_price: float = 63.0

    # Supply components
    strait: StraitStatus = field(default_factory=StraitStatus)
    red_sea: RedSeaStatus = field(default_factory=RedSeaStatus)

    # Kharg Island oil terminal status
    kharg_damaged: float = 0.5      # 0 = intact, 1 = destroyed
    # If destroyed, Iran loses ~90% of oil exports but also loses
    # leverage (can't threaten what's already gone)

    # War risk premium — baseline premium from active conflict
    war_risk_premium: float = 15.0  # $/barrel just from war existing

    # Demand offsets
    spr_releases: float = 0.03      # fraction of disruption offset by reserves
    russian_backfill: float = 0.05  # Russia filling gap
    demand_destruction: float = 0.0  # high prices reduce demand

    # Market expectations
    ceasefire_probability: float = 0.3  # market-implied
    panic_level: float = 0.0           # 0 = calm, 1 = panic

    # History
    price_history: list[float] = field(default_factory=lambda: [98.0])

    def update(self, world_state: dict) -> float:
        """
        Compute new oil price based on current conditions.
        """
        # --- Net supply disruption ---
        strait_disruption = 1.0 - self.strait.overall_flow
        red_sea_disruption = 1.0 - self.red_sea.flow

        # Kharg damage affects Iran's exports specifically
        # Iran ~= 3-4% of global supply
        kharg_disruption = self.kharg_damaged * 0.04

        total_disruption = (
            strait_disruption * 0.20    # ~20% of global oil through Hormuz
            + red_sea_disruption * 0.10  # ~10% through Suez/Red Sea
            + kharg_disruption
        )

        # --- Offsets ---
        offsets = self.spr_releases + self.russian_backfill + self.demand_destruction
        net_disruption = max(0.0, total_disruption - offsets)

        # --- Panic multiplier (nonlinear) ---
        if net_disruption < 0.10:
            panic_mult = 1.5
        elif net_disruption < 0.20:
            panic_mult = 2.5
        elif net_disruption < 0.40:
            panic_mult = 4.0
        else:
            panic_mult = 8.0

        # Panic level smooths over time
        target_panic = min(1.0, net_disruption * 3)
        self.panic_level = self.panic_level * 0.7 + target_panic * 0.3

        # --- Ceasefire expectation dampens price ---
        # If market expects ceasefire, forward prices drop
        ceasefire_damper = 1.0 - (self.ceasefire_probability * 0.3)

        # --- Price calculation ---
        disruption_premium = (
            net_disruption * panic_mult * self.base_price * ceasefire_damper
        )

        # War risk premium exists as long as conflict is active
        target_price = self.base_price + self.war_risk_premium + disruption_premium

        # Add market noise
        noise = random.gauss(0, 2.0)
        target_price += noise

        # Price has inertia — doesn't jump instantly
        self.price = self.price * 0.6 + target_price * 0.4

        # Floor and ceiling
        self.price = max(40.0, min(300.0, self.price))

        # --- Secondary effects ---
        # High prices cause demand destruction
        if self.price > 120:
            self.demand_destruction = min(0.1, (self.price - 120) * 0.001)
        else:
            self.demand_destruction = max(0.0, self.demand_destruction - 0.005)

        # SPR draws down over time (finite resource)
        self.spr_releases = max(0.0, self.spr_releases - 0.002)

        # Reflagging gradually restores flow
        self.strait.apply_reflagging()

        self.price_history.append(self.price)
        return self.price

    @property
    def price_change_pct(self) -> float:
        return ((self.price - self.base_price) / self.base_price) * 100

    @property
    def trend(self) -> str:
        if len(self.price_history) < 3:
            return "insufficient_data"
        recent = self.price_history[-3:]
        if recent[-1] > recent[0] + 3:
            return "rising"
        elif recent[-1] < recent[0] - 3:
            return "falling"
        return "stable"


@dataclass
class InsuranceMarket:
    """Maritime insurance state."""
    # Western insurers (Lloyd's etc.)
    western_coverage: bool = False   # suspended for Gulf transit
    western_premium_mult: float = 5.0  # 500% of normal if available

    # Chinese state insurer (PICC)
    chinese_coverage: bool = True
    chinese_premium_mult: float = 3.0

    # Premium trend
    def update(self, strait: StraitStatus) -> None:
        if strait.trap_mode:
            self.western_coverage = False
            self.chinese_coverage = False  # even PICC pulls out
            self.chinese_premium_mult = 10.0
        elif strait.overall_flow < 0.5:
            self.western_coverage = False
            self.chinese_premium_mult = min(
                8.0, self.chinese_premium_mult + 0.5
            )
        else:
            # Gradual restoration
            if strait.overall_flow > 0.7:
                self.western_coverage = True
                self.western_premium_mult = max(
                    2.0, self.western_premium_mult - 0.3
                )
            self.chinese_premium_mult = max(
                1.5, self.chinese_premium_mult - 0.2
            )

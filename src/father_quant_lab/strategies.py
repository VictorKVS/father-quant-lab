"""Control strategies used as mandatory baselines in every tournament."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol, Sequence

from .models import Bar, Decision


class Strategy(Protocol):
    strategy_id: str

    def on_bar(self, index: int, history: Sequence[Bar]) -> Decision | None:
        """Return a target weight after the current bar has closed."""


@dataclass(slots=True)
class NoTradeStrategy:
    strategy_id: str = "BOT-CTRL-000"

    def on_bar(self, index: int, history: Sequence[Bar]) -> Decision | None:
        return None


@dataclass(slots=True)
class BuyHoldStrategy:
    target_weight: float = 1.0
    strategy_id: str = "BOT-CTRL-002"

    def on_bar(self, index: int, history: Sequence[Bar]) -> Decision:
        return Decision(history[-1].timestamp, self.target_weight, "buy-and-hold target")


@dataclass(slots=True)
class PeriodicRebalanceStrategy:
    target_weight: float = 0.5
    rebalance_every: int = 5
    strategy_id: str = "BOT-CTRL-003"

    def __post_init__(self) -> None:
        if self.rebalance_every <= 0:
            raise ValueError("rebalance_every must be positive")

    def on_bar(self, index: int, history: Sequence[Bar]) -> Decision | None:
        if index % self.rebalance_every != 0:
            return None
        return Decision(history[-1].timestamp, self.target_weight, "scheduled rebalance")


@dataclass(slots=True)
class RandomStrategy:
    seed: int = 20260816
    targets: tuple[float, ...] = (0.0, 1.0)
    strategy_id: str = "BOT-CTRL-001"
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.targets:
            raise ValueError("targets must not be empty")
        self._rng = random.Random(self.seed)

    def on_bar(self, index: int, history: Sequence[Bar]) -> Decision:
        target = self._rng.choice(self.targets)
        return Decision(history[-1].timestamp, target, f"seeded random target ({self.seed})")


def control_strategies(seed: int = 20260816) -> tuple[Strategy, ...]:
    return (
        NoTradeStrategy(),
        RandomStrategy(seed=seed),
        BuyHoldStrategy(),
        PeriodicRebalanceStrategy(),
    )

import sys
from abc import ABC, abstractmethod
from typing import Callable

from src.gamestate import GameState
from src.pathfinding import manhattan
from src.schemas import Coords


def simple_tie_breaker(
    scored_candidates: dict[Coords, tuple[list[Coords], float]],
) -> tuple[Coords, list[Coords]]:
    """Pick move with minimal score (closest to center)."""
    best = min(scored_candidates.items(), key=lambda x: x[1][1])[0]
    return best, scored_candidates[best][0]


class Strategy(ABC):
    name: str

    @abstractmethod
    def decide(self, game_state: GameState) -> Coords:
        """Decide the next move based on the game state."""
        pass


class LocalStrategy(Strategy):
    def __init__(
        self,
        name: str,
        evaluator: Callable[[GameState, Coords], tuple[list[Coords], float]],
        planner: Callable[[GameState], list[Coords]],
        tie_breaker: Callable[
            [dict[Coords, tuple[list[Coords], float]]],
            tuple[Coords, list[Coords]],
        ],
    ):
        self.name = name
        self.evaluator = evaluator
        self.planner = planner
        self.tie_breaker = tie_breaker

    def decide(self, game_state: GameState) -> Coords:
        if game_state.config is None:
            print("GameConfig must be set to decide moves", file=sys.stderr)
            return game_state.bot
        candidates = self.planner(game_state)
        scored_candidates = {
            target: self.evaluator(game_state, target) for target in candidates
        }
        best_candidate, best_path = self.tie_breaker(scored_candidates)
        if best_candidate and best_candidate != game_state.bot:
            if best_path and len(best_path) > 1:
                next_step = best_path[1]
                return next_step
        return game_state.bot


class GlobalGreedyStrategy(Strategy):
    def __init__(
        self, greedy_strategy, search_strategy, name: str = "GlobalGreedyStrategy"
    ):
        self.greedy_strategy = greedy_strategy
        self.search_strategy = search_strategy
        self.name = name

    def get_strategy(self, game_state: GameState) -> Strategy:
        reachable_gems = [gem for gem in game_state.visible_gems if gem.reachable]
        if not reachable_gems:
            return self.search_strategy
        else:
            return self.greedy_strategy

    def decide(self, game_state: GameState) -> Coords:
        strategy = self.get_strategy(game_state)
        if strategy.name != game_state.current_strategy:
            print(
                f"[{self.name}] Switching strategy to: {strategy.name}", file=sys.stderr
            )
        game_state.current_strategy = strategy.name
        return strategy.decide(game_state)


class GlobalReachableStrategy(Strategy):
    def __init__(
        self, greedy_strategy, search_strategy, name: str = "GlobalReachableStrategy"
    ):
        self.greedy_strategy = greedy_strategy
        self.search_strategy = search_strategy
        self.name = name

    def get_strategy(self, game_state: GameState) -> Strategy:
        candidates = []
        for gem in game_state.visible_gems:
            if gem.distance2bot is not None and gem.reachable:
                for enemy in game_state.visible_bots:
                    if manhattan(gem.position, enemy.position) > gem.distance2bot:
                        candidates.append(gem.position)

        if not candidates:
            return self.search_strategy
        else:
            return self.greedy_strategy

    def decide(self, game_state: GameState) -> Coords:
        strategy = self.get_strategy(game_state)
        if strategy.name != game_state.current_strategy:
            print(
                f"[{self.name}] Switching strategy to: {strategy.name}", file=sys.stderr
            )
        game_state.current_strategy = strategy.name
        return strategy.decide(game_state)

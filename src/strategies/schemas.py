import sys
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from src.gamestate import GameState
from src.pathfinding import find_path
from src.schemas import Coords


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
        evaluator: Callable[[GameState, Coords], float],
        planner: Callable[[GameState], List[Coords]],
        tie_breaker: Callable[[List[Tuple[Coords, float]]], Optional[Coords]],
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
        scored_candidates = [
            (move, self.evaluator(game_state, move)) for move in candidates
        ]
        best = self.tie_breaker(scored_candidates)
        if best and best != game_state.bot:
            path = find_path(
                start=game_state.bot,
                goal=best,
                forbidden=set(walls_pos.position for walls_pos in game_state.wall),
                width=game_state.config.width,
                height=game_state.config.height,
            )
            if path and len(path) > 1:
                next_step = path[1]
                return next_step
        return game_state.bot


class GlobalGreedyStrategy(Strategy):
    def __init__(self, greedy_strategy, search_strategy):
        self.greedy_strategy = greedy_strategy
        self.search_strategy = search_strategy
        self.name = "GlobalGreedyStrategy"

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


def simple_tie_breaker(
    scored_candidates: List[Tuple[Coords, float]],
) -> Optional[Coords]:
    """Pick move with minimal score (closest to center)."""
    if not scored_candidates:
        return None
    best = min(scored_candidates, key=lambda x: x[1])[0]
    return best

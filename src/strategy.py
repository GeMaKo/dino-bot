from abc import ABC, abstractmethod

from src.gamestate import GameState
from src.pathfinding import find_path
from src.schemas import Coords


class Strategy(ABC):
    name: str

    @abstractmethod
    def decide(self, game_state: GameState) -> Coords:
        pass


class ModularStrategy(Strategy):
    name = "ModularStrategy"

    def __init__(self, name, evaluator, planner, tie_breaker):
        self.name = name
        self.evaluator = evaluator
        self.planner = planner
        self.tie_breaker = tie_breaker

    def decide(self, game_state) -> Coords:
        candidates = self.planner(game_state)
        scored_candidates = [
            (move, self.evaluator(game_state, move)) for move in candidates
        ]
        best = self.tie_breaker(scored_candidates)
        return best if best else game_state.bot


def greedy_planner(game_state: GameState) -> list[Coords]:
    # Plan: Only consider moves towards visible gems
    assert game_state.config is not None, "GameConfig must be set to plan moves"
    return [
        gem.position for gem in game_state.visible_gems if gem.distance2bot is not None
    ]


def greedy_evaluator(game_state: GameState, move: Coords) -> int:
    # Evaluate: Use path length from bot to gem
    assert game_state.config is not None, "GameConfig must be set to evaluate moves"
    path = find_path(
        start=game_state.bot,
        goal=move,
        forbidden=set(walls_pos.position for walls_pos in game_state.wall),
        width=game_state.config.width,
        height=game_state.config.height,
    )
    return len(path)


def greedy_tie_breaker(scored_candidates: list[tuple[Coords, int]]) -> Coords:
    # Tie breaker: Pick move with minimal score (shortest path)
    return min(scored_candidates, key=lambda x: x[1])[0]

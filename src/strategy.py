import sys
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from src.config import DISTANCE_TO_ENEMY
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


def greedy_planner(game_state: GameState) -> List[Coords]:
    """Plan moves towards visible gems."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    candidates = [
        gem.position for gem in game_state.visible_gems if gem.distance2bot is not None
    ]
    if not candidates:
        candidates = [game_state.bot]
    return candidates


def greedy_evaluator(game_state: GameState, move: Coords) -> float:
    """Evaluate moves using path length from bot to move."""
    if game_state.config is None:
        print("GameConfig must be set to evaluate moves", file=sys.stderr)
        return float("inf")
    path = find_path(
        start=game_state.bot,
        goal=move,
        forbidden=game_state.wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
    )
    return len(path) if path else float("inf")


def simple_search_planner(game_state: GameState) -> List[Coords]:
    """Plan moves for search mode (e.g., towards center, avoiding enemies)."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    directions = [
        Coords(game_state.bot.x + dx, game_state.bot.y + dy)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
    ]
    # Filter out walls and out-of-bounds
    candidates = [
        pos
        for pos in directions
        if 0 <= pos.x < game_state.config.width
        and 0 <= pos.y < game_state.config.height
        and pos not in [w.position for w in game_state.wall]
    ]
    if not candidates:
        candidates = [game_state.bot]
    return candidates


def simple_search_evaluator(game_state: GameState, move: Coords) -> float:
    """Score moves by shortest path length to center (lower is better)."""
    if game_state.config is None:
        return float("inf")
    center = Coords(game_state.config.width // 2, game_state.config.height // 2)
    path = find_path(
        start=move,
        goal=center,
        forbidden=game_state.wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
    )
    return len(path) if path else float("inf")


def simple_tie_breaker(
    scored_candidates: List[Tuple[Coords, float]],
) -> Optional[Coords]:
    """Pick move with minimal score (closest to center)."""
    if not scored_candidates:
        return None
    best = min(scored_candidates, key=lambda x: x[1])[0]
    return best


def advanced_search_planner(game_state: GameState) -> List[Coords]:
    """Plan moves for advanced search mode (center bias, enemy avoidance)."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    bot_pos = game_state.bot
    directions = [
        Coords(bot_pos.x + dx, bot_pos.y + dy)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
    ]
    # Filter out walls, out-of-bounds, and recent positions
    candidates = [
        pos
        for pos in directions
        if 0 <= pos.x < game_state.config.width
        and 0 <= pos.y < game_state.config.height
        and pos not in [w.position for w in game_state.wall]
        and pos not in game_state.recent_positions
    ]
    if not candidates:
        candidates = [game_state.bot]
    return candidates


def advanced_search_evaluator(game_state: GameState, move: Coords) -> float:
    """Score moves by center bias and enemy avoidance."""
    assert game_state is not None
    assert game_state.config is not None
    if game_state.config is None:
        return float("inf")
    center = Coords(game_state.config.width // 2, game_state.config.height // 2)
    bot_pos = game_state.bot
    visible_enemies = game_state.visible_bots
    closest_enemy = min(
        visible_enemies,
        key=lambda e: abs(e.position.x - bot_pos.x) + abs(e.position.y - bot_pos.y),
        default=None,
    )
    center_dist = abs(move.x - center.x) + abs(move.y - center.y)
    score = center_dist
    if closest_enemy:
        enemy_center_dist = abs(closest_enemy.position.x - center.x) + abs(
            closest_enemy.position.y - center.y
        )
        bot_center_dist = abs(bot_pos.x - center.x) + abs(bot_pos.y - center.y)
        enemy_dist = abs(move.x - closest_enemy.position.x) + abs(
            move.y - closest_enemy.position.y
        )
        # If bot is at least DISTANCE_TO_ENEMY steps closer to center than enemy, move towards enemy
        if bot_center_dist <= enemy_center_dist - DISTANCE_TO_ENEMY:
            score += enemy_dist
        # Otherwise, move towards center
        elif bot_center_dist >= enemy_center_dist:
            score += center_dist
        # Stay close to enemy (distance DISTANCE_TO_ENEMY), but keep center advantage
        elif center_dist < enemy_center_dist:
            score += abs(enemy_dist - DISTANCE_TO_ENEMY) * 10 + center_dist
        else:
            score += center_dist
    return score


def advanced_search_tie_breaker(
    scored_candidates: List[Tuple[Coords, float]],
) -> Optional[Coords]:
    """Pick move with minimal score."""
    if not scored_candidates:
        return None
    best = min(scored_candidates, key=lambda x: x[1])[0]
    return best

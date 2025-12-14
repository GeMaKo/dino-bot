import sys

from src.bot_logic import get_best_gem_collection_path
from src.config import CENTER_MOVE_WEIGHT, CENTER_STAY_WEIGHT, DISTANCE_TO_ENEMY
from src.gamestate import GameState, get_pre_filled_cached_path
from src.pathfinding import manhattan
from src.schemas import Coords


def greedy_evaluator(game_state: GameState, move: Coords) -> tuple[list[Coords], float]:
    """Evaluate moves using path length from bot to move."""
    if game_state.config is None:
        print("GameConfig must be set to evaluate moves", file=sys.stderr)
        return [], float("inf")
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        forbidden=game_state.known_wall_positions,
        target=move,
        game_state=game_state,
    )
    return path, len(path) if path else float("inf")


def tsm_evaluator(game_state: GameState, move: Coords) -> tuple[list[Coords], float]:
    """Evaluate moves for TSV strategy (stub implementation)."""
    if game_state.config is None:
        return [], float("inf")
    # Filter gems to those at the candidate position
    gems = [gem for gem in game_state.visible_gems if gem.position == move]
    if not gems:
        return [], float("inf")
    path = get_best_gem_collection_path(
        bot_pos=game_state.bot,
        gems=gems,
        walls=game_state.wall,
        width=game_state.config.width,
        height=game_state.config.height,
        enemies=game_state.visible_bots,
        initiative=game_state.initiative,
        distance_matrix=game_state.distance_matrix,
        path_segments=game_state.path_segments,
    )
    score = len(path) if path else float("inf")
    return path if path is not None else [], score


def simple_search_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """Score moves by shortest path length to center (lower is better)."""
    if game_state.config is None:
        return [], float("inf")
    path = get_pre_filled_cached_path(
        start=move,
        forbidden=game_state.known_wall_positions,
        target=game_state.center,
        game_state=game_state,
    )
    score = len(path) if path else float("inf")
    return path if path is not None else [], score


def advanced_search_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """Score moves by center bias and enemy avoidance."""
    assert game_state is not None
    assert game_state.config is not None
    if game_state.config is None:
        return [], float("inf")
    bot_pos = game_state.bot
    visible_enemies = game_state.visible_bots
    closest_enemy = min(
        visible_enemies,
        key=lambda e: abs(e.position.x - bot_pos.x) + abs(e.position.y - bot_pos.y),
        default=None,
    )
    center = game_state.center
    if bot_pos == center and move == center:
        return [], CENTER_STAY_WEIGHT  # Large negative score to prefer WAIT/stay
    # Penalize moving away from center if already there
    if bot_pos == center and move != center:
        if closest_enemy:
            enemy_center_dist = manhattan(closest_enemy.position, center)
            # If enemy is farther from center than DISTANCE_TO_ENEMY, follow at DISTANCE_TO_ENEMY
            if enemy_center_dist > DISTANCE_TO_ENEMY:
                # Score moves that bring bot to DISTANCE_TO_ENEMY from enemy
                enemy_dist = manhattan(move, closest_enemy.position)
                score = abs(enemy_dist - DISTANCE_TO_ENEMY) + 2
                path = get_pre_filled_cached_path(
                    start=game_state.bot,
                    forbidden=game_state.known_wall_positions,
                    target=move,
                    game_state=game_state,
                )
                # Prefer moves that are not the center and bring bot closer to enemy
                if move != center:
                    return path if path is not None else [], score
        # Default: discourage leaving center if not following enemy
        return [], CENTER_MOVE_WEIGHT
    center_dist = manhattan(move, center)
    score = center_dist
    if closest_enemy:
        enemy_center_dist = manhattan(closest_enemy.position, center)
        bot_center_dist = manhattan(bot_pos, center)
        enemy_dist = manhattan(move, closest_enemy.position)
        # If bot is at least DISTANCE_TO_ENEMY steps closer to center than enemy, move towards enemy
        if bot_center_dist <= enemy_center_dist - 1:
            score += enemy_dist
        # Otherwise, move towards center
        elif bot_center_dist >= enemy_center_dist:
            score += center_dist - 2
        # Stay close to enemy (distance DISTANCE_TO_ENEMY), but keep center advantage
        elif center_dist < enemy_center_dist:
            score += abs(enemy_dist - DISTANCE_TO_ENEMY) + center_dist
        else:
            score += center_dist
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        forbidden=game_state.known_wall_positions,
        target=move,
        game_state=game_state,
    )
    return path if path is not None else [], score

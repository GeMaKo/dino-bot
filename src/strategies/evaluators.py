import sys

from src.bot_logic import get_best_gem_collection_path
from src.config import CENTER_MOVE_WEIGHT, CENTER_STAY_WEIGHT, DISTANCE_TO_ENEMY
from src.gamestate import GameState
from src.pathfinding import find_path, manhattan
from src.schemas import Coords


def greedy_evaluator(game_state: GameState, move: Coords) -> tuple[list[Coords], float]:
    """Evaluate moves using path length from bot to move."""
    if game_state.config is None:
        print("GameConfig must be set to evaluate moves", file=sys.stderr)
        return [], float("inf")
    path = find_path(
        start=game_state.bot,
        goal=move,
        forbidden=game_state.wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
    )
    return path, len(path) if path else float("inf")


def _get_path(start, forbidden, target, game_state):
    assert game_state.config is not None, "GameConfig must be set to evaluate moves"
    return find_path(
        start=start,
        goal=target,
        forbidden=forbidden,
        width=game_state.config.width,
        height=game_state.config.height,
    )


def greedy_blocking_evaluator(
    game_state: GameState, target: Coords
) -> tuple[list[Coords], float]:
    if game_state.config is None:
        print("GameConfig must be set to evaluate moves", file=sys.stderr)
        return [], float("inf")
    for enemy in game_state.visible_bots:
        is_close = (
            enemy.position in game_state.bot_diagonal_positions
            or enemy.position in game_state.bot_adjacent_positions
        )
        if is_close:
            # Both bot and enemy try to reach the target
            if game_state.initiative:
                # Both bot and enemy try to reach the target
                enemy_path = _get_path(
                    enemy.position, game_state.wall_positions, target, game_state
                )
                bot_path = _get_path(
                    game_state.bot, game_state.wall_positions, target, game_state
                )

                # Ensure both paths exist and enemy has at least one move
                if not bot_path or not enemy_path or len(enemy_path) <= 1:
                    return bot_path if bot_path else [], float("inf")

                block_move = enemy_path[1]  # Enemy's next move towards target
                if block_move not in game_state.bot_adjacent_positions:
                    return bot_path, len(bot_path) if bot_path else float("inf")

                # Simulate bot moving to block enemy's next move
                block_path = _get_path(
                    block_move, game_state.wall_positions, target, game_state
                )

                # Only block if it brings bot closer to target
                bot_distance = manhattan(game_state.bot, target)
                block_distance = manhattan(block_move, target)

                if block_path and block_distance < bot_distance:
                    # Score is path length minus 2 (to prioritize shorter paths and blocking)
                    score = len(block_path) - 2
                    block_path.insert(0, block_move)  # Include blocking move
                    print(
                        "[CloseEncounter] Blocking enemy and advancing!",
                        file=sys.stderr,
                    )
                    return block_path, score
            else:
                # Block enemy by treating their adjacent cells as walls
                enemy_moves = {
                    Coords(enemy.position.x + 1, enemy.position.y),
                    Coords(enemy.position.x - 1, enemy.position.y),
                    Coords(enemy.position.x, enemy.position.y + 1),
                    Coords(enemy.position.x, enemy.position.y - 1),
                }
                bot_path = _get_path(
                    game_state.bot,
                    game_state.wall_positions.union(enemy_moves),
                    target,
                    game_state,
                )
                return bot_path, len(bot_path) - 2 if bot_path else float("inf")
        # Default path if not close
        bot_path = find_path(
            start=game_state.bot,
            goal=target,
            forbidden=game_state.wall_positions,
            width=game_state.config.width,
            height=game_state.config.height,
        )
        score = len(bot_path) if bot_path else float("inf")

    return bot_path if bot_path is not None else [], score  # type: ignore


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
    path = find_path(
        start=move,
        goal=game_state.center,
        forbidden=game_state.wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
    )
    score = len(path) if path else float("inf")
    return path, score


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
        return (
            [],
            CENTER_MOVE_WEIGHT,
        )  # Large positive score to discourage leaving center

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
    path = find_path(
        start=game_state.bot,
        goal=move,
        forbidden=game_state.wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
    )
    return path if path is not None else [], score

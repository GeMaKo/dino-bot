import sys

from src.gamestate import GameState, get_pre_filled_cached_path
from src.pathfinding import manhattan
from src.schemas import Coords


def greedy_planner(game_state: GameState) -> list[Coords]:
    """Plan moves towards visible gems."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    candidates = [
        gem.position
        for gem in game_state.known_gems.values()
        if gem.distance2bot is not None
    ]
    if not candidates:
        candidates = [game_state.bot]
    return candidates


def greedy_blocking_evaluator(
    game_state: GameState, target: Coords
) -> tuple[list[Coords], float]:
    if game_state.config is None:
        print("GameConfig must be set to evaluate moves", file=sys.stderr)
        return [], float("inf")

    # Default path if not close
    bot_path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=target,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    if bot_path and len(bot_path) > 1 and bot_path[1] == target:
        # print("Next move is on the gem!", file=sys.stderr)
        game_state.gem_captured_tick = game_state.tick

    score = len(bot_path) if bot_path else float("inf")

    for enemy in game_state.visible_bots:
        is_close = (
            enemy.position in game_state.bot_diagonal_positions
            or enemy.position in game_state.bot_adjacent_positions
        )
        if is_close:
            # Both bot and enemy try to reach the target
            if game_state.initiative:
                # Both bot and enemy try to reach the target
                enemy_path = get_pre_filled_cached_path(
                    start=enemy.position,
                    target=target,
                    forbidden=game_state.known_wall_positions,
                    game_state=game_state,
                )
                bot_path = get_pre_filled_cached_path(
                    start=game_state.bot,
                    target=target,
                    forbidden=game_state.known_wall_positions,
                    game_state=game_state,
                )

                # Ensure both paths exist and enemy has at least one move
                if not bot_path or not enemy_path or len(enemy_path) <= 1:
                    return bot_path if bot_path else [], float("inf")

                block_move = enemy_path[1]  # Enemy's next move towards target
                if block_move not in game_state.bot_adjacent_positions:
                    return bot_path, len(bot_path) if bot_path else float("inf")

                # Simulate bot moving to block enemy's next move
                block_path = get_pre_filled_cached_path(
                    start=block_move,
                    forbidden=game_state.known_wall_positions,
                    target=target,
                    game_state=game_state,
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
                bot_path = get_pre_filled_cached_path(
                    start=game_state.bot,
                    forbidden=game_state.known_wall_positions.union(enemy_moves),
                    target=target,
                    game_state=game_state,
                )
                return bot_path, len(bot_path) - 2 if bot_path else float("inf")

    return bot_path if bot_path is not None else [], score  # type: ignore


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

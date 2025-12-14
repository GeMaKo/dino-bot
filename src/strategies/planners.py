import sys

from src.gamestate import GameState
from src.schemas import Coords


def advanced_search_planner(game_state: GameState) -> list[Coords]:
    """Plan moves for advanced search mode (center bias, enemy avoidance)."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    directions = game_state.bot_adjacent_positions
    # Filter out walls, out-of-bounds, and recent positions
    candidates = [game_state.bot] + [
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


def simple_search_planner(game_state: GameState) -> list[Coords]:
    """Plan moves for search mode (e.g., towards center, avoiding enemies)."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    directions = game_state.bot_adjacent_positions
    # Filter out walls and out-of-bounds
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

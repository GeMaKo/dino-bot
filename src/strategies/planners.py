import sys

from src.gamestate import GameState
from src.schemas import Coords


def greedy_planner(game_state: GameState) -> list[Coords]:
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


def reachable_planner(game_state: GameState) -> list[Coords]:
    """Plan moves towards reachable visible gems only."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    candidates = [
        gem.position
        for gem in game_state.visible_gems
        if gem.distance2bot is not None and gem.reachable
    ]
    if not candidates:
        candidates = [game_state.bot]
    return candidates


def advanced_search_planner(game_state: GameState) -> list[Coords]:
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
    candidates = [bot_pos] + [
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

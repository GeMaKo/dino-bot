import sys

from src.gamestate import GameState
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


def find_hidden_positions(game_state: GameState) -> list[Coords]:
    """Return hidden positions adjacent to known floor tiles."""
    assert game_state.config is not None, (
        "GameConfig must be set to find hidden positions"
    )
    known_floor_positions = set(game_state.known_floors.keys())

    def _adjacent(pos: Coords, width: int, height: int) -> list[Coords]:
        return [
            Coords(pos.x + dx, pos.y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if 0 <= pos.x + dx < width and 0 <= pos.y + dy < height
        ]

    hidden = [
        pos
        for pos in game_state.hidden_positions
        if any(
            adj in known_floor_positions
            for adj in _adjacent(pos, game_state.config.width, game_state.config.height)
        )
    ]
    return hidden


def cave_explore_planner(game_state: GameState) -> list[Coords]:
    """Plan moves to hidden positions blocked by walls, or oldest visited floor."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return [game_state.bot]
    if game_state.explore_target is not None:
        game_state.explore_target = None
    if game_state.cave_revealed:
        hidden = []
    else:
        hidden = find_hidden_positions(game_state)
        if not hidden:
            game_state.cave_revealed = True
            print("Cave fully revealed!", file=sys.stderr)
            print("Switching to oldest floor exploration.", file=sys.stderr)

    if hidden:
        # If previous target is still valid, keep it
        if (
            game_state.explore_target in hidden
            and game_state.explore_target not in game_state.recent_positions
        ):
            target = game_state.explore_target
        else:
            target = min(hidden, key=lambda pos: manhattan(game_state.bot, pos))
            game_state.explore_target = target
        return [target]
    if game_state.known_floors:
        oldest_floor = min(
            game_state.known_floors.values(),
            key=lambda f: f.last_seen,
        )
        return [oldest_floor.position]

    # Fallback: stay in place
    return [game_state.bot]


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

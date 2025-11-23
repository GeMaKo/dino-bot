import heapq
import sys

from src.bot_logic import solve_set_cover
from src.debug import highlight_coords
from src.gamestate import GameState
from src.pathfinding import find_path, manhattan
from src.schemas import BehaviourState, Coords


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


def patrol_oldest_floor(game_state: GameState) -> list[Coords]:
    oldest_floor = min(
        game_state.known_floors.values(),
        key=lambda f: f.last_seen,
    )
    return [oldest_floor.position]


def order_patrol_points(
    start: Coords,
    patrol_points: set[Coords],
    forbidden: set[Coords],
    width: int,
    height: int,
    patrol_points_visited: set[Coords],
    visited_penalty: int = 100,
) -> list[Coords]:
    if patrol_points_visited is None:
        patrol_points_visited = set()
    route = []
    points = set(patrol_points)
    current = start
    while points:
        next_point = min(
            points,
            key=lambda p: (
                len(find_path(current, p, forbidden, width, height))
                + (visited_penalty if p in patrol_points_visited else 0)
            ),
        )
        route.append(next_point)
        points.remove(next_point)
        current = next_point
    return route


def patrol_set_cover(game_state: GameState) -> list[Coords]:
    if not game_state.patrol_points or game_state.tick % 100 == 0:
        print("Recomputing patrol points using set cover.", file=sys.stderr)
        game_state.patrol_points = solve_set_cover(
            game_state.view_points, set(game_state.known_floors.keys())
        )
    # Find the closest patrol point to the bot
    if game_state.behaviour_state != BehaviourState.PATROLLING:
        print("Switching to PATROLLING behaviour.", file=sys.stderr)
        game_state.behaviour_state = BehaviourState.PATROLLING
        closest = min(
            game_state.patrol_points,
            key=lambda p: len(
                find_path(
                    game_state.bot,
                    p,
                    game_state.wall_positions,
                    game_state.config.width,
                    game_state.config.height,
                )
            ),
        )
        # Order patrol points starting from the closest
        ordered_route = order_patrol_points(
            closest,
            game_state.patrol_points,
            game_state.wall_positions,
            game_state.config.width,
            game_state.config.height,
            set(game_state.patrol_points_visited),
        )
        game_state.patrol_route = ordered_route
        # Set patrol_index to the closest point
        game_state.patrol_index = 0

    target = game_state.patrol_route[game_state.patrol_index]
    highlight_coords.extend(game_state.patrol_route)

    # Advance patrol_index when bot arrives at the target
    if game_state.bot == target:
        game_state.patrol_index = (game_state.patrol_index + 1) % len(
            game_state.patrol_route
        )
        game_state.patrol_points_visited.append(target)
        target = game_state.patrol_route[game_state.patrol_index]
    return [target]


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


def cave_explore_planner(
    game_state: GameState, patrol_mode: str = "set_cover"
) -> list[Coords]:
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
            print("Switching floor patrol.", file=sys.stderr)

    if hidden:
        if game_state.behaviour_state != BehaviourState.EXPLORING:
            print("Switching to EXPLORING behaviour.", file=sys.stderr)
        game_state.behaviour_state = BehaviourState.EXPLORING
        # If previous target is still valid, keep it
        if (
            game_state.explore_target in hidden
            and game_state.explore_target not in game_state.recent_positions
        ):
            target = game_state.explore_target
        else:
            top3targets = heapq.nsmallest(
                3, hidden, key=lambda pos: manhattan(game_state.bot, pos)
            )
            target = min(
                top3targets,
                key=lambda pos: len(
                    find_path(
                        game_state.bot,
                        pos,
                        game_state.wall_positions,
                        game_state.config.width,
                        game_state.config.height,
                    )
                ),
            )
            game_state.explore_target = target
        return [target]
    if game_state.known_floors:
        if patrol_mode == "oldest":
            return patrol_oldest_floor(game_state)
        elif patrol_mode == "set_cover":
            return patrol_set_cover(game_state)
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

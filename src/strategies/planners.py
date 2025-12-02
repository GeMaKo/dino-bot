import heapq
import sys

from src.debug import highlight_coords
from src.gamestate import GameState
from src.pathfinding import cached_find_path, manhattan
from src.schemas import BehaviourState, Coords
from src.strategies.aco import ant_colony_optimization
from src.strategies.exploration import find_hidden_positions
from src.strategies.set_cover import set_cover_patrol
from src.strategies.simple import oldest_floor_patrol


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


def aco_patrol_planner(game_state: GameState) -> list[Coords]:
    """
    Plan patrol or collection path using Ant Colony Optimization (ACO).
    """
    if not game_state.patrol_points:
        highlight_coords.extend(game_state.exploration_points_visited)
        game_state.patrol_points = set(game_state.exploration_points_visited)

    best_path = ant_colony_optimization(
        start=game_state.bot,
        targets=game_state.patrol_points,
        walls=game_state.known_wall_positions,
        width=game_state.config.width,
        height=game_state.config.height,
        distance_function=cached_find_path,
    )
    highlight_coords.extend(best_path)
    game_state.current_patrol_path = best_path
    return best_path


def cave_explore_planner(
    game_state: GameState, patrol_mode: str = "oldest"
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
                    cached_find_path(
                        game_state.bot,
                        pos,
                        game_state.known_wall_positions,
                        game_state.config.width,
                        game_state.config.height,
                    )
                ),
            )
            game_state.explore_target = target
        return [target]
    if game_state.known_floors:
        if game_state.behaviour_state != BehaviourState.PATROLLING:
            print("Switching to PATROLLING behaviour.", file=sys.stderr)
            game_state.behaviour_state = BehaviourState.PATROLLING
        if patrol_mode == "oldest":
            return oldest_floor_patrol(game_state)
        elif patrol_mode == "set_cover":
            return set_cover_patrol(game_state)
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

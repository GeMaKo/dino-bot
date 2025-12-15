import sys

from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.pathfinding import cached_find_path  # Assuming this is your distance function
from src.schemas import Coords
from src.strategies.aco import ant_colony_optimization


def simple_patrol_route_planner(game_state: GameState) -> list[Coords]:
    """
    Generate the next patrol target(s) based on the patrol points.
    """
    # Ensure patrol points exist
    if not game_state.patrol_points:
        print("No patrol points defined.", file=sys.stderr)
        return []

    # Determine the current target dynamically
    patrol_points_list = list(game_state.patrol_points)
    current_target = patrol_points_list[game_state.patrol_index]
    if game_state.bot == current_target:
        # Move to the next patrol point
        game_state.patrol_index = (game_state.patrol_index + 1) % len(
            game_state.patrol_points
        )
        patrol_points_list = list(game_state.patrol_points)
        current_target = patrol_points_list[game_state.patrol_index]
        print(
            f"Reached patrol point. Moving to next patrol point: {current_target} {game_state.patrol_index}",
            file=sys.stderr,
        )
    highlight_coords.append(
        HighlightCoords("patrol_target", [current_target], "#0000ff")
    )

    # Return the current target as the next move candidate
    return [current_target]


def oldest_floor_patrol_planner(game_state: GameState) -> list[Coords]:
    """
    Plan patrol moves to the oldest known floor positions.
    """
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return []

    # Sort known floor positions by their last visited timestamp
    sorted_floors = sorted(
        game_state.known_floors.items(), key=lambda item: item[1].last_seen
    )

    highlight_coords.append(
        HighlightCoords("oldest_floors", [sorted_floors[0][0]], "#00ffff")
    )

    return [sorted_floors[0][0]]


def aco_patrol_planner(game_state: GameState) -> list[Coords]:
    """
    Plan patrol moves using Ant Colony Optimization (ACO), considering the bot's current position.
    """
    if not game_state.patrol_points:
        print("No patrol points defined.", file=sys.stderr)
        return []
    assert game_state.config is not None

    # Prepare inputs for ACO
    start = game_state.bot
    targets = game_state.patrol_points
    walls = game_state.known_wall_positions
    width = game_state.config.width
    height = game_state.config.height

    # Call ACO function to generate the full path
    full_path = ant_colony_optimization(
        start=start,
        targets=targets,
        walls=walls,
        width=width,
        height=height,
        distance_function=cached_find_path,  # Replace with your actual pathfinding function
        num_ants=10,
        num_iterations=50,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.5,
        pheromone_boost=1.0,
    )
    print(f"[ACO Patrol] Planned full path: {full_path}", file=sys.stderr)

    # Highlight the path for debugging
    highlight_coords.append(HighlightCoords("aco_patrol_path", full_path, "#00ff59"))

    # If the bot is not on the path, find the nearest point on the path
    if start not in full_path:
        print("Bot is not on the planned path. Finding nearest point.", file=sys.stderr)
        nearest_point = min(
            full_path,
            key=lambda point: len(cached_find_path(start, point, walls, width, height)),
        )
        print(f"Nearest point on path: {nearest_point}", file=sys.stderr)

        # Recalculate the path starting from the nearest point
        nearest_index = full_path.index(nearest_point)
        adjusted_path = [start] + full_path[nearest_index:]
    else:
        # Continue from the bot's current position
        adjusted_path = full_path[full_path.index(start) :]

    print(f"[ACO Patrol] Adjusted path: {adjusted_path}", file=sys.stderr)

    # Return the adjusted path
    return adjusted_path


def patrol_evaluator(game_state: GameState, move: Coords) -> tuple[list[Coords], float]:
    """
    Evaluate moves during patrol based on distance to the next patrol point.
    """
    # Calculate the path to the target
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    score = len(path) if path else float("inf")

    return path if path is not None else [], score


def aco_patrol_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """
    Evaluate moves during patrol based on distance to the next patrol point.
    """
    # Ensure the ACO path exists
    if not hasattr(game_state, "aco_path") or not game_state.aco_path:
        print("ACO path not found. Evaluator cannot proceed.", file=sys.stderr)
        return [], float("inf")

    # Calculate the path to the target
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    score = len(path) if path else float("inf")

    # Prefer moves that align with the ACO path
    if move in game_state.aco_path:
        score -= 10  # Favor moves on the ACO path

    return path if path is not None else [], score

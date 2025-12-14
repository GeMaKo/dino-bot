import sys

from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.schemas import Coords


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

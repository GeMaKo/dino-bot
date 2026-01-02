import sys

from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.schemas import Coords, ViewPoint


def oldest_floor_patrol_planner(game_state: GameState) -> list[Coords]:
    """
    Plan patrol moves to the oldest known floor positions.
    """
    # Sort known floor positions by their last visited timestamp
    sorted_floors = sorted(
        game_state.known_floors.items(), key=lambda item: item[1].last_seen
    )

    highlight_coords.append(
        HighlightCoords("oldest_floors", [sorted_floors[0][0]], "#00ffff")
    )

    return [sorted_floors[0][0]]


def simple_patrol_point_planner(game_state: GameState) -> list[Coords]:
    """
    Plan patrol moves to the defined patrol points.
    """
    return list(game_state.patrol_points)


def last_seen_sum_patrol_point_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """
    Evaluate moves during patrol based on distance to the next patrol point.
    """
    score = 0
    current_tick = game_state.tick
    ticks_since_last_capture = current_tick - game_state.gem_captured_tick
    last_seen_sum = 0
    k = 100  # scaling constant for exponential growth
    diversity_penalty = 0
    enemy_penalty = 0
    recency_scaling = 2
    criticality_scaling = 2
    viewpoint = game_state.visibility_map.get(move, ViewPoint(position=move))
    if {enemy.position for enemy in game_state.visible_bots} in viewpoint.visible_tiles:
        enemy_penalty = 10000  # Large penalty for enemy in range
    if set(game_state.last_n_ticks_bot_positions).intersection(viewpoint.visible_tiles):
        diversity_penalty = 10000  # Penalty for being visible to enemies
    criticality_factor = 1 + (ticks_since_last_capture / k) ** criticality_scaling

    for seen_tile in viewpoint.visible_tiles:
        ticks_since_last_seen = abs(
            current_tick - game_state.known_floors[seen_tile].last_seen
        )
        last_seen_sum += ticks_since_last_seen**recency_scaling * criticality_factor
    if False:
        print(
            f"[LastSeenSum Patrol] Evaluated move {move} with last_seen_sum {last_seen_sum}, "
            f"diversity_penalty {diversity_penalty}, enemy_penalty {enemy_penalty}",
            file=sys.stderr,
        )
    score = 1 / (last_seen_sum + diversity_penalty + enemy_penalty + 1)
    # Calculate the path to the target
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    # print(
    #    f"[LastSeenSum Patrol] Evaluated move {move} with score {score}",
    #    file=sys.stderr,
    # )
    return path if path is not None else [], score


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

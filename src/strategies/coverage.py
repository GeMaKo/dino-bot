import heapq

from src.config import (
    PROBABILITY_WEIGHT,
    RECENCY_PENALTY_WEIGHT,
)
from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.schemas import Coords, Floor


def coverage_planner(game_state: GameState) -> list[Coords]:
    """
    Selects the floor tile with the highest probability of a gem spawn since the last capture.
    """
    current_tick = game_state.tick
    gem_spawn_rate = game_state.config.gem_spawn_rate
    gem_captured_tick = game_state.gem_captured_tick
    ticks_since_capture = current_tick - gem_captured_tick

    def gem_score(floor_info: Floor):
        ticks_after_capture = max(floor_info.last_seen - gem_captured_tick, 0)
        ticks_unseen = ticks_since_capture - ticks_after_capture
        prob = 1 - (1 - gem_spawn_rate) ** ticks_unseen if ticks_unseen > 0 else 0
        recency_penalty = 1 / (1 + ticks_after_capture)
        # bot_pos = game_state.bot
        # dist = manhattan(bot_pos, floor_info.position)
        # distance_penalty = 1 / (1 + dist)
        # Combine scores with weights from config
        return (
            prob * PROBABILITY_WEIGHT * recency_penalty * RECENCY_PENALTY_WEIGHT
            # * distance_penalty
            # * DISTANCE_PENALTY_WEIGHT
        )

    top_tiles = heapq.nlargest(
        5,
        game_state.known_floors.items(),
        key=lambda item: gem_score(item[1]),
    )
    best_tiles = [item[0] for item in top_tiles]
    highlight_coords.append(
        HighlightCoords(
            "coverage_best_tiles",
            best_tiles,
            "#00ff00" if best_tiles else "#ff0000",
        )
    )
    return best_tiles


def coverage_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """
    Evaluate moves during patrol based on distance to the next patrol point,
    factoring in the number of tiles refreshed and their last_seen values.
    Older tiles contribute more to the score.
    """
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )

    if not path:
        return [], float("inf")

    # Score: sum of (current_tick - last_seen) for each tile in path
    current_tick = game_state.tick
    refreshed_score = 0
    for coords in path:
        floor_info = game_state.known_floors.get(coords)
        if floor_info:
            refreshed_score += current_tick - floor_info.last_seen

    # Higher score for older tiles, shorter path preferred
    # You can adjust the weighting as needed
    score = -refreshed_score + len(path)  # Negative so older tiles are prioritized

    return path, score

from src.config import (
    PROBABILITY_WEIGHT,
    RECENCY_PENALTY_WEIGHT,
)
from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState
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

    best = max(
        game_state.known_floors.items(),
        key=lambda item: gem_score(item[1]),
        default=(None, None),
    )
    best_tile = best[0]
    highlight_coords.append(
        HighlightCoords(
            "coverage_best_tile",
            [best_tile] if best_tile else [],
            "#00ff00" if best_tile else "#ff0000",
        )
    )

    return [best_tile] if best_tile else []

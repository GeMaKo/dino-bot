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
    gem_spawn_rate = game_state.config.gem_spawn_rate

    def gem_score(floor_info: Floor):
        # Time since this tile was last seen
        ticks_unseen = game_state.tick - floor_info.last_seen
        # Probability at least one gem has spawned since last seen
        prob = 1 - (1 - gem_spawn_rate) ** ticks_unseen if ticks_unseen > 0 else 0
        recency_penalty = 1 / (1 + ticks_unseen)
        return prob * PROBABILITY_WEIGHT * recency_penalty * RECENCY_PENALTY_WEIGHT

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

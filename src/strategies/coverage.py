from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState
from src.schemas import Coords


def coverage_planner(game_state: GameState) -> list[Coords]:
    """
    Selects the floor tile with the highest probability of a gem spawn since the last capture.
    """
    current_tick = game_state.tick
    gem_spawn_rate = game_state.config.gem_spawn_rate
    gem_captured_tick = game_state.gem_captured_tick
    ticks_since_capture = current_tick - gem_captured_tick

    def gem_prob(floor_info):
        ticks_after_capture = max(floor_info.last_seen - gem_captured_tick, 0)
        ticks_unseen = ticks_since_capture - ticks_after_capture
        return 1 - (1 - gem_spawn_rate) ** ticks_unseen if ticks_unseen > 0 else 0

    best = max(
        game_state.known_floors.items(),
        key=lambda item: gem_prob(item[1]),
        default=(None, None),
    )
    best_tile = best[0]
    best_prob = gem_prob(best[1]) if best[1] else -1.0

    highlight_coords.append(
        HighlightCoords(
            "coverage_best_tile",
            [best_tile] if best_tile else [],
            "#00ff00" if best_tile else "#ff0000",
        )
    )

    return [best_tile] if best_tile else []

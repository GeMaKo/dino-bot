from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState
from src.schemas import Coords


def coverage_planner(game_state: GameState) -> list[Coords]:
    current_tick = game_state.tick
    gem_spawn_rate = game_state.config.gem_spawn_rate

    best_tile = None
    best_prob = -1.0

    for floor_pos, floor_info in game_state.known_floors.items():
        ticks_after_capture = (
            (floor_info.last_seen - game_state.gem_captured_tick)
            if (floor_info.last_seen - game_state.gem_captured_tick) > 0
            else 0
        )
        ticks_unseen_after_capture = (
            current_tick - game_state.gem_captured_tick - ticks_after_capture
        )
        p_gem = 1 - (1 - gem_spawn_rate) ** ticks_unseen_after_capture
        if p_gem > best_prob:
            best_prob = p_gem
            best_tile = floor_pos
    highlight_coords.append(
        HighlightCoords(
            "coverage_best_tile", [best_tile], "#00ff00" if best_tile else "#ff0000"
        )
    )

    if best_tile is not None:
        return [best_tile]
    else:
        return []

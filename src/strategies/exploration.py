import sys

from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.pathfinding import manhattan
from src.schemas import Coords


def cave_explore_planner(game_state: GameState) -> list[Coords]:
    """Plan moves to all hidden positions."""
    hidden = game_state.update_hidden_floors()
    highlight_coords.append(HighlightCoords("hidden_positions", hidden, "#e2d21a97"))
    if len(game_state.last_path) > 0 and game_state.last_path[-1] in hidden:
        candidates = [game_state.last_path[-1]]  # Continue to last target
        print(
            f"Cave explore continuing to last target {game_state.last_path[-1]}",
            file=sys.stderr,
        )
    else:
        candidates = sorted(hidden, key=lambda pos: manhattan(game_state.bot, pos))[:1]
    highlight_coords.append(HighlightCoords("cave_explore_top3", candidates, "#b82d8a"))
    return candidates


def cave_explore_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """Evaluate moves towards hidden positions."""
    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    penalty = 0
    if game_state.last_bot_pos in path:
        penalty = 10
    score = (len(path) if path else float("inf")) + penalty
    return path if path else [], score

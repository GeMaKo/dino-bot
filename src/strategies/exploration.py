import sys

from src.debug import HighlightCoords, highlight_coords
from src.gamestate import GameState, get_pre_filled_cached_path
from src.pathfinding import manhattan
from src.schemas import Coords


def cave_explore_planner(game_state: GameState) -> list[Coords]:
    """Plan moves to all hidden positions."""
    if game_state.config is None:
        print("GameConfig must be set to plan moves", file=sys.stderr)
        return []

    hidden = game_state.update_hidden_floors()
    highlight_coords.append(HighlightCoords("hidden_positions", hidden, "#e2d21a97"))
    top5 = sorted(hidden, key=lambda pos: manhattan(game_state.bot, pos))[:5]
    return hidden  # Return all hidden positions as candidates


def cave_explore_evaluator(
    game_state: GameState, move: Coords
) -> tuple[list[Coords], float]:
    """Score moves by unexplored status and path length to oldest floor."""
    if game_state.config is None:
        return [], float("inf")

    # Bonus for moving into a hole
    bonus = (
        -20
        if move not in game_state.known_wall_positions
        and move not in game_state.known_floor_positions
        else 0
    )

    path = get_pre_filled_cached_path(
        start=game_state.bot,
        target=move,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    score = (len(path) if path else float("inf")) + bonus
    return path if path else [], score

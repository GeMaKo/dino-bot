from src.gamestate import GameState
from src.schemas import Coords


def unstuck_bot(game_state: GameState) -> tuple[Coords, list[Coords]]:
    """Simple unstucking strategy that moves the bot in a random valid direction."""
    from src.pathfinding import get_valid_moves

    valid_moves = get_valid_moves(
        start=game_state.bot,
        forbidden=game_state.known_wall_positions,
        game_state=game_state,
    )
    if not valid_moves:
        print("No valid moves available to unstuck the bot.", file=sys.stderr)
        return game_state.bot, [game_state.bot]

    # Choose the first valid move (could be randomized for more variety)
    next_move = valid_moves[0]
    path = [game_state.bot, next_move]
    return next_move, path

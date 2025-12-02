from src.gamestate import GameState
from src.schemas import Coords


def find_hidden_positions(game_state: GameState) -> list[Coords]:
    """Return hidden positions adjacent to known floor tiles."""
    assert game_state.config is not None, (
        "GameConfig must be set to find hidden positions"
    )
    known_floor_positions = set(game_state.known_floors.keys())

    def _adjacent(pos: Coords, width: int, height: int) -> list[Coords]:
        return [
            Coords(pos.x + dx, pos.y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if 0 <= pos.x + dx < width and 0 <= pos.y + dy < height
        ]

    hidden = [
        pos
        for pos in game_state.hidden_positions
        if any(
            adj in known_floor_positions
            for adj in _adjacent(pos, game_state.config.width, game_state.config.height)
        )
    ]
    return hidden

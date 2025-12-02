from src.gamestate import GameState
from src.schemas import Coords


def derive_initial_patrol_route(exploration_path: list[Coords]) -> list[Coords]:
    """
    Derive an initial patrol route from the exploration path.
    """
    # Remove duplicates while preserving order
    visited = []
    for node in exploration_path:
        if node not in visited:
            visited.append(node)

    # Close the loop by returning to the start
    if visited and visited[-1] != visited[0]:
        visited.append(visited[0])

    return visited


def oldest_floor_patrol(game_state: GameState) -> list[Coords]:
    oldest_floor = min(
        game_state.known_floors.values(),
        key=lambda f: f.last_seen,
    )
    return [oldest_floor.position]

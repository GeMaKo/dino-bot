from collections import deque
from typing import Callable

from config import Coords, Direction, Wall


def manhattan(a: Coords, b: Coords) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def bfs(
    start: Coords,
    is_goal: Callable[[Coords, list[Coords]], bool],
    walls: set[Wall],
    width: int,
    height: int,
    directions: list[Direction] | None = None,
) -> list[Coords]:
    """
    Generic BFS for grid pathfinding using Coords and Wall objects.
    """
    queue = deque()
    queue.append((start, [start]))
    visited = set([start])
    if directions is None:
        directions = [d for d in Direction if d != Direction.WAIT]

    wall_positions = {wall.position for wall in walls}

    while queue:
        current_pos, path = queue.popleft()
        if is_goal(current_pos, path):
            return path
        for direction in directions:
            dx, dy = direction.value.x, direction.value.y
            neighbor = Coords(current_pos.x + dx, current_pos.y + dy)
            if (
                0 <= neighbor.x < width
                and 0 <= neighbor.y < height
                and neighbor not in wall_positions
                and neighbor not in visited
            ):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


def find_path(
    start: Coords,
    goal: Coords,
    walls: set[Wall],
    width: int,
    height: int,
) -> list[Coords]:
    path_tuples = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
    )
    return path_tuples

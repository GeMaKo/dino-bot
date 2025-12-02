import sys
from collections import deque
from typing import Callable

from src.schemas import Coords, Direction


def cluster_targets(targets, max_distance):
    clusters = []
    for target in targets:
        for cluster in clusters:
            if any(manhattan(target, c) <= max_distance for c in cluster):
                cluster.add(target)
                break
        else:
            clusters.append({target})
    return [
        Coords(
            sum(c.x for c in cluster) // len(cluster),
            sum(c.y for c in cluster) // len(cluster),
        )
        for cluster in clusters
    ]


def manhattan(a: Coords, b: Coords) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def bfs(
    start: Coords,
    is_goal: Callable[[Coords, list[Coords]], bool],
    forbidden: set[Coords],
    width: int,
    height: int,
    directions: list[Direction] | None = None,
    goal: Coords | None = None,  # Add goal for axis prioritization
) -> list[Coords]:
    """
    Generic BFS for grid pathfinding using Coords and Wall objects.
    Prioritizes movement along the axis with the greatest remaining distance to the goal.
    """
    queue = deque()
    queue.append((start, [start]))
    visited = set([start])
    if directions is None:
        directions = [d for d in Direction if d != Direction.WAIT]

    while queue:
        current_pos, path = queue.popleft()
        if is_goal(current_pos, path):
            return path

        # Prioritize directions based on greatest axis distance to goal
        if goal is not None:
            dx = abs(goal.x - current_pos.x)
            dy = abs(goal.y - current_pos.y)
            if dx > dy:
                prioritized = [d for d in directions if d.value.x != 0] + [
                    d for d in directions if d.value.y != 0
                ]
            elif dy > dx:
                prioritized = [d for d in directions if d.value.y != 0] + [
                    d for d in directions if d.value.x != 0
                ]
            else:
                prioritized = directions
        else:
            prioritized = directions

        for direction in prioritized:
            ddx, ddy = direction.value.x, direction.value.y
            neighbor = Coords(current_pos.x + ddx, current_pos.y + ddy)
            if (
                0 <= neighbor.x < width
                and 0 <= neighbor.y < height
                and neighbor not in forbidden
                and neighbor not in visited
            ):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


def find_path(
    start: Coords,
    goal: Coords,
    forbidden: set[Coords],
    width: int,
    height: int,
) -> list[Coords]:
    path_tuples = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        goal=goal,  # Pass goal for axis prioritization
    )
    return path_tuples


def cached_path_decorator(func):
    cache = {}

    def wrapper(start, goal, forbidden, width, height):
        # Normalize the key so (start, goal) is the same as (goal, start)
        normalized_key = tuple(sorted([start, goal])) + (
            frozenset(forbidden),
            width,
            height,
        )

        if normalized_key not in cache:
            # Compute the path and store it in the cache
            path = func(start, goal, forbidden, width, height)
            cache[normalized_key] = path
            if len(cache) % 200 == 0:
                print(f"[Pathfinding] Cache size: {len(cache)}", file=sys.stderr)

        return cache[normalized_key]

    return wrapper


# Apply the decorator to find_path
@cached_path_decorator
def cached_find_path(start, goal, forbidden, width, height):
    return find_path(start, goal, forbidden, width, height)

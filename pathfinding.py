from collections import deque


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """
    Compute the Manhattan distance between two points.

    Parameters
    ----------
    a : tuple of int
        First point as (x, y).
    b : tuple of int
        Second point as (x, y).

    Returns
    -------
    distance : int
        Manhattan distance between a and b.

    Examples
    --------
    >>> manhattan((0, 0), (2, 3))
    5
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    walls: set[tuple[int, int]],
    width: int,
    height: int,
) -> list[tuple[int, int]]:
    """
    Find the shortest path from start to goal on a grid, avoiding walls, using Breadth-First Search (BFS).

    This function explores the grid in all four cardinal directions (up, down, left, right),
    expanding outward from the start position. It avoids positions listed in `walls` and does not revisit any position.
    The search guarantees the shortest path in terms of number of steps, if one exists. If no path is found, returns an empty list.

    Parameters
    ----------
    start : tuple of int
        The starting position as (x, y).
    goal : tuple of int
        The goal position as (x, y).
    walls : set of tuple of int
        Set of blocked positions (x, y) that cannot be traversed.
    width : int
        Width of the grid.
    height : int
        Height of the grid.

    Returns
    -------
    path : list of tuple of int
        List of positions from start to goal (inclusive). Empty if no path exists.

    Examples
    --------
    >>> find_path((0, 0), (2, 2), {(1, 1)}, 3, 3)
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
    """
    queue = deque()
    queue.append((start, [start]))
    visited = set([start])

    directions: list[tuple[int, int]] = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ]  # left, right, up, down

    while queue:
        current_pos, path = queue.popleft()
        if current_pos == goal:
            return path

        for dx, dy in directions:
            neighbor = (current_pos[0] + dx, current_pos[1] + dy)
            x, y = neighbor
            # Check bounds and obstacles
            if (
                0 <= x < width
                and 0 <= y < height
                and neighbor not in walls
                and neighbor not in visited
            ):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []

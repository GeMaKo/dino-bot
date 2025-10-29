from collections import deque
from typing import Callable

from config import Direction


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


def bfs(
    start: tuple[int, int],
    is_goal: Callable[[tuple[int, int], list[tuple[int, int]]], bool],
    walls: set[tuple[int, int]],
    width: int,
    height: int,
    directions: list | None = None,
) -> list[tuple[int, int]]:
    """
    Generic BFS for grid pathfinding.

    Parameters
    ----------
    start : tuple[int, int]
        Starting position.
    is_goal : callable
        Function taking (pos, path) and returning True if goal is reached.
    walls : set[tuple[int, int]]
        Blocked positions.
    width : int
        Grid width.
    height : int
        Grid height.
    directions : list, optional
        List of movement directions.

    Returns
    -------
    path : list[tuple[int, int]]
        Path from start to goal, or empty list if not found.
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
        for direction in directions:
            dx, dy = direction.value
            neighbor = (current_pos[0] + dx, current_pos[1] + dy)
            x, y = neighbor
            if (
                0 <= x < width
                and 0 <= y < height
                and neighbor not in walls
                and neighbor not in visited
            ):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


def find_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    walls: set[tuple[int, int]],
    width: int,
    height: int,
) -> list[tuple[int, int]]:
    """
    Find the shortest path from start to goal on a grid using BFS.

    This function computes the shortest path between two points on a grid, avoiding blocked positions (walls).
    It uses Breadth-First Search (BFS) to guarantee the shortest path in an unweighted grid.

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
        The shortest path from start to goal as a list of positions [(x0, y0), ..., (xn, yn)].
        Returns an empty list if no path exists.

    Examples
    --------
    >>> find_path((0, 0), (2, 2), set(), 3, 3)
    [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
    >>> find_path((0, 0), (1, 1), {(1, 0)}, 2, 2)
    [(0, 0), (0, 1), (1, 1)]
    """
    return bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
    )

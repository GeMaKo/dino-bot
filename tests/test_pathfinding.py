from pathfinding import find_path
from pathfinding import bfs
from config import Direction


def test_simple_path():
    start = (0, 0)
    goal = (2, 0)
    walls = set()
    width, height = 3, 1
    path = find_path(start, goal, walls, width, height)
    assert path == [(0, 0), (1, 0), (2, 0)]


def test_with_walls():
    start = (0, 0)
    goal = (2, 0)
    walls = {(1, 0)}
    width, height = 3, 1
    path = find_path(start, goal, walls, width, height)
    assert path == []


def test_grid_path():
    start = (0, 0)
    goal = (2, 2)
    walls = {(1, 1)}
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    # Should avoid (1,1)
    assert (1, 1) not in path
    assert path[0] == start
    assert path[-1] == goal


def test_start_is_goal():
    start = (1, 1)
    goal = (1, 1)
    walls = set()
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    assert path == [(1, 1)]


def test_unreachable_goal():
    start = (0, 0)
    goal = (2, 2)
    walls = {(1, 0), (0, 1), (1, 2), (2, 1)}
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    assert path == []


def test_bfs_simple_path():
    directions = [Direction.RIGHT]
    start = (0, 0)
    goal = (2, 0)
    walls = set()
    width, height = 3, 1
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
        directions=directions,
    )
    assert path == [(0, 0), (1, 0), (2, 0)]


def test_bfs_with_walls():
    directions = [Direction.RIGHT]
    start = (0, 0)
    goal = (2, 0)
    walls = {(1, 0)}
    width, height = 3, 1
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
        directions=directions,
    )
    assert path == []


def test_bfs_grid_path():
    directions = [
        Direction.RIGHT,
        Direction.DOWN,
        Direction.LEFT,
        Direction.UP,
    ]
    start = (0, 0)
    goal = (2, 2)
    walls = {(1, 1)}
    width, height = 3, 3
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
        directions=directions,
    )
    assert (1, 1) not in path
    assert path[0] == start
    assert path[-1] == goal


def test_bfs_start_is_goal():
    directions = [
        Direction.RIGHT,
        Direction.DOWN,
        Direction.LEFT,
        Direction.UP,
    ]
    start = (1, 1)
    goal = (1, 1)
    walls = set()
    width, height = 3, 3
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
        directions=directions,
    )
    assert path == [(1, 1)]


def test_bfs_unreachable_goal():
    directions = [
        Direction.RIGHT,
        Direction.DOWN,
        Direction.LEFT,
        Direction.UP,
    ]
    start = (0, 0)
    goal = (2, 2)
    walls = {(1, 0), (0, 1), (1, 2), (2, 1)}
    width, height = 3, 3
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        walls=walls,
        width=width,
        height=height,
        directions=directions,
    )
    assert path == []

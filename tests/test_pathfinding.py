from src.pathfinding import bfs, find_path, manhattan
from src.schemas import Coords, Direction


def test_manhattan_distance():
    a = Coords(0, 0)
    b = Coords(3, 4)
    assert manhattan(a, b) == 7
    assert manhattan(b, a) == 7
    assert manhattan(a, a) == 0
    assert manhattan(Coords(-1, -1), Coords(1, 1)) == 4


def test_bfs_finds_path():
    start = Coords(0, 0)
    goal = Coords(2, 0)
    walls = set()
    width, height = 3, 1
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=walls,
        width=width,
        height=height,
        directions=[Direction.RIGHT],
    )
    assert path == [Coords(0, 0), Coords(1, 0), Coords(2, 0)]


def test_bfs_with_wall():
    start = Coords(0, 0)
    goal = Coords(2, 0)
    walls = {Coords(1, 0)}
    width, height = 3, 1
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=walls,
        width=width,
        height=height,
        directions=[Direction.RIGHT],
    )
    assert path == []


def test_find_path_grid():
    start = Coords(0, 0)
    goal = Coords(2, 2)
    walls = {Coords(1, 1)}
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    assert path[0] == start
    assert path[-1] == goal
    assert Coords(1, 1) not in path


def test_find_path_start_is_goal():
    start = Coords(1, 1)
    goal = Coords(1, 1)
    walls = set()
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    assert path == [Coords(1, 1)]


def test_find_path_unreachable():
    start = Coords(0, 0)
    goal = Coords(2, 2)
    walls = {
        Coords(1, 0),
        Coords(0, 1),
        Coords(1, 2),
        Coords(2, 1),
    }
    width, height = 3, 3
    path = find_path(start, goal, walls, width, height)
    assert path == []

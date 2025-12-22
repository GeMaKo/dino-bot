from src.pathfinding import astar, bfs
from src.schemas import Coords, Direction


def test_bfs_forbidden_cells():
    start = Coords(0, 0)
    goal = Coords(2, 0)
    width, height = 3, 1
    forbidden = {Coords(1, 0)}
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        directions=[Direction.RIGHT],
        goal=goal,
    )
    assert path == []


def test_bfs_unreachable_goal():
    start = Coords(0, 0)
    goal = Coords(1, 1)
    width, height = 2, 2
    forbidden = {Coords(0, 1), Coords(1, 0)}
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        goal=goal,
    )
    assert path == []


def test_bfs_start_equals_goal():
    start = Coords(2, 2)
    goal = Coords(2, 2)
    width, height = 5, 5
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=set(),
        width=width,
        height=height,
        goal=goal,
    )
    assert path == [Coords(2, 2)]


def test_bfs_empty_grid():
    start = Coords(0, 0)
    goal = Coords(0, 0)
    width, height = 1, 1
    path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=set(),
        width=width,
        height=height,
        goal=goal,
    )
    assert path == [Coords(0, 0)]


def dfs(start, is_goal, forbidden, width, height, directions, goal=None):
    stack = [(start, [start])]
    visited = set([start])
    while stack:
        current_pos, path = stack.pop()
        if is_goal(current_pos, path):
            return path
        for direction in directions:
            ddx, ddy = direction.value.x, direction.value.y
            neighbor = Coords(current_pos.x + ddx, current_pos.y + ddy)
            if (
                0 <= neighbor.x < width
                and 0 <= neighbor.y < height
                and neighbor not in forbidden
                and neighbor not in visited
            ):
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    return []


def test_bfs_performance_comparison():
    import time

    start = Coords(0, 0)
    goal = Coords(49, 49)
    width, height = 50, 50
    forbidden = set()
    directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]

    t0 = time.time()
    bfs_path = bfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        directions=directions,
        goal=goal,
    )
    t1 = time.time()
    bfs_time = t1 - t0

    t2 = time.time()
    dfs_path = dfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        directions=directions,
        goal=goal,
    )
    t3 = time.time()
    dfs_time = t3 - t2

    # BFS should find the shortest path and be faster or at least not slower than DFS
    assert len(bfs_path) == 99  # 49 right + 49 down + start
    assert len(dfs_path) >= len(bfs_path)
    assert bfs_time <= dfs_time * 2  # Allow some margin for timing noise


def test_astar_performance_comparison():
    import time

    start = Coords(0, 0)
    goal = Coords(49, 49)
    width, height = 50, 50
    forbidden = set()
    directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]

    t0 = time.time()
    bfs_path = astar(
        start,
        forbidden=forbidden,
        width=width,
        height=height,
        directions=directions,
        goal=goal,
    )
    t1 = time.time()
    bfs_time = t1 - t0

    t2 = time.time()
    dfs_path = dfs(
        start,
        is_goal=lambda pos, path: pos == goal,
        forbidden=forbidden,
        width=width,
        height=height,
        directions=directions,
        goal=goal,
    )
    t3 = time.time()
    dfs_time = t3 - t2

    # BFS should find the shortest path and be faster or at least not slower than DFS
    assert len(bfs_path) == 99  # 49 right + 49 down + start
    assert len(dfs_path) >= len(bfs_path)
    assert bfs_time <= dfs_time * 2  # Allow some margin for timing noise

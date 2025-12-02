from typing import Generator

from src.schemas import Coords


def compute_fov(grid: list[list[bool]], position: Coords, radius: int) -> set[Coords]:
    """
    Compute the field of view (FOV) for a bot at a given position with a given radius.

    Args:
        grid: 2D list of cells, where True = wall, False = open.
        position: Coords object representing the bot's position.
        radius: Visibility radius.

    Returns:
        A set of Coords objects representing visible tiles.
    """
    visible = set()
    height = len(grid)
    width = len(grid[0])

    def is_blocking(coord: Coords) -> bool:
        """Check if a coordinate is blocking visibility."""
        return (
            not (0 <= coord.x < width and 0 <= coord.y < height)
            or grid[coord.y][coord.x]
        )

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            target = Coords(position.x + dx, position.y + dy)
            if (
                0 <= target.x < width
                and 0 <= target.y < height
                and dx * dx + dy * dy <= radius * radius
            ):
                # Use Bresenham's line algorithm to check visibility
                blocked = False
                for step in bresenham_line(position, target):
                    if is_blocking(step):
                        blocked = True
                        break
                if not blocked:
                    visible.add(target)
    return visible


def bresenham_line(start: Coords, end: Coords) -> Generator[Coords, None, None]:
    """
    Yield cells on a line from start to end using Bresenham's line algorithm.

    Args:
        start: Coords object representing the starting position.
        end: Coords object representing the ending position.

    Returns:
        A generator of Coords objects representing the cells on the line.
    """
    dx = abs(end.x - start.x)
    dy = abs(end.y - start.y)
    x, y = start.x, start.y
    sx = 1 if start.x < end.x else -1
    sy = 1 if start.y < end.y else -1
    if dx > dy:
        err = dx / 2.0
        while x != end.x:
            yield Coords(x, y)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != end.y:
            yield Coords(x, y)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    yield Coords(x, y)

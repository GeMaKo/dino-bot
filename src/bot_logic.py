import itertools

from src.config import Coords, EnemyBot, Gem, Wall
from src.pathfinding import find_path, manhattan


def get_bot2gems_distances(
    bot_pos: Coords,
    gems: list[Gem],
) -> list[Gem]:
    """
    Compute Manhattan distances from the bot to each gem.

    """
    for gem in gems:
        distance = manhattan(bot_pos, gem.position)
        gem.distance2bot = distance
    return gems


def get_enemy2gems_distances(
    enemy_pos: Coords,
    gems: list[Gem],
) -> list[Gem]:
    """
    Compute Manhattan distances from an enemy to each gem.
    """
    for gem in gems:
        distance = manhattan(enemy_pos, gem.position)
        gem.distance2enemies.append(distance)
    return gems


def analyze_enemies(enemies: list[EnemyBot], gems: list[Gem]) -> list[Gem]:
    for enemy in enemies:
        gems = get_enemy2gems_distances(enemy.position, gems)
    return gems


def check_reachable_gems(gems: list[Gem]) -> list[Gem]:
    for gem in gems:
        if gem.distance2bot is not None:
            gem.reachable = gem.distance2bot < gem.ttl + 1
    return gems


def get_distances(
    bot_pos: Coords,
    enemies: list[EnemyBot],
    gems: list[Gem],
) -> list[Gem]:
    """
    Compute distances from the bot and enemies to each gem.

    """
    gems = get_bot2gems_distances(bot_pos, gems)
    gems = analyze_enemies(enemies, gems)
    return gems


def get_path_to_closest_reachable_gem(
    bot_pos: Coords,
    gems: list[Gem],
    walls: set[Wall],
    width: int,
    height: int,
) -> list[Coords] | None:
    """
    Find the shortest path to the closest gem by Manhattan distance.

    Filters the visible gems to the three closest (using Manhattan distance), then computes the shortest path to each using BFS. Returns the shortest valid path found, or None if no path exists.

    """
    gems_sorted = sorted(gems, key=lambda gem: manhattan(bot_pos, gem.position))
    gem_to_check = gems_sorted[0]
    shortest_path = None
    forbidden = set(walls_pos.position for walls_pos in walls)
    path = find_path(bot_pos, gem_to_check.position, forbidden, width, height)
    if path and (shortest_path is None or len(path) < len(shortest_path)):
        shortest_path = path
    return shortest_path


def get_best_gem_collection_path(
    bot_pos: Coords,
    gems: list[Gem],
    walls: set[Wall],
    width: int,
    height: int,
    enemies: list[EnemyBot],
    initiative: bool,
    distance_matrix=None,
    path_segments=None,
) -> list[Coords] | None:
    if not gems:
        return None

    # Compute forbidden positions for each step
    def get_forbidden(step: int) -> set[Coords]:
        forbidden = set(walls_pos.position for walls_pos in walls)
        for enemy in enemies:
            # Current position
            forbidden.add(enemy.position)
            # If initiative, add possible next positions
            if not initiative:
                # Example: add all adjacent positions (customize as needed)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    next_pos = Coords(enemy.position.x + dx, enemy.position.y + dy)
                    if 0 <= next_pos.x < width and 0 <= next_pos.y < height:
                        forbidden.add(next_pos)
        return forbidden

    # Use passed-in caches if available, otherwise compute
    if distance_matrix is not None and path_segments is not None:
        path_lengths = distance_matrix
        path_segs = path_segments
    else:
        positions = [bot_pos] + [gem.position for gem in gems]
        path_lengths = {}
        path_segs = {}
        for i, src in enumerate(positions):
            for j, dst in enumerate(positions):
                if i != j:
                    seg = find_path(src, dst, get_forbidden(0), width, height)
                    path_segs[(src, dst)] = seg
                    path_lengths[(src, dst)] = len(seg) if seg else float("inf")

    best_path = None
    max_total_remaining_ttl = -float("inf")

    for perm in itertools.permutations(gems):
        path = []
        current_pos = bot_pos
        valid = True
        steps = 0
        total_remaining_ttl = 0
        for gem in perm:
            seg = path_segments.get((current_pos, gem.position), [])  # type: ignore
            seg_len = path_lengths.get((current_pos, gem.position), float("inf"))
            if seg_len == float("inf"):
                valid = False
                break
            if path:
                seg = seg[1:]
            path += seg
            steps += seg_len
            remaining_ttl = gem.ttl - steps
            if remaining_ttl < 0:
                valid = False
                break
            total_remaining_ttl += remaining_ttl
            current_pos = gem.position
        if valid and total_remaining_ttl > max_total_remaining_ttl:
            max_total_remaining_ttl = total_remaining_ttl
            best_path = path

    return best_path

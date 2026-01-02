import itertools
from functools import lru_cache

from src.pathfinding import cached_find_path, manhattan
from src.schemas import Coords, EnemyBot, Gem, ViewPoint, Wall


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


def get_bot_enemy_2_gem_distances(
    bot_pos: Coords,
    enemies: list[EnemyBot],
    gem: Gem,
) -> Gem:
    """
    Compute distances from the bot and enemies to a single gem.
    """
    distance = manhattan(bot_pos, gem.position)
    gem.distance2bot = distance
    for enemy in enemies:
        enemy_distance = manhattan(enemy.position, gem.position)
        gem.distance2enemies.append(enemy_distance)
    return gem


def analyze_enemies(enemies: list[EnemyBot], gems: list[Gem]) -> list[Gem]:
    for enemy in enemies:
        gems = get_enemy2gems_distances(enemy.position, gems)
    return gems


def check_reachable_gem(
    bot_pos: Coords,
    gem: Gem,
    walls: set[Coords],
    width: int,
    height: int,
) -> bool:
    gem_path = cached_find_path(
        start=bot_pos,
        goal=gem.position,
        forbidden=walls,
        width=width,
        height=height,
    )
    if len(gem_path) > 0 and len(gem_path) - 1 <= gem.ttl:
        reachable = True
    else:
        reachable = False
    return reachable


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


def find_viewpoints(
    graph: dict[Coords, set[Coords]],
    visibility_map: dict[Coords, ViewPoint],
    dead_ends: set[Coords],
) -> set[Coords]:
    """
    Find viewpoints that are as far away as possible from dead ends while maximizing visibility.
    Args:
        graph (dict): The adjacency list representation of the graph.
        visibility_map (dict): Precomputed visibility map for each floor tile.
        dead_ends (set): A set of dead end coordinates.
    Returns:
        set: A set of viewpoints (Coords).
    """
    viewpoints = set()

    for dead_end in dead_ends:
        # Filter viewpoints that can see the dead end
        visible_viewpoints = {
            vp
            for vp in visibility_map.keys()
            if dead_end in visibility_map.get(vp, ViewPoint(position=vp)).visible_tiles
        }

        if visible_viewpoints:
            # Find the viewpoint that maximizes visibility of the dead end and its surroundings
            best_viewpoint = max(
                visible_viewpoints,
                key=lambda vp: (
                    len(
                        visibility_map.get(vp, ViewPoint(position=vp)).visible_tiles
                    ),  # Total visibility
                    manhattan(dead_end, vp),  # Distance from the dead end
                ),
            )
            viewpoints.add(best_viewpoint)

    return viewpoints


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
                    seg = cached_find_path(src, dst, get_forbidden(0), width, height)
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


@lru_cache(maxsize=None)
def get_adjacents(pos: Coords) -> set[Coords]:
    """Return adjacent coordinates within bounds."""
    return {
        Coords(pos.x + dx, pos.y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
    }


@lru_cache(maxsize=None)
def get_diagonal_adjacents(pos: Coords) -> set[Coords]:
    """Return diagonal adjacent coordinates within bounds."""
    return {
        Coords(pos.x + dx, pos.y + dy)
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    }


@lru_cache(maxsize=None)
def _cached_get_adjacent_floors(
    pos: Coords,
    known_floors: frozenset[Coords],
    width: int,
    height: int,
) -> set[Coords]:
    """Cached version of get_adjacent_floors."""
    adjacents = get_adjacents(pos, width, height)
    return {adj for adj in adjacents if adj in known_floors}


def get_adjacent_floors(
    pos: Coords,
    known_floors: set[Coords],
    width: int,
    height: int,
) -> set[Coords]:
    """Wrapper for get_adjacent_floors with caching."""
    return _cached_get_adjacent_floors(pos, frozenset(known_floors), width, height)

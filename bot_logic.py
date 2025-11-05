from config import Coords, EnemyBot, Gem, Wall
from pathfinding import find_path, manhattan


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
        if gem.distance2enemies and gem.distance2bot is not None:
            min_enemy_dist = min(gem.distance2enemies)
            gem.reachable = gem.reachable and (
                gem.distance2bot < min_enemy_dist
            )  # TODO: check if enemy can reach the gem
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
    path = find_path(bot_pos, gem_to_check.position, walls, width, height)
    if path and (shortest_path is None or len(path) < len(shortest_path)):
        shortest_path = path
    return shortest_path

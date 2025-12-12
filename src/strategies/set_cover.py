import sys
from itertools import combinations
from typing import Callable

from src.debug import highlight_coords
from src.gamestate import GameState
from src.pathfinding import cached_find_path
from src.schemas import BehaviourState, Coords


def solve_set_cover_optimal(
    view_points: dict[Coords, set[Coords]], universe: set[Coords]
) -> set[Coords]:
    """
    Solve the set cover problem optimally using dynamic programming.
    """
    # Generate all subsets of the keys in view_points
    all_sets = list(view_points.keys())

    # Map to store the minimum set cover for each subset of the universe
    dp = {frozenset(): set()}  # Base case: empty universe requires no sets

    # Iterate over all subsets of the universe
    for subset_size in range(1, len(universe) + 1):
        for subset in combinations(universe, subset_size):
            subset = frozenset(subset)
            dp[subset] = None  # Initialize as unsolvable

            # Try to cover the subset using each set in view_points
            for s in all_sets:
                covered_by_s = view_points[s]
                remaining = subset - covered_by_s

                if remaining in dp and dp[remaining] is not None:
                    candidate = dp[remaining] | {s}
                    if dp[subset] is None or len(candidate) < len(dp[subset]):
                        dp[subset] = candidate

    # Return the solution for the full universe
    return dp[frozenset(universe)] if frozenset(universe) in dp else set()


def solve_set_cover(
    view_points: dict[Coords, set[Coords]], universe: set[Coords]
) -> set[Coords]:
    """Solve the set cover problem using a greedy algorithm."""
    covery_sets = view_points.copy()
    covered = set()
    selected_sets = set()

    while covered != universe:
        best_set = None
        best_coverage = 0

        for s, elements in covery_sets.items():
            coverage = len(elements - covered)
            if coverage > best_coverage:
                best_coverage = coverage
                best_set = s

        if best_set is None:
            break  # No more sets can cover new elements

        selected_sets.add(best_set)
        covered.update(covery_sets[best_set])
        del covery_sets[best_set]

    if covered == universe:
        return selected_sets
    else:
        return set()


def solve_weighted_set_cover(
    view_points: dict[Coords, set[Coords]],
    universe: set[Coords],
    start: Coords,
    distance_function: Callable,
    distance_kwargs: dict,
) -> set[Coords]:
    """
    Solve the set cover problem using a weighted greedy algorithm that also
    minimizes the distance between selected points.
    """
    covery_sets = view_points.copy()
    covered = set()
    selected_sets = set()
    last_selected = start

    while covered != universe:
        best_set = None
        best_score = -float("inf")

        for s, elements in covery_sets.items():
            coverage = len(elements - covered)
            if coverage == 0:
                continue
            distance = len(distance_function(last_selected, s, **distance_kwargs))
            score = coverage / (1 + distance)
            if score > best_score:
                best_score = score
                best_set = s

        if best_set is None:
            break

        selected_sets.add(best_set)
        covered.update(covery_sets[best_set])
        del covery_sets[best_set]
        last_selected = best_set

    if covered == universe:
        return selected_sets
    else:
        return set()


def order_patrol_points(
    start: Coords,
    patrol_points: set[Coords],
    forbidden: set[Coords],
    width: int,
    height: int,
    patrol_points_visited: set[Coords],
    visited_penalty: int = 100,
) -> list[Coords]:
    if patrol_points_visited is None:
        patrol_points_visited = set()
    route = []
    points = set(patrol_points)
    current = start
    while points:
        next_point = min(
            points,
            key=lambda p: (
                len(cached_find_path(current, p, forbidden, width, height))
                + (visited_penalty if p in patrol_points_visited else 0)
            ),
        )
        route.append(next_point)
        points.remove(next_point)
        current = next_point
    return route


def set_cover_patrol(game_state: GameState, strategy: str = "anderes") -> list[Coords]:
    if not game_state.patrol_points or game_state.tick % 300 == 0:
        print("Recomputing patrol points using set cover.", file=sys.stderr)
        if strategy == "optimal":
            game_state.patrol_points = solve_set_cover_optimal(
                game_state.visibility_map, set(game_state.known_floors.keys())
            )
        else:
            game_state.patrol_points = solve_weighted_set_cover(
                game_state.visibility_map,
                set(game_state.known_floors.keys()),
                game_state.bot,
                cached_find_path,
                {
                    "forbidden": game_state.known_wall_positions,
                    "width": game_state.config.width,
                    "height": game_state.config.height,
                },
            )
    # Find the closest patrol point to the bot
    if game_state.behaviour_state != BehaviourState.PATROLLING:
        print("Switching to PATROLLING behaviour.", file=sys.stderr)
        game_state.behaviour_state = BehaviourState.PATROLLING
        closest = min(
            game_state.patrol_points,
            key=lambda p: len(
                cached_find_path(
                    game_state.bot,
                    p,
                    game_state.known_wall_positions,
                    game_state.config.width,
                    game_state.config.height,
                )
            ),
        )
        # Order patrol points starting from the closest
        ordered_route = order_patrol_points(
            closest,
            game_state.patrol_points,
            game_state.known_wall_positions,
            game_state.config.width,
            game_state.config.height,
            set(game_state.patrol_points_visited),
        )
        game_state.patrol_route = ordered_route
        # Set patrol_index to the closest point
        game_state.patrol_index = 0

    target = game_state.patrol_route[game_state.patrol_index]
    highlight_coords.extend(game_state.patrol_route)

    # Advance patrol_index when bot arrives at the target
    if game_state.bot == target:
        game_state.patrol_index = (game_state.patrol_index + 1) % len(
            game_state.patrol_route
        )
        game_state.patrol_points_visited.append(target)
        target = game_state.patrol_route[game_state.patrol_index]
    return [target]

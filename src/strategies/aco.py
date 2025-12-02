import random
import sys
from typing import Callable

from src.pathfinding import cluster_targets
from src.schemas import Coords


def calculate_probabilities(current, unvisited, alpha, beta, pheromones, distances):
    probabilities = []
    for next_node in unvisited:
        pheromone = pheromones[(current, next_node)]
        distance = distances[(current, next_node)]
        heuristic = 1 / distance if distance > 0 else 0
        probabilities.append((next_node, (pheromone**alpha) * (heuristic**beta)))
    total = sum(p[1] for p in probabilities)
    if total == 0:  # Avoid division by zero
        return [
            (p[0], 1 / len(probabilities)) for p in probabilities
        ]  # Equal probabilities
    return [(p[0], p[1] / total) for p in probabilities]


def ant_colony_optimization(
    start: Coords,
    targets: set[Coords],
    walls: set[Coords],
    width: int,
    height: int,
    distance_function: Callable[[Coords, Coords, set[Coords], int, int], list[Coords]],
    num_ants: int = 10,
    num_iterations: int = 100,
    alpha: float = 1.0,  # Pheromone importance
    beta: float = 2.0,  # Heuristic importance
    evaporation_rate: float = 0.5,
    pheromone_boost: float = 1.0,
) -> list[Coords]:
    """
    Solve the patrol or collection path problem using Ant Colony Optimization (ACO).
    """
    print("Starting Ant Colony Optimization...", file=sys.stderr)
    # Initialize pheromones for all edges
    clustered_targets = cluster_targets(targets, max_distance=4)
    print(
        f"Clustering results in {len(clustered_targets)} targets from {len(targets)} original targets.",
        file=sys.stderr,
    )
    nodes = [start] + clustered_targets
    pheromones = {(src, dst): 1.0 for src in nodes for dst in nodes if src != dst}

    # Precompute distances between all nodes
    distances = {}
    for src in nodes:
        for dst in nodes:
            if src != dst:
                path = distance_function(src, dst, walls, width, height)
                if path is None:
                    distances[(src, dst)] = float("inf")
                else:
                    distances[(src, dst)] = len(path)

    # Helper function to calculate probabilities for the next move

    # Main ACO loop
    best_path = []
    best_cost = float("inf")

    for _ in range(num_iterations):
        all_paths = []
        all_costs = []

        # Simulate ants
        for _ in range(num_ants):
            path = [start]
            unvisited = set(clustered_targets)
            current = start
            cost = 0

            while unvisited:
                probabilities = calculate_probabilities(
                    current, unvisited, alpha, beta, pheromones, distances
                )
                next_node = random.choices(
                    [p[0] for p in probabilities],
                    weights=[p[1] for p in probabilities],
                )[0]
                path.append(next_node)
                cost += distances[(current, next_node)]
                current = next_node
                unvisited.remove(next_node)

            # Return to the start to complete the cycle
            cost += distances[(current, start)]
            path.append(start)

            all_paths.append(path)
            all_costs.append(cost)

            # Update best path
            if cost < best_cost:
                best_path = path
                best_cost = cost

        # Update pheromones
        for edge in pheromones:
            pheromones[edge] *= 1 - evaporation_rate  # Evaporate pheromones

        for path, cost in zip(all_paths, all_costs):
            for i in range(len(path) - 1):
                pheromones[(path[i], path[i + 1])] += pheromone_boost / cost
    if not best_path:
        print("No valid path found. Staying in place.", file=sys.stderr)
        return [start]  # Stay in place or return a default path
    return best_path

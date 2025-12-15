from src.schemas import Coords


def find_articulation_points(graph: dict[Coords, set[Coords]]) -> set[Coords]:
    """
    Find articulation points (critical nodes) in the graph.
    Args:
        graph (dict): The adjacency list representation of the graph.
    Returns:
        set: A set of articulation points (Coords).
    """

    def dfs(node, parent, time):
        nonlocal timer
        visited.add(node)
        discovery[node] = low[node] = timer
        timer += 1
        children = 0

        for neighbor in graph[node]:
            if neighbor == parent:
                continue
            if neighbor not in visited:
                children += 1
                dfs(neighbor, node, time)
                # Update low-link value
                low[node] = min(low[node], low[neighbor])
                # Check if the node is an articulation point
                if parent is not None and low[neighbor] >= discovery[node]:
                    articulation_points.add(node)
            else:
                # Update low-link value for back edges
                low[node] = min(low[node], discovery[neighbor])

        # Special case for root
        if parent is None and children > 1:
            articulation_points.add(node)

    visited = set()
    discovery = {}
    low = {}
    articulation_points = set()
    timer = 0

    for node in graph:
        if node not in visited:
            dfs(node, None, timer)

    return articulation_points


def find_bridges(graph: dict[Coords, set[Coords]]) -> set[tuple[Coords, Coords]]:
    """
    Find bridges (critical edges) in the graph.
    Args:
        graph (dict): The adjacency list representation of the graph.
    Returns:
        list: A list of bridges, where each bridge is a tuple (Coords, Coords).
    """

    def dfs(node, parent, time):
        nonlocal timer
        visited.add(node)
        discovery[node] = low[node] = timer
        timer += 1

        for neighbor in graph[node]:
            if neighbor == parent:
                continue
            if neighbor not in visited:
                dfs(neighbor, node, time)
                # Update low-link value
                low[node] = min(low[node], low[neighbor])
                # Check if the edge is a bridge
                if low[neighbor] > discovery[node]:
                    bridges.append((node, neighbor))
            else:
                # Update low-link value for back edges
                low[node] = min(low[node], discovery[neighbor])

    visited = set()
    discovery = {}
    low = {}
    bridges = []
    timer = 0

    for node in graph:
        if node not in visited:
            dfs(node, None, timer)
    return set(bridges)


def find_dead_ends_and_rooms(graph: dict[Coords, set[Coords]]) -> set[Coords]:
    """
    Identify dead ends, including rooms, in the floor graph.
    A dead end is a region of tiles with only one entry point.
    """
    visited = set()
    dead_ends = set()

    def dfs(node):
        stack = [node]
        component = set()
        entry_points = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)

            # Check neighbors
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)
                else:
                    # If the neighbor is outside the component, it's an entry point
                    if neighbor not in component:
                        entry_points.add(neighbor)

        return component, entry_points

    for start in graph:
        if start not in visited:
            component, entry_points = dfs(start)

            # If the component has only one entry point, it's a dead end or room
            if len(entry_points) <= 1:
                # Only mark nodes with exactly one neighbor as dead ends
                dead_ends.update(node for node in component if len(graph[node]) == 1)

    return dead_ends

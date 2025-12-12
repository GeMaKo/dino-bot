import sys
from collections import deque
from dataclasses import dataclass, field
from functools import cached_property

from src.bot_logic import (
    check_reachable_gem,
    get_adjacents,
    get_bot_enemy_2_gem_distances,
    get_diagonal_adjacents,
)
from src.debug import highlight_coords
from src.graph import find_articulation_points, find_bridges, find_dead_ends_and_rooms
from src.pathfinding import cached_find_path, manhattan
from src.schemas import BehaviourState, Coords, EnemyBot, Floor, GameConfig, Gem, Wall
from src.visibility import compute_fov


@dataclass
class GameState:
    tick: int
    bot: Coords
    wall: set[Wall]
    floor: set[Floor]
    initiative: bool
    visible_gems: list[Gem]
    visible_bots: list[EnemyBot]
    known_gems: dict[Coords, Gem] = field(default_factory=dict)
    known_walls: dict[Coords, Wall] = field(default_factory=dict)
    known_floors: dict[Coords, Floor] = field(default_factory=dict)
    distance_matrix: dict = field(default_factory=dict)
    path_segments: dict = field(default_factory=dict)
    last_gem_positions: set[Coords] = field(default_factory=set)
    last_bot_pos: Coords | None = None
    config: GameConfig | None = field(default=None)
    current_strategy: str = field(default="")
    debug_mode: bool = field(default=True)
    recent_positions: list[Coords] = field(default_factory=list)
    bot_adjacent_positions: set[Coords] = field(default_factory=set)
    bot_diagonal_positions: set[Coords] = field(default_factory=set)
    hidden_positions: set[Coords] = field(default_factory=set)
    cave_revealed: bool = field(default=False)
    explore_target: Coords | None = field(default=None)
    visibility_map: dict[Coords, set[Coords]] = field(default_factory=dict)
    highlight_sink: list[Coords] | None = None
    patrol_route: list[Coords] = field(default_factory=list)
    patrol_points: set[Coords] = field(default_factory=set)
    patrol_index: int = field(default=0)
    behaviour_state: BehaviourState = field(default=BehaviourState.IDLE)
    patrol_points_visited: deque[Coords] = field(
        default_factory=lambda: deque(maxlen=2)
    )
    exploration_points_visited: list[Coords] = field(default_factory=list)
    current_patrol_path: list[Coords] | None = field(default_factory=list)
    floor_graph: dict[Coords, set[Coords]] = field(default_factory=dict)
    graph_articulation_points: set[Coords] = field(default_factory=set)
    graph_bridges: set[tuple[Coords, Coords]] = field(default_factory=set)
    visibility_grid: list[list[bool]] = field(default_factory=list)
    dead_ends: set[Coords] = field(default_factory=set)

    def __post_init__(self):
        if self.config is not None:
            self.hidden_positions = self._init_hidden_positions()
        self.highlight_sink = highlight_coords

    def _init_hidden_positions(self):
        assert self.config is not None, (
            "GameConfig must be set to initialize hidden positions"
        )
        self.update_known_walls()
        self.update_known_floors()
        # Initialize all positions as hidden except known floors/walls
        hidden = []
        for x in range(self.config.width):
            for y in range(self.config.height):
                pos = Coords(x, y)
                if (
                    pos not in self.known_wall_positions
                    and pos not in self.known_floor_positions
                ):
                    hidden.append(pos)
        return set(hidden)

    @cached_property
    def center(self) -> Coords:
        assert self.config is not None, "GameConfig must be set to get center"
        return Coords(self.config.width // 2, self.config.height // 2)

    @property
    def known_wall_positions(self) -> set[Coords]:
        return set(self.known_walls.keys())

    @property
    def known_floor_positions(self) -> set[Coords]:
        return set(self.known_floors.keys())

    @property
    def visible_floor_positions(self) -> set[Coords]:
        return set(floor.position for floor in self.floor)

    @property
    def gem_positions(self) -> set[Coords]:
        return set(self.known_gems.keys())

    def generate_visibility_grid(self):
        """
        Generate a 2D grid representing the visibility map.
        """
        assert self.config is not None, (
            "GameConfig must be set to generate visibility grid"
        )
        self.visibility_grid = [
            [False for _ in range(self.config.width)] for _ in range(self.config.height)
        ]
        for wall in self.known_wall_positions:
            self.visibility_grid[wall.y][wall.x] = True

    def refresh_visibility_map(self):
        self.visibility_map[self.bot] = {f.position for f in self.floor}

    def update_patrol_points(self):
        """
        Select the best patrol points based on dead ends and visibility.
        """
        assert self.dead_ends, (
            "Dead ends must be defined before updating patrol points."
        )
        assert self.visibility_map, (
            "Visibility map must be defined before updating patrol points."
        )

        best_viewpoints = set()

        # Step 1: Select the best viewpoints for dead ends
        for dead_end in self.dead_ends:
            # Filter viewpoints that can see the dead end
            visible_viewpoints = {
                vp
                for vp in self.visibility_map.keys()
                if dead_end in self.visibility_map.get(vp, set())
            }

            if visible_viewpoints:
                # Find the viewpoint that maximizes visibility of the dead end and its surroundings
                best_viewpoint = max(
                    visible_viewpoints,
                    key=lambda vp: (
                        len(self.visibility_map.get(vp, set())),  # Total visibility
                        manhattan(dead_end, vp),  # Distance from the dead end
                    ),
                )
                best_viewpoints.add(best_viewpoint)

        # Step 2: Ensure all known floors are covered without overriding dead end-focused points
        uncovered_floors = self.known_floor_positions.copy()
        for vp in best_viewpoints:
            uncovered_floors -= self.visibility_map.get(vp, set())

        while uncovered_floors:
            # Find the viewpoint that covers the most uncovered floors, but avoid overriding dead end-focused points
            best_additional_viewpoint = max(
                self.visibility_map.keys() - best_viewpoints,
                key=lambda vp: len(
                    self.visibility_map.get(vp, set()) & uncovered_floors
                ),
            )
            best_viewpoints.add(best_additional_viewpoint)
            uncovered_floors -= self.visibility_map.get(
                best_additional_viewpoint, set()
            )

        # Update patrol points and highlight them
        self.patrol_points = best_viewpoints
        highlight_coords.extend(self.patrol_points)

    def update_known_gems(self):
        assert self.config is not None, "GameConfig must be set to update known gems"
        # Decrease TTL for all known gems
        for pos, gem in list(self.known_gems.items()):
            self.known_gems[pos].ttl -= 1
            if self.known_gems[pos].ttl <= 0:
                del self.known_gems[pos]
        # Update with currently visible gems (resetting TTL if seen again)
        self.known_gems.update({gem.position: gem for gem in self.visible_gems})
        for gem in self.known_gems.values():
            gem.reachable = check_reachable_gem(
                self.bot,
                gem,
                self.known_wall_positions,
                self.config.width,
                self.config.height,
            )
        self.known_gems.pop(self.bot, None)

    def update_floor_graph(self):
        """
        Incrementally update the floor graph when new floors are added or removed.
        """
        for floor in self.known_floor_positions:
            # Add the new floor as a node
            self.floor_graph[floor] = set()
            # Connect to existing neighbors
            for neighbor in get_adjacents(floor):
                if neighbor in self.floor_graph:
                    self.floor_graph[floor].add(neighbor)
                    self.floor_graph[neighbor].add(floor)

    def update_bottleneck_info(self):
        self.graph_articulation_points = find_articulation_points(self.floor_graph)
        self.graph_bridges = find_bridges(self.floor_graph)
        if self.debug_mode:
            highlight_coords.extend(self.graph_articulation_points)

    def update_known_walls(self):
        for wall in self.wall:
            self.known_walls[wall.position] = wall

    def update_known_floors(self):
        for floor in self.floor:
            self.known_floors[floor.position] = floor

    def update_hidden_positions(self):
        self.hidden_positions -= self.known_floor_positions | self.known_wall_positions

    def update_bot_adjacent_positions(self):
        self.bot_adjacent_positions = get_adjacents(self.bot)

    def update_bot_diagonal_adjacent_positions(self):
        self.bot_diagonal_positions = get_diagonal_adjacents(self.bot)

    def update_recent_positions(self, limit: int):
        self.recent_positions.append(self.bot)
        if len(self.recent_positions) > limit:
            self.recent_positions.pop(0)

    def update_dead_ends_and_rooms(self):
        self.dead_ends = find_dead_ends_and_rooms(self.floor_graph)
        highlight_coords.extend(self.dead_ends)

    def precompute_visibility_map(self):
        """
        TOO EXPENSIVE
        Precompute visibility for all known floor tiles.
        """
        assert self.config is not None, (
            "GameConfig must be set to precompute visibility map"
        )
        for floor in self.known_floor_positions:
            if floor not in self.visibility_map:
                self.visibility_map[floor] = compute_fov(
                    self.visibility_grid, floor, self.config.vis_radius
                )

    def recalculate_gem_distances(self):
        for pos, gem in list(self.known_gems.items()):
            self.known_gems[pos] = get_bot_enemy_2_gem_distances(
                self.bot, self.visible_bots, gem
            )

    def recalculate_distance_matrix(self):
        assert self.config is not None, (
            "GameConfig must be set to update distance matrix"
        )
        bot_pos = self.bot
        gem_positions = self.gem_positions
        # Only recalculate changed paths
        if self.last_gem_positions != gem_positions:
            if self.debug_mode:
                print(
                    "[GameState] Updating changed gem positions in distance matrix and path segments",
                    file=sys.stderr,
                )
            # Remove paths for gems that disappeared
            removed_gems = (
                self.last_gem_positions - gem_positions
                if self.last_gem_positions
                else set()
            )
            for gem_pos in removed_gems:
                keys_to_remove = [
                    k for k in self.distance_matrix.keys() if gem_pos in k
                ]
                for k in keys_to_remove:
                    self.distance_matrix.pop(k, None)
                    self.path_segments.pop(k, None)
            # Add/update paths for new gems
            new_gems = (
                gem_positions - self.last_gem_positions
                if self.last_gem_positions
                else gem_positions
            )
            all_positions = [bot_pos] + list(new_gems)
            for src in all_positions:
                for dst in all_positions:
                    if src != dst:
                        seg = cached_find_path(
                            src,
                            dst,
                            self.known_wall_positions,
                            self.config.width,
                            self.config.height,
                        )
                        self.path_segments[(src, dst)] = seg
                        self.distance_matrix[(src, dst)] = (
                            len(seg) if seg else float("inf")
                        )
            self.last_gem_positions = set(gem_positions)
            self.last_bot_pos = bot_pos
        elif self.last_gem_positions and self.last_bot_pos != bot_pos:
            if self.debug_mode:
                print("[GameState] Updating bot-to-gem distances", file=sys.stderr)
            for gem_pos in gem_positions:
                seg = cached_find_path(
                    bot_pos,
                    gem_pos,
                    self.known_wall_positions,
                    self.config.width,
                    self.config.height,
                )
                self.path_segments[(bot_pos, gem_pos)] = seg
                self.distance_matrix[(bot_pos, gem_pos)] = (
                    len(seg) if seg else float("inf")
                )
            self.last_bot_pos = bot_pos

    @classmethod
    def from_dict(cls, data: dict, config: GameConfig) -> "GameState":
        required_keys = ["tick", "bot", "wall", "floor", "initiative", "visible_gems"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key in data: {key}")
        if not isinstance(data["bot"], (list, tuple)) or len(data["bot"]) != 2:
            raise ValueError("'bot' must be a list or tuple of length 2")
        bot = Coords(x=data["bot"][0], y=data["bot"][1])
        wall = {Wall(position=Coords(x=w[0], y=w[1])) for w in data["wall"]}
        floor = {
            Floor(position=Coords(x=f[0], y=f[1]), last_seen=data["tick"])
            for f in data["floor"]
        }
        visible_gems = []
        for g in data["visible_gems"]:
            if "position" not in g or "ttl" not in g:
                raise ValueError("Each gem must have 'position' and 'ttl'")
            if not isinstance(g["position"], (list, tuple)) or len(g["position"]) != 2:
                raise ValueError("Gem 'position' must be a list or tuple of length 2")
            visible_gems.append(
                Gem(
                    position=Coords(x=g["position"][0], y=g["position"][1]),
                    ttl=g["ttl"],
                    distance2bot=g.get("distance2bot"),
                    distance2enemies=g.get("distance2enemies", []),
                    reachable=g.get("reachable", False),
                )
            )
        visible_bots = [
            EnemyBot(position=Coords(x=b["position"][0], y=b["position"][1]))
            for b in data.get("visible_bots", [])
            if "position" in b
            and isinstance(b["position"], (list, tuple))
            and len(b["position"]) == 2
        ]

        return cls(
            tick=data["tick"],
            bot=bot,
            wall=wall,
            floor=floor,
            initiative=data["initiative"],
            visible_gems=visible_gems,
            visible_bots=visible_bots,
            config=config,
        )

    def update_from_dict(self, data: dict):
        required_keys = ["tick", "bot", "wall", "floor", "initiative", "visible_gems"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key in data: {key}")
        if not isinstance(data["bot"], (list, tuple)) or len(data["bot"]) != 2:
            raise ValueError("'bot' must be a list or tuple of length 2")
        self.tick = data["tick"]
        self.bot = Coords(x=data["bot"][0], y=data["bot"][1])
        self.wall = {Wall(position=Coords(x=w[0], y=w[1])) for w in data["wall"]}
        self.floor = {
            Floor(position=Coords(x=f[0], y=f[1]), last_seen=self.tick)
            for f in data["floor"]
        }
        self.initiative = data["initiative"]
        self.visible_gems = []
        for g in data["visible_gems"]:
            if "position" not in g or "ttl" not in g:
                raise ValueError("Each gem must have 'position' and 'ttl'")
            if not isinstance(g["position"], (list, tuple)) or len(g["position"]) != 2:
                raise ValueError("Gem 'position' must be a list or tuple of length 2")
            self.visible_gems.append(
                Gem(
                    position=Coords(x=g["position"][0], y=g["position"][1]),
                    ttl=g["ttl"],
                    distance2bot=g.get("distance2bot"),
                    distance2enemies=g.get("distance2enemies", []),
                    reachable=g.get("reachable", False),
                )
            )
        self.visible_bots = [
            EnemyBot(position=Coords(x=b["position"][0], y=b["position"][1]))
            for b in data.get("visible_bots", [])
            if "position" in b
            and isinstance(b["position"], (list, tuple))
            and len(b["position"]) == 2
        ]

    def refresh(self):
        self.update_dead_ends_and_rooms()

        if self.behaviour_state == BehaviourState.EXPLORING:
            self.update_known_walls()
            self.update_hidden_positions()
            self.update_floor_graph()
            # self.generate_visibility_grid()
            # self.update_bottleneck_info()
            # self.precompute_visibility_map()
        if self.behaviour_state == BehaviourState.PATROLLING:
            self.update_patrol_points()
        self.refresh_visibility_map()
        self.update_known_floors()
        self.update_dead_ends_and_rooms()
        self.update_known_gems()
        self.recalculate_gem_distances()
        # self.recalculate_distance_matrix()
        self.update_bot_adjacent_positions()
        self.update_bot_diagonal_adjacent_positions()

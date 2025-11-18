import sys
from dataclasses import dataclass, field
from functools import cached_property

from src.bot_logic import (
    check_reachable_gem,
    get_bot_enemy_2_gem_distances,
)
from src.pathfinding import find_path
from src.schemas import Coords, EnemyBot, Floor, GameConfig, Gem, Wall


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
    debug_mode: bool = field(default=False)
    recent_positions: list[Coords] = field(default_factory=list)
    bot_adjacent_positions: set[Coords] = field(default_factory=set)
    bot_diagonal_positions: set[Coords] = field(default_factory=set)
    hidden_positions: set[Coords] = field(default_factory=set)
    cave_revealed: bool = field(default=False)
    explore_target: Coords | None = field(default=None)

    def __post_init__(self):
        if self.config is not None:
            self.hidden_positions = self._init_hidden_positions()

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
                if pos not in self.wall_positions and pos not in self.floor_positions:
                    hidden.append(pos)
        return set(hidden)

    @cached_property
    def center(self) -> Coords:
        assert self.config is not None, "GameConfig must be set to get center"
        return Coords(self.config.width // 2, self.config.height // 2)

    @property
    def wall_positions(self) -> set[Coords]:
        return set(self.known_walls.keys())

    @property
    def floor_positions(self) -> set[Coords]:
        return set(self.known_floors.keys())

    @property
    def gem_positions(self) -> set[Coords]:
        return set(self.known_gems.keys())

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
                self.wall_positions,
                self.config.width,
                self.config.height,
            )
        self.known_gems.pop(self.bot, None)

    def update_known_walls(self):
        for wall in self.wall:
            self.known_walls[wall.position] = wall

    def update_known_floors(self):
        for floor in self.floor:
            self.known_floors[floor.position] = floor

    def update_hidden_positions(self):
        self.hidden_positions -= self.floor_positions | self.wall_positions

    def update_bot_adjacent_positions(self):
        self.bot_adjacent_positions = {
            Coords(self.bot.x + dx, self.bot.y + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        }

    def update_bot_diagonal_adjacent_positions(self):
        self.bot_diagonal_positions = {
            Coords(self.bot.x + dx, self.bot.y + dy)
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        }

    def update_recent_positions(self, limit: int):
        self.recent_positions.append(self.bot)
        if len(self.recent_positions) > limit:
            self.recent_positions.pop(0)

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
                        seg = find_path(
                            src,
                            dst,
                            self.wall_positions,
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
                seg = find_path(
                    bot_pos,
                    gem_pos,
                    self.wall_positions,
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
        self.update_known_floors()
        self.update_known_walls()
        self.update_known_gems()
        self.update_hidden_positions()
        self.recalculate_gem_distances()
        self.recalculate_distance_matrix()
        self.update_bot_adjacent_positions()
        self.update_bot_diagonal_adjacent_positions()

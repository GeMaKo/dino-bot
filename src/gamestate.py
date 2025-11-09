import sys
from dataclasses import dataclass, field
from functools import cached_property

from src.bot_logic import (
    check_reachable_gems,
    get_distances,
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
    distance_matrix: dict = field(default_factory=dict)
    path_segments: dict = field(default_factory=dict)
    last_gem_positions: set[Coords] = field(default_factory=set)
    last_bot_pos: Coords | None = None
    config: GameConfig | None = field(default=None)

    @cached_property
    def wall_positions(self) -> set[Coords]:
        return {w.position for w in self.wall}

    @cached_property
    def floor_positions(self) -> set[Coords]:
        return {f.position for f in self.floor}

    def update_gem_distances(self):
        self.visible_gems = get_distances(
            self.bot,
            self.visible_bots,
            self.visible_gems,
        )
        self.visible_gems = check_reachable_gems(self.visible_gems)

    def update_distance_matrix(self):
        assert self.config is not None, (
            "GameConfig must be set to update distance matrix"
        )
        gem_positions = set(gem.position for gem in self.visible_gems if gem.reachable)
        bot_pos = self.bot
        if self.last_gem_positions != gem_positions:
            print("Updating full distance matrix and path segments", file=sys.stderr)
            self.distance_matrix = {}
            self.path_segments = {}
            all_positions = [bot_pos] + list(gem_positions)
            for i, src in enumerate(all_positions):
                for j, dst in enumerate(all_positions):
                    if i != j:
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
            print("Updating bot-to-gem distances", file=sys.stderr)
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
        bot = Coords(x=data["bot"][0], y=data["bot"][1])
        wall = {Wall(position=Coords(x=w[0], y=w[1])) for w in data["wall"]}
        floor = {Floor(position=Coords(x=f[0], y=f[1])) for f in data["floor"]}
        visible_gems = [
            Gem(
                position=Coords(x=g["position"][0], y=g["position"][1]),
                ttl=g["ttl"],
                distance2bot=g.get("distance2bot"),
                distance2enemies=g.get("distance2enemies", []),
                reachable=g.get("reachable", False),
            )
            for g in data["visible_gems"]
        ]
        visible_bots = [
            EnemyBot(position=Coords(x=b["position"][0], y=b["position"][1]))
            for b in data.get("visible_bots", [])
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
        self.tick = data["tick"]
        self.bot = Coords(x=data["bot"][0], y=data["bot"][1])
        self.wall = {Wall(position=Coords(x=w[0], y=w[1])) for w in data["wall"]}
        self.floor = {Floor(position=Coords(x=f[0], y=f[1])) for f in data["floor"]}
        self.initiative = data["initiative"]
        self.visible_gems = [
            Gem(
                position=Coords(x=g["position"][0], y=g["position"][1]),
                ttl=g["ttl"],
                distance2bot=g.get("distance2bot"),
                distance2enemies=g.get("distance2enemies", []),
                reachable=g.get("reachable", False),
            )
            for g in data["visible_gems"]
        ]
        self.visible_bots = [
            EnemyBot(position=Coords(x=b["position"][0], y=b["position"][1]))
            for b in data.get("visible_bots", [])
        ]

    def refresh(self):
        self.update_gem_distances()
        self.update_distance_matrix()

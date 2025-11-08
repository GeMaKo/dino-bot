import sys
from dataclasses import dataclass, field
from functools import cached_property

from bot_logic import (
    check_reachable_gems,
    get_distances,
)
from config import Coords, EnemyBot, Floor, Gem, Wall
from pathfinding import find_path


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

    def update_distance_matrix(self, config):
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
                            config.width,
                            config.height,
                        )
                        self.path_segments[(src, dst)] = seg
                        self.distance_matrix[(src, dst)] = (
                            len(seg) if seg else float("inf")
                        )
            self.last_gem_positions = set(gem_positions)
            self.last_bot_pos = bot_pos
        elif self.last_bot_pos != bot_pos:
            print("Updating bot-to-gem distances", file=sys.stderr)
            for gem_pos in gem_positions:
                seg = find_path(
                    bot_pos,
                    gem_pos,
                    self.wall_positions,
                    config.width,
                    config.height,
                )
                self.path_segments[(bot_pos, gem_pos)] = seg
                self.distance_matrix[(bot_pos, gem_pos)] = (
                    len(seg) if seg else float("inf")
                )
            self.last_bot_pos = bot_pos

from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

RECENT_POSITIONS_LIMIT = 5
DISTANCE_TO_ENEMY = 3
RANDOM_MOVES = 5

_STR_MAP = {
    "LEFT": "W",
    "RIGHT": "E",
    "UP": "N",
    "DOWN": "S",
    "WAIT": "WAIT",
}


class Phase(Enum):
    SEARCH_GEMS = 0
    COLLECT_GEMS = 1


@dataclass(frozen=True)
class Coords:
    x: int
    y: int


class Direction(Enum):
    LEFT = Coords(-1, 0)
    RIGHT = Coords(1, 0)
    UP = Coords(0, -1)
    DOWN = Coords(0, 1)
    WAIT = Coords(0, 0)

    @staticmethod
    @lru_cache(maxsize=None)
    def from_delta(coords: Coords) -> "Direction":
        for direction in Direction:
            if coords == direction.value:
                return direction
        return Direction.WAIT

    @classmethod
    def to_str(cls, direction: "Direction") -> str:
        return _STR_MAP[direction.name]


@dataclass
class GameConfig:
    stage_key: str
    width: int
    height: int
    generator: str
    max_ticks: int
    emit_signals: bool
    vis_radius: int
    max_gems: int
    gem_spawn_rate: float
    gem_ttl: int
    signal_radius: float
    signal_cutoff: float
    signal_noise: float
    signal_quantization: int
    signal_fade: int
    bot_seed: int


@dataclass
class Gem:
    position: Coords
    ttl: int
    distance2bot: int | None = None
    distance2enemies: list[int] = field(default_factory=list)
    reachable: bool = False


@dataclass
class EnemyBot:
    position: Coords


@dataclass(frozen=True)
class Wall:
    position: Coords


@dataclass(frozen=True)
class Floor:
    position: Coords


@dataclass
class GameState:
    tick: int
    bot: Coords
    wall: set[Wall]
    floor: set[Floor]
    initiative: bool
    visible_gems: list[Gem]
    visible_bots: list[EnemyBot]

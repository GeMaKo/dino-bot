from dataclasses import dataclass, field, fields
from enum import Enum
from functools import lru_cache

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


class BehaviourState(Enum):
    IDLE = 0
    EXPLORING = 1
    PATROLLING = 2
    COLLECTING_GEM = 3
    UNSTUCKING = 4


@dataclass(frozen=True)
class Coords:
    x: int
    y: int

    def __eq__(self, other):
        return isinstance(other, Coords) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __lt__(self, other):
        if not isinstance(other, Coords):
            return NotImplemented
        return (self.x, self.y) < (other.x, other.y)


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
    enable_debug: bool = False

    @classmethod
    def from_dict(cls, d: dict):
        allowed = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in allowed}
        return cls(**filtered)


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
    last_seen: int

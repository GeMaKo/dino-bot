from enum import Enum
from functools import lru_cache

_STR_MAP = {
    "LEFT": "W",
    "RIGHT": "E",
    "UP": "N",
    "DOWN": "S",
    "WAIT": "WAIT",
}


class Direction(Enum):
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP = (0, -1)
    DOWN = (0, 1)
    WAIT = (0, 0)

    @staticmethod
    @lru_cache(maxsize=None)
    def from_delta(dx: int, dy: int) -> "Direction":
        for direction in Direction:
            if (dx, dy) == direction.value:
                return direction
        return Direction.WAIT

    @classmethod
    def to_str(cls, direction: "Direction") -> str:
        return _STR_MAP[direction.name]

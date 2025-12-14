from dataclasses import dataclass

from src.schemas import Coords


@dataclass
class HighlightCoords:
    name: str
    coords: list[Coords]
    color: str


highlight_coords: list[HighlightCoords] = []

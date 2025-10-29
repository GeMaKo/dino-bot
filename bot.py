#!/usr/bin/env python3
import sys
import json
from pathfinding import find_path, manhattan
from config import Direction


class CollectorBot:
    """
    CollectorBot implements a bot for collecting gems on a grid map.

    The bot uses BFS pathfinding to navigate towards the closest gems, avoiding walls. Configuration is set on the first tick.

    Attributes
    ----------
    width : int
        Width of the map (set on first tick).
    height : int
        Height of the map (set on first tick).
    walls : set of tuple of int
        Set of blocked positions (x, y) that cannot be traversed (set on first tick).

    Examples
    --------
    >>> bot = CollectorBot()
    >>> bot.width, bot.height, bot.walls = 5, 5, set()
    """

    def __init__(self):
        """
        Initialize CollectorBot with uninitialized map configuration.

        Attributes are set on the first tick via process_input.

        Returns
        -------
        None

        Examples
        --------
        >>> bot = CollectorBot()
        >>> bot.width, bot.height, bot.walls = 5, 5, set()
        """
        self.width: int | None = None
        self.height: int | None = None
        self.walls: set[tuple[int, int]] | None = None

    def get_path_to_closest_top3_gem(
        self, bot_pos: tuple[int, int], gems: list[dict]
    ) -> list[tuple[int, int]] | None:
        """
        Find the shortest path to one of the top 3 closest gems by Manhattan distance.

        Filters the visible gems to the three closest (using Manhattan distance), then computes the shortest path to each using BFS. Returns the shortest valid path found, or None if no path exists.

        Parameters
        ----------
        bot_pos : tuple of int
            The current position of the bot as (x, y).
        gems : list of dict
            List of gem objects, each with a 'position' key.

        Returns
        -------
        shortest_path : list of tuple of int or None
            The shortest path to a gem, as a list of positions. None if no path exists.

        Examples
        --------
        >>> bot = CollectorBot()
        >>> bot.width, bot.height, bot.walls = 5, 5, set()
        >>> gems = [{"position": [2, 2]}, {"position": [1, 1]}]
        >>> bot.get_path_to_closest_top3_gem((0, 0), gems)
        [(0, 0), (0, 1), (1, 1)]
        """
        # Pre-filter gems by Manhattan distance (top 3 closest)
        gems_sorted = sorted(
            gems, key=lambda gem: manhattan(bot_pos, tuple(gem["position"]))
        )
        gems_to_check = gems_sorted[:3]  # Only check top 3 closest gems
        shortest_path = None
        for gem in gems_to_check:
            gem_pos = tuple(gem["position"])
            if self.width is None or self.height is None or self.walls is None:
                raise ValueError(
                    "Map width, height, and walls must be initialized before pathfinding."
                )
            path = find_path(bot_pos, gem_pos, self.walls, self.width, self.height)
            if path and (shortest_path is None or len(path) < len(shortest_path)):
                shortest_path = path
        return shortest_path

    def navigate_to_gem(self, game_state: dict) -> tuple[int, int]:
        """
        Determine the next position for the bot to move towards the closest gem.

        Uses pathfinding to select the shortest path to one of the top 3 closest gems (by Manhattan distance).
        If no gems are visible, the bot stays in its current position.

        Parameters
        ----------
        game_state : dict
            The current game state containing bot position and visible gems.

        Returns
        -------
        next_pos : tuple of int
            The next position (x, y) for the bot to move to. If no gems, returns current position.

        Examples
        --------
        >>> bot = CollectorBot()
        >>> bot.width, bot.height, bot.walls = 5, 5, set()
        >>> bot.navigate_to_gem({"bot": [0, 0], "visible_gems": [{"position": [2, 2]}]})
        (0, 1)
        """
        bot_pos = tuple(game_state["bot"])
        gems = game_state.get("visible_gems", [])
        if not gems:
            return bot_pos  # No gems to move to
        shortest_path = self.get_path_to_closest_top3_gem(bot_pos, gems)
        if shortest_path and len(shortest_path) > 1:
            next_pos = shortest_path[1]  # Next step
            return next_pos
        return bot_pos

    def process_input(self, line: str, first_tick: bool = False) -> str:
        """
        Process a single line of input and determine the next move.

        Parses the input line (JSON), updates configuration on the first tick, and computes the next move using pathfinding.

        Parameters
        ----------
        line : str
            A JSON-encoded string representing the current game state.
        first_tick : bool, default=False
            Whether this is the first tick (used to initialize map configuration).

        Returns
        -------
        move : str
            The direction to move ('N', 'S', 'E', 'W', or 'WAIT').

        Examples
        --------
        >>> bot = CollectorBot()
        >>> bot.process_input('{"bot": [0, 0], "visible_gems": [], "config": {"width": 5, "height": 5}, "wall": []}', first_tick=True)
        'WAIT'
        """
        data = json.loads(line)
        config = data.get("config", {})
        if first_tick:
            self.width = config.get("width")
            self.height = config.get("height")
            self.walls = set(tuple(w) for w in data.get("wall", []))
            print(
                f"Collector bot (Python) launching on a {self.width}x{self.height} map",
                file=sys.stderr,
            )
        # Use pathfinding to determine next move
        bot_pos = tuple(data.get("bot"))
        next_pos = self.navigate_to_gem(data)
        # Map position delta to direction
        dx = next_pos[0] - bot_pos[0]
        dy = next_pos[1] - bot_pos[1]
        # Find the matching Direction enum for the delta
        move_direction = Direction.from_delta(dx, dy)
        move = Direction.to_str(move_direction)
        return move

    def run(self):
        """
        Run the main bot loop, reading input from stdin and printing moves.

        Reads each line from standard input, processes the game state, and outputs the next move.
        The first tick initializes the map configuration.

        Returns
        -------
        None

        Examples
        --------
        >>> bot = CollectorBot()
        >>> bot.run()
        # Reads from stdin, prints moves to stdout
        """
        first_tick = True
        for line in sys.stdin:
            move = self.process_input(line, first_tick=first_tick)
            print(move, flush=True)
            first_tick = False


if __name__ == "__main__":
    bot = CollectorBot()
    bot.run()

#!/usr/bin/env python3
import json
import random
import sys
from typing import Optional

from bot_logic import (
    check_reachable_gems,
    get_distances,
    get_path_to_closest_reachable_gem,
)
from bot_utils import parse_gamestate
from config import (
    RANDOM_MOVES,
    RECENT_POSITIONS_LIMIT,
    Coords,
    Direction,
    GameConfig,
    GameState,
    Gem,
    Phase,
)
from pathfinding import bfs


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
        self.config: Optional[GameConfig] = None
        self.game_state: Optional[GameState] = None
        self.recent_positions: list[Coords] = []
        self.phase = Phase.MOVE_TO_CENTER
        self.random_moves_left = 0
        self.normal_search_directions = [
            Direction.LEFT,
            Direction.RIGHT,
            Direction.UP,
            Direction.DOWN,
        ]

    def navigate_to_gem(self, reachable_gems: list[Gem]) -> Coords:
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
        if self.config is None or self.game_state is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.config is not None
        assert self.game_state is not None
        shortest_path = get_path_to_closest_reachable_gem(
            self.game_state.bot,
            reachable_gems,
            self.game_state.wall,
            self.config.width,
            self.config.height,
        )
        if shortest_path and len(shortest_path) > 1:
            next_pos = shortest_path[1]  # Next step
            return next_pos
        return self.game_state.bot

    def search_gems(self) -> Coords:
        if self.config is None or self.game_state is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.config is not None
        assert self.game_state is not None

        # Calculate center of the map
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        center = Coords(center_x, center_y)

        if self.phase == Phase.MOVE_TO_CENTER:
            bot_pos = self.game_state.bot
            if bot_pos == center:
                self.phase = Phase.RANDOM_MOVEMENT
                self.random_moves_left = RANDOM_MOVES  # Number of random moves
            else:
                # Try moving along x axis first
                dx = center.x - bot_pos.x
                dy = center.y - bot_pos.y
                if dx != 0:
                    next_x = bot_pos.x + (1 if dx > 0 else -1)
                    next_pos = Coords(next_x, bot_pos.y)
                    if next_pos not in self.game_state.wall:
                        return next_pos
                if dy != 0:
                    next_y = bot_pos.y + (1 if dy > 0 else -1)
                    next_pos = Coords(bot_pos.x, next_y)
                    if next_pos not in self.game_state.wall:
                        return next_pos

        # Phase 2: Random moves
        if self.phase == Phase.RANDOM_MOVEMENT and self.random_moves_left > 0:
            directions = [Direction.LEFT, Direction.RIGHT, Direction.UP, Direction.DOWN]
            random.shuffle(directions)
            for direction in directions:
                dx, dy = direction.value.x, direction.value.y
                next_pos = Coords(
                    self.game_state.bot.x + dx, self.game_state.bot.y + dy
                )
                if next_pos not in self.game_state.wall:
                    self.random_moves_left -= 1
                    if self.random_moves_left == 0:
                        self.phase = Phase.NORMAL_SEARCH
                        # Shuffle left/right directions only once when entering NORMAL_SEARCH
                        lr = [Direction.LEFT, Direction.RIGHT]
                        random.shuffle(lr)
                        self.normal_search_directions = lr + [
                            Direction.UP,
                            Direction.DOWN,
                        ]
                    return next_pos
            # If all random moves blocked, fall back to normal search below

        # Phase 3: Normal search
        directions = self.normal_search_directions
        center = Coords(center_x, center_y)

        def direction_bias(direction):
            assert self.game_state is not None
            dx, dy = direction.value.x, direction.value.y
            new_pos = Coords(self.game_state.bot.x + dx, self.game_state.bot.y + dy)
            return abs(new_pos.x - center.x) + abs(new_pos.y - center.y)

        preferred_directions = sorted(directions, key=direction_bias)

        def is_goal(pos: Coords, path: list[Coords]) -> bool:
            assert self.game_state is not None
            return (
                pos != self.game_state.bot
                and pos not in self.game_state.wall
                and pos not in self.recent_positions
            )

        path = bfs(
            self.game_state.bot,
            is_goal=is_goal,
            walls=self.game_state.wall,
            width=self.config.width,
            height=self.config.height,
            directions=preferred_directions,
        )
        if path and len(path) > 1:
            return path[1]
        return self.game_state.bot

    def enrich_game_state(self) -> None:
        """
        Enrich the current game state with additional analysis.
        """
        assert self.game_state is not None
        # Compute distances from bot to gems
        self.game_state.visible_gems = get_distances(
            self.game_state.bot,
            self.game_state.visible_bots,
            self.game_state.visible_gems,
        )
        # Analyze gem positions
        self.game_state.visible_gems = check_reachable_gems(
            self.game_state.visible_gems
        )

    def process_game_state(self) -> str:
        """
        Process a single line of input and determine the next move.

        Parses the input line (JSON), updates configuration on the first tick, and computes the next move using pathfinding.

        Returns
        -------
        move : str
            The direction to move ('N', 'S', 'E', 'W', or 'WAIT').
        """
        if self.config is None or self.game_state is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.config is not None
        assert self.game_state is not None

        # Use pathfinding to determine next move
        # Update recent positions (keep last N, from config)
        self.recent_positions.append(self.game_state.bot)
        if len(self.recent_positions) > RECENT_POSITIONS_LIMIT:
            self.recent_positions.pop(0)
        self.enrich_game_state()

        # Check for search or navigate to gems
        reachable_gems = [gem for gem in self.game_state.visible_gems if gem.reachable]
        if not reachable_gems:
            next_pos = self.search_gems()
            print(f"Searching for gems {self.phase}...", file=sys.stderr)
        else:
            next_pos = self.navigate_to_gem(reachable_gems)
            print(f"Navigating to gem at {next_pos}", file=sys.stderr)
            if any(gem.position == next_pos for gem in self.game_state.visible_gems):
                self.phase = Phase.MOVE_TO_CENTER
                self.random_moves_left = 0
                self.recent_positions.clear()
                print(
                    "Will collect a gem, resetting to MOVE_TO_CENTER phase",
                    file=sys.stderr,
                )
        # Map position delta to direction
        dx = next_pos.x - self.game_state.bot.x
        dy = next_pos.y - self.game_state.bot.y
        # Find the matching Direction enum for the delta
        move_direction = Direction.from_delta(Coords(x=dx, y=dy))
        # print(
        #    f"Bot at {self.game_state.bot}, moving to {next_pos} via {move_direction}",
        #    file=sys.stderr,
        # )
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
            data = json.loads(line)
            if first_tick:
                self.config = GameConfig(**data.get("config"))
                random.seed(self.config.bot_seed)
                data.pop("config", None)
                print(
                    f"Collector bot (Python) launching on a {self.config.width}x{self.config.height} map",
                    file=sys.stderr,
                )
            self.game_state = parse_gamestate(data)
            move = self.process_game_state()
            print(move, flush=True)
            first_tick = False


if __name__ == "__main__":
    bot = CollectorBot()
    bot.run()

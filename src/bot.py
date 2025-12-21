import json
import random
import sys
from typing import Optional

from src.config import (
    RECENT_POSITIONS_LIMIT,
)
from src.debug import highlight_coords
from src.gamestate import GameState
from src.schemas import (
    Coords,
    Direction,
    GameConfig,
    Phase,
)
from src.strategy_register import STRATEGY_REGISTRY


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
    """

    def __init__(self, name: str, strategy: str, debug_mode: bool = False):
        """
        Initialize CollectorBot with uninitialized map configuration.

        Attributes are set on the first tick via process_input.

        """
        self.name = name
        strategy_cls = STRATEGY_REGISTRY.get(strategy)
        if strategy_cls is None:
            raise ValueError(f"Unknown strategy: {strategy}")
        self.strategy = strategy_cls() if callable(strategy_cls) else strategy_cls
        self.game_state: Optional[GameState] = None
        self.recent_positions: list[Coords] = []
        self.random_moves_left = 0
        self.normal_search_directions = [
            Direction.LEFT,
            Direction.RIGHT,
            Direction.UP,
            Direction.DOWN,
        ]
        self.bot_phase = Phase.SEARCH_GEMS
        self.debug_mode = debug_mode

    def process_game_state(self) -> tuple[str, list[Coords]]:
        """
        Process a single line of input and determine the next move.

        Parses the input line (JSON), updates configuration on the first tick, and computes the next move using pathfinding.

        Returns
        -------
        move : str
            The direction to move ('N', 'S', 'E', 'W', or 'WAIT').
        """
        if self.game_state is None or self.game_state.config is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.game_state is not None

        # Use the strategy to decide the next position
        next_pos, next_path = self.strategy.decide(self.game_state)

        # Use pathfinding to determine next move
        # Update recent positions (keep last N, from config)
        self.game_state.update_recent_positions(RECENT_POSITIONS_LIMIT)
        self.game_state.last_path = next_path

        # Map position delta to direction
        dx = next_pos.x - self.game_state.bot.x
        dy = next_pos.y - self.game_state.bot.y
        move_direction = Direction.from_delta(Coords(x=dx, y=dy))
        move = Direction.to_str(move_direction)
        return move, next_path

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
                config = GameConfig.from_dict(data.get("config"))
                random.seed(config.bot_seed)
                data.pop("config", None)
                print(
                    f"{self.name} (Python) launching on a {config.width}x{config.height} map",
                    file=sys.stderr,
                )
                # Initialize game_state with all fields
                self.game_state = GameState.from_dict(data, config)
                self.game_state.debug_mode = self.debug_mode
                first_tick = False
            # Save previous gem positions before overwriting game_state
            else:
                assert self.game_state is not None
                self.game_state.update_from_dict(data)
            assert self.game_state is not None
            self.game_state.refresh()

            move, next_path = self.process_game_state()
            highlight_next_path = [[w.x, w.y, "#00ff11"] for w in next_path]
            highlight = {
                "highlight": [
                    [w.x, w.y, "#2f00ff"] for w in self.game_state.known_wall_positions
                ]
                + highlight_next_path
                + [
                    [hc.x, hc.y, hc_group.color]
                    for hc_group in highlight_coords
                    for hc in hc_group.coords
                ]
            }
            highlight_coords.clear()
            self.game_state.exploration_points_visited.append(self.game_state.bot)
            print(
                f"{move} {json.dumps(highlight)}",
                flush=True,
            )
            self.game_state.last_bot_pos = self.game_state.bot

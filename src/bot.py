import json
import random
import sys
from typing import Optional

from src.bot_logic import (
    get_best_gem_collection_path,
)
from src.config import (
    DISTANCE_TO_ENEMY,
    RECENT_POSITIONS_LIMIT,
)
from src.gamestate import GameState
from src.pathfinding import bfs, manhattan
from src.schemas import (
    Coords,
    Direction,
    GameConfig,
    Gem,
    Phase,
)
from src.strategy import Strategy


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

    def __init__(self, name, strategy: Strategy | None = None):
        """
        Initialize CollectorBot with uninitialized map configuration.

        Attributes are set on the first tick via process_input.

        """
        self.name = name
        self.strategy = "CollectorBot"
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

    def navigate_to_gem(self, reachable_gems: list[Gem]) -> Coords:
        """
        Determine the next position for the bot to move towards the closest gem.

        Uses pathfinding to select the shortest path to one of the top 3 closest gems (by Manhattan distance).
        If no gems are visible, the bot stays in its current position.

        """
        if self.game_state is None or self.game_state.config is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.game_state is not None
        assert self.game_state.config is not None
        shortest_path = get_best_gem_collection_path(
            bot_pos=self.game_state.bot,
            gems=reachable_gems,
            walls=self.game_state.wall,
            width=self.game_state.config.width,
            height=self.game_state.config.height,
            distance_matrix=self.game_state.distance_matrix,
            path_segments=self.game_state.path_segments,
            initiative=self.game_state.initiative,
            enemies=self.game_state.visible_bots,
        )
        if shortest_path and len(shortest_path) > 1:
            next_pos = shortest_path[1]  # Next step
            return next_pos
        return self.game_state.bot

    def search_gems(self) -> Coords:
        if self.game_state is None or self.game_state.config is None:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        assert self.game_state.config is not None
        assert self.game_state is not None

        center = Coords(
            self.game_state.config.width // 2, self.game_state.config.height // 2
        )
        bot_pos = self.game_state.bot

        visible_enemies = [e for e in self.game_state.visible_bots if e != bot_pos]
        closest_enemy = min(
            visible_enemies,
            key=lambda e: manhattan(e.position, bot_pos),
            default=None,
        )

        directions = self.normal_search_directions

        def direction_bias(direction):
            dx, dy = direction.value.x, direction.value.y
            new_pos = Coords(bot_pos.x + dx, bot_pos.y + dy)
            center_dist = manhattan(new_pos, center)
            if closest_enemy:
                enemy_center_dist = manhattan(closest_enemy.position, center)
                bot_center_dist = manhattan(bot_pos, center)
                enemy_dist = manhattan(new_pos, closest_enemy.position)
                # If bot is at least DISTANCE_TO_ENEMY steps closer to center than enemy, move towards enemy
                if bot_center_dist <= enemy_center_dist - DISTANCE_TO_ENEMY:
                    return enemy_dist
                # Otherwise, move towards center
                if bot_center_dist >= enemy_center_dist:
                    return center_dist
                # Stay close to enemy (distance DISTANCE_TO_ENEMY), but keep center advantage
                if center_dist < enemy_center_dist:
                    return abs(enemy_dist - DISTANCE_TO_ENEMY) * 10 + center_dist
                return center_dist
            else:
                return center_dist

        preferred_directions = sorted(directions, key=direction_bias)

        def is_goal(pos: Coords, path: list[Coords]) -> bool:
            assert self.game_state is not None
            if pos == bot_pos:
                return False
            if pos in self.game_state.wall_positions or pos in self.recent_positions:
                return False
            enemy_on_pos = pos in self.game_state.visible_bots
            if enemy_on_pos and not self.game_state.initiative:
                return False

            if closest_enemy:
                enemy_center_dist = manhattan(closest_enemy.position, center)
                bot_center_dist = manhattan(bot_pos, center)
                pos_center_dist = manhattan(pos, center)
                enemy_dist = manhattan(pos, closest_enemy.position)

                # Phase 1: Move closer to center than enemy (or if enemy is at center, just get closer to center)
                if bot_center_dist >= enemy_center_dist:
                    if enemy_center_dist == 0:
                        return pos_center_dist < bot_center_dist
                    return (
                        pos_center_dist < enemy_center_dist
                        and pos_center_dist < bot_center_dist
                    )

                # Phase 2: Stay close to enemy (distance DISTANCE_TO_ENEMY), but keep center advantage
                return (
                    pos_center_dist < enemy_center_dist
                    and enemy_dist == DISTANCE_TO_ENEMY
                )

            # No enemy: just move closer to center
            return manhattan(pos, center) < manhattan(bot_pos, center)

        path = bfs(
            bot_pos,
            is_goal=is_goal,
            forbidden=self.game_state.wall_positions,
            width=self.game_state.config.width,
            height=self.game_state.config.height,
            directions=preferred_directions,
        )
        if path and len(path) > 1:
            return path[1]
        return bot_pos

    def process_game_state(self) -> str:
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
        assert self.game_state.config is not None

        # Use pathfinding to determine next move
        # Update recent positions (keep last N, from config)
        self.recent_positions.append(self.game_state.bot)
        if len(self.recent_positions) > RECENT_POSITIONS_LIMIT:
            self.recent_positions.pop(0)

        # Check for search or navigate to gems
        reachable_gems = [gem for gem in self.game_state.visible_gems if gem.reachable]
        if not reachable_gems:
            next_pos = self.search_gems()
            if self.bot_phase == Phase.COLLECT_GEMS:
                print("No reachable gems, switching to search mode", file=sys.stderr)
            self.bot_phase = Phase.SEARCH_GEMS
        else:
            next_pos = self.navigate_to_gem(reachable_gems)
            if self.bot_phase == Phase.SEARCH_GEMS:
                print("Navigating to gem", file=sys.stderr)
            self.bot_phase = Phase.COLLECT_GEMS

            if any(gem.position == next_pos for gem in self.game_state.visible_gems):
                self.recent_positions.clear()

        # Map position delta to direction
        dx = next_pos.x - self.game_state.bot.x
        dy = next_pos.y - self.game_state.bot.y
        # Find the matching Direction enum for the delta
        move_direction = Direction.from_delta(Coords(x=dx, y=dy))
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
                config = GameConfig(**data.get("config"))
                random.seed(config.bot_seed)
                data.pop("config", None)
                print(
                    f"{self.name} (Python) launching on a {config.width}x{config.height} map",
                    file=sys.stderr,
                )
                # Initialize game_state with all fields
                self.game_state = GameState.from_dict(data, config)
                first_tick = False
            # Save previous gem positions before overwriting game_state
            else:
                assert self.game_state is not None
                self.game_state.update_from_dict(data)
            assert self.game_state is not None
            self.game_state.refresh()

            move = self.process_game_state()
            print(move, flush=True)
            self.game_state.last_bot_pos = self.game_state.bot

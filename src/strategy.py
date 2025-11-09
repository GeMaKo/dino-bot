from abc import ABC, abstractmethod

from src.gamestate import GameState
from src.pathfinding import find_path
from src.schemas import Coords


class Strategy(ABC):
    name: str

    @abstractmethod
    def decide(self, game_state: GameState) -> Coords:
        pass


class GreedyStrategy(Strategy):
    name = "GreedyStrategy"

    def decide(self, game_state: GameState) -> Coords:
        assert game_state.visible_gems is not None
        visible_gems_with_distance = [
            gem.distance2bot
            for gem in game_state.visible_gems
            if gem.distance2bot is not None
        ]
        nearest_gem = min(visible_gems_with_distance)
        if nearest_gem:
            return self.navigate_to_gem(game_state.bot, nearest_gem, game_state)
        return game_state.bot  # Stay in place if no gems are visible

    def navigate_to_gem(self, bot_pos, gem_pos, gamestate) -> Coords:
        shortest_path = find_path(
            start=bot_pos,
            goal=gem_pos,
            forbidden=set(walls_pos.position for walls_pos in gamestate.walls),
            width=gamestate.width,
            height=gamestate.height,
        )
        return shortest_path[1] if len(shortest_path) > 1 else bot_pos


class ModularStrategy(Strategy):
    name = "ModularStrategy"

    def __init__(self, evaluator, planner, tie_breaker):
        self.evaluator = evaluator
        self.planner = planner
        self.tie_breaker = tie_breaker

    def decide(self, game_state) -> Coords:
        candidates = self.planner(game_state)
        scored_candidates = [
            (move, self.evaluator(game_state, move)) for move in candidates
        ]
        best = self.tie_breaker(scored_candidates)
        return best if best else game_state.bot


def simple_planner(game_state: GameState) -> list[Coords]:
    # Generate possible moves (to be implemented)
    possible_moves = []
    for direction in [Coords(1, 0), Coords(-1, 0), Coords(0, 1), Coords(0, -1)]:
        new_pos = Coords(
            game_state.bot.x + direction.x,
            game_state.bot.y + direction.y,
        )
        possible_moves.append(new_pos)
    return possible_moves

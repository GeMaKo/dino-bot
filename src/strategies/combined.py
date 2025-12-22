import sys

from src.gamestate import GameState
from src.schemas import BehaviourState, Coords
from src.strategies.schemas import LocalStrategy, Strategy


class GlobalCombinedStrategy(Strategy):
    def __init__(
        self,
        exploration_strategy: LocalStrategy,
        patrol_strategy: LocalStrategy,
        gem_collection_strategy: LocalStrategy,
        name: str = "GlobalCombinedStrategy",
    ):
        self.name = name
        self.strategies = {
            "exploration": exploration_strategy,
            "patrol": patrol_strategy,
            "gem_collection": gem_collection_strategy,
        }

    def decide_strategy(self, game_state: GameState) -> Strategy:
        """
        Decide which strategy to use based on the game state.
        """
        # Check for reachable gems first (even during exploration)
        reachable_gems = [
            gem for gem in game_state.known_gems.values() if gem.reachable
        ]
        if reachable_gems:
            game_state.behaviour_state = BehaviourState.COLLECTING_GEM
            return self.strategies["gem_collection"]

        # Exploration behavior
        if not game_state.cave_revealed:
            game_state.behaviour_state = BehaviourState.EXPLORING
            return self.strategies["exploration"]

        # Patrol behavior
        if game_state.behaviour_state == BehaviourState.PATROLLING:
            return self.strategies["patrol"]

        # Default to patrol if no other behavior is active
        game_state.behaviour_state = BehaviourState.PATROLLING
        return self.strategies["patrol"]

    def decide(self, game_state: GameState) -> tuple[Coords, list[Coords]]:
        """
        Decide the next move by delegating to the selected strategy.
        """
        strategy = self.decide_strategy(game_state)
        if strategy.name != game_state.current_strategy:
            print(
                f"[{self.name}] Switching strategy to: {strategy.name}", file=sys.stderr
            )
        if 30 > game_state.stuck_counter >= 3:
            print(
                f"[{self.name}] Bot seems stuck (stuck_counter={game_state.stuck_counter}). sticking to previous target {game_state.last_path[-1]}.",
                file=sys.stderr,
            )
            next_path = game_state.last_path
            if next_path is None:
                next_path = [game_state.bot]

            next_pos = next_path[next_path.index(game_state.bot) + 1]
            return next_pos, next_path
        elif game_state.stuck_counter >= 10:
            print(
                f"[{self.name}] Bot seems very stuck, probably enemy interference (stuck_counter={game_state.stuck_counter}). Forcing exploration.",
                file=sys.stderr,
            )
            game_state.bot_very_stuck = True
        else:
            game_state.bot_very_stuck = False
        game_state.current_strategy = strategy.name
        return strategy.decide(game_state)

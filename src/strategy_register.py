from src.strategies.evaluators import (
    advanced_search_evaluator,
    cave_explore_evaluator,
    greedy_blocking_evaluator,
    greedy_evaluator,
    simple_search_evaluator,
    tsm_evaluator,
)
from src.strategies.planners import (
    advanced_search_planner,
    cave_explore_planner,
    greedy_planner,
    simple_search_planner,
)
from src.strategies.schemas import (
    GlobalGreedyStrategy,
    LocalStrategy,
    Strategy,
    simple_tie_breaker,
)


def create_local_greedy_strategy() -> LocalStrategy:
    """Create and return a greedy strategy instance."""
    return LocalStrategy(
        name="Greedy Collection Strategy",
        evaluator=greedy_evaluator,
        planner=greedy_planner,
        tie_breaker=simple_tie_breaker,
    )


def create_greedy_blocking_strategy() -> LocalStrategy:
    """Create and return a greedy blocking strategy instance."""
    return LocalStrategy(
        name="Greedy Blocking Strategy",
        evaluator=greedy_blocking_evaluator,
        planner=greedy_planner,
        tie_breaker=simple_tie_breaker,
    )


def create_tsm_collection_strategy() -> LocalStrategy:
    """Create and return a TSM-based collection strategy instance."""
    return LocalStrategy(
        name="TSM Collection Strategy",
        evaluator=tsm_evaluator,
        planner=greedy_planner,
        tie_breaker=simple_tie_breaker,
    )


def create_simple_search_strategy() -> LocalStrategy:
    """Create and return a search strategy instance."""
    return LocalStrategy(
        name="Simple Search Strategy",
        evaluator=simple_search_evaluator,
        planner=simple_search_planner,
        tie_breaker=simple_tie_breaker,
    )


def create_advanced_search_strategy() -> LocalStrategy:
    """Create and return an advanced search strategy instance."""
    return LocalStrategy(
        name="Advanced Search Strategy",
        evaluator=advanced_search_evaluator,
        planner=advanced_search_planner,
        tie_breaker=simple_tie_breaker,
    )


def create_cave_explore_strategy() -> LocalStrategy:
    """Create and return a cave exploration strategy instance."""
    return LocalStrategy(
        name="Cave Explore Strategy",
        evaluator=cave_explore_evaluator,
        planner=cave_explore_planner,
        tie_breaker=simple_tie_breaker,
    )


STRATEGY_REGISTRY: dict[str, Strategy] = {
    "greedy": GlobalGreedyStrategy(
        create_local_greedy_strategy(),
        create_simple_search_strategy(),
        name="GreedyStrategy",
    ),
    "advanced_greedy": GlobalGreedyStrategy(
        create_local_greedy_strategy(),
        create_advanced_search_strategy(),
        name="AdvancedGreedyStrategy",
    ),
    "advanced_greedy_blocking": GlobalGreedyStrategy(
        create_greedy_blocking_strategy(),
        create_advanced_search_strategy(),
        name="AdvancedGreedyBlockingStrategy",
    ),
    "tsm_collection": GlobalGreedyStrategy(
        create_tsm_collection_strategy(),
        create_advanced_search_strategy(),
        name="TSMCollectionStrategy",
    ),
    "cave_explore_greedy": GlobalGreedyStrategy(
        create_greedy_blocking_strategy(),
        create_cave_explore_strategy(),
        name="CaveExploreGreedyStrategy",
    ),
}

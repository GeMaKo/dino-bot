from src.strategy import (
    GlobalGreedyStrategy,
    LocalStrategy,
    Strategy,
    advanced_search_evaluator,
    advanced_search_planner,
    advanced_search_tie_breaker,
    greedy_evaluator,
    greedy_planner,
    simple_search_evaluator,
    simple_search_planner,
    simple_tie_breaker,
)


def create_local_greedy_strategy() -> LocalStrategy:
    """Create and return a greedy strategy instance."""
    return LocalStrategy(
        name="Greedy Strategy",
        evaluator=greedy_evaluator,
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
        tie_breaker=advanced_search_tie_breaker,
    )


STRATEGY_REGISTRY: dict[str, Strategy] = {
    "greedy": GlobalGreedyStrategy(
        create_local_greedy_strategy(),
        create_simple_search_strategy(),
    ),
    "advanced_greedy": GlobalGreedyStrategy(
        create_local_greedy_strategy(),
        create_advanced_search_strategy(),
    ),
}

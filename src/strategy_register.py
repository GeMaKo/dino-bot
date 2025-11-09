from src.strategy import (
    ModularStrategy,
    greedy_evaluator,
    greedy_planner,
    greedy_tie_breaker,
)


def create_greedy_strategy():
    return ModularStrategy(
        name="Greedy Strategy",
        evaluator=greedy_evaluator,
        planner=greedy_planner,
        tie_breaker=greedy_tie_breaker,
    )


STRATEGY_REGISTRY = {
    "greedy": create_greedy_strategy,
}

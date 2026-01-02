from src.gamestate import Floor, GameConfig, GameState, Gem, Wall
from src.schemas import Coords
from src.strategy_register import (
    create_exploration_strategy,
    create_gem_collection_strategy,
)


def create_realistic_gamestate():
    """
    Create a realistic GameState for testing strategies.
    """
    config = GameConfig(
        width=10,
        height=10,
        vis_radius=5,
        stage_key="test_stage",
        generator="test_generator",
        max_ticks=100,
        emit_signals=True,
        max_gems=5,
        gem_spawn_rate=1.0,
        gem_ttl=10,
        signal_radius=3,
        signal_cutoff=0.1,
        signal_noise=0.0,
        signal_quantization=1,
        signal_fade=0,
        bot_seed=42,
    )
    walls = {Wall(position=Coords(x, y)) for x, y in [(1, 1), (2, 2), (3, 3)]}
    floors = {
        Floor(position=Coords(x, y), last_seen=0) for x in range(10) for y in range(10)
    }
    gems = [Gem(position=Coords(5, 5), ttl=10, reachable=True)]
    bot_position = Coords(0, 0)

    return GameState(
        tick=1,
        bot=bot_position,
        wall=walls,
        floor=floors,
        initiative=True,
        visible_gems=gems,
        visible_bots=[],
        config=config,
    )


def test_exploration_strategy_execution():
    gamestate = create_realistic_gamestate()
    gamestate.refresh()
    strategy = create_exploration_strategy()
    decision = strategy.decide(gamestate)
    assert decision is not None, "Decision for exploration strategy failed"


def test_gem_collection_strategy_execution():
    gamestate = create_realistic_gamestate()
    gamestate.refresh()
    strategy = create_gem_collection_strategy()
    decision = strategy.decide(gamestate)
    assert decision is not None, "Decision for exploration strategy failed"

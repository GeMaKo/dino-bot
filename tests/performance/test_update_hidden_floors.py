import timeit

from src.gamestate import GameState
from src.schemas import Coords, Floor, GameConfig


def setup_gamestate():
    # Create a dummy GameState with a reasonable map size and random floors/walls
    config = GameConfig(
        width=50,
        height=50,
        stage_key="test_stage",
        generator="",
        max_ticks=1000,
        emit_signals=True,
        vis_radius=5,
        max_gems=10,
        gem_spawn_rate=0.1,
        gem_ttl=50,
        signal_radius=3,
        signal_cutoff=0.5,
        signal_noise=0.1,
        signal_quantization=1,
        signal_fade=1,
        bot_seed=42,
    )
    gs = GameState(
        tick=0,
        bot=Coords(0, 0),
        wall=set(),
        floor=set(),
        initiative=True,
        visible_gems=[],
        visible_bots=[],
        config=config,
    )
    # Simulate some known floors and hidden positions

    for x in range(10, 40):
        for y in range(10, 40):
            gs.known_floors[Coords(x, y)] = Floor(
                position=Coords(x, y), last_seen=0
            )  # Assign a valid Floor instance
    all_coords = set(
        Coords(x, y) for x in range(config.width) for y in range(config.height)
    )
    known_coords = set(gs.known_floors.keys())
    gs.hidden_positions = all_coords - known_coords
    return gs


def test_update_hidden_floors_perf():
    gs = setup_gamestate()
    t = timeit.timeit(lambda: gs.update_hidden_floors(), number=100)
    print(f"update_hidden_floors: {t:.4f} seconds for 100 runs")

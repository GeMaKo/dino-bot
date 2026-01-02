import pytest

from src.gamestate import GameState
from src.schemas import Coords, EnemyBot, Floor, GameConfig
from src.strategies.patrol import last_seen_sum_patrol_point_evaluator


@pytest.fixture
def setup_gamestate():
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
        tick=100,
        bot=Coords(1, 1),
        wall=set(),
        floor={
            Floor(position=Coords(1, 2), last_seen=10),
            Floor(position=Coords(2, 2), last_seen=90),
            Floor(position=Coords(3, 3), last_seen=80),
        },
        initiative=False,
        visible_gems=[],
        visible_bots=[EnemyBot(position=Coords(2, 2))],
        config=config,
    )
    gs.gem_captured_tick = 50
    gs.recent_positions = [Coords(2, 2), Coords(3, 3)]
    gs.known_floors = {
        Coords(1, 2): Floor(position=Coords(1, 2), last_seen=10),
        Coords(2, 2): Floor(position=Coords(2, 2), last_seen=90),
        Coords(3, 3): Floor(position=Coords(3, 3), last_seen=80),
    }
    # gs.known_wall_positions = set()  # Ensure this is present for pathfinding
    gs.visibility_map = {
        Coords(1, 2): {Coords(1, 2), Coords(2, 2)},
        Coords(3, 3): {Coords(3, 3)},
        Coords(2, 2): {Coords(2, 2), Coords(3, 3)},
    }
    return gs


def test_last_seen_sum_patrol_point_evaluator_basic(setup_gamestate):
    move = Coords(1, 2)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_penalties(setup_gamestate):
    move = Coords(3, 3)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_no_recent_positions(setup_gamestate):
    setup_gamestate.recent_positions = []
    move = Coords(3, 3)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_high_tick(setup_gamestate):
    setup_gamestate.tick = 1000
    move = Coords(1, 2)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_missing_visibility(setup_gamestate):
    move = Coords(2, 2)
    setup_gamestate.visibility_map[move] = set()
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_missing_known_floor(setup_gamestate):
    move = Coords(4, 4)
    setup_gamestate.visibility_map[move] = {Coords(4, 4)}
    setup_gamestate.known_floors[Coords(4, 4)] = Floor(
        position=Coords(4, 4), last_seen=0
    )
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0
    if path:
        assert path[0] == setup_gamestate.bot
        assert path[-1] == move


def test_last_seen_sum_patrol_point_evaluator_empty_visibility_map(setup_gamestate):
    move = Coords(5, 5)
    setup_gamestate.visibility_map[move] = set()
    setup_gamestate.known_floors[Coords(5, 5)] = Floor(
        position=Coords(5, 5), last_seen=0
    )
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0


def test_last_seen_sum_patrol_point_evaluator_all_recent_positions(setup_gamestate):
    setup_gamestate.recent_positions = [Coords(1, 2), Coords(2, 2), Coords(3, 3)]
    move = Coords(1, 2)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0


def test_last_seen_sum_patrol_point_evaluator_enemy_penalty(setup_gamestate):
    # Simulate visible_bots matching recent_positions as a set
    setup_gamestate.visible_bots = [
        EnemyBot(position=Coords(2, 2)),
        EnemyBot(position=Coords(3, 3)),
    ]
    setup_gamestate.recent_positions = [Coords(2, 2), Coords(3, 3)]
    move = Coords(2, 2)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0


def test_last_seen_sum_patrol_point_evaluator_large_tick_difference(setup_gamestate):
    setup_gamestate.tick = 5000
    setup_gamestate.gem_captured_tick = 100
    move = Coords(1, 2)
    path, score = last_seen_sum_patrol_point_evaluator(setup_gamestate, move)
    assert isinstance(path, list)
    assert isinstance(score, float)
    assert score > 0

import json

from bot import CollectorBot
from bot_helper import generate_arena_state


def test_bot_initialization():
    bot = CollectorBot()
    assert hasattr(bot, "width")
    assert hasattr(bot, "height")
    assert hasattr(bot, "walls")


def test_process_input_first_tick_sets_config():
    bot = CollectorBot()
    state = json.loads(generate_arena_state())
    line = json.dumps(state)
    move = bot.process_input(line, first_tick=True)
    assert bot.width == state["config"]["width"]
    assert bot.height == state["config"]["height"]
    assert bot.walls == set(tuple(w) for w in state["wall"])
    assert move == "WAIT" or move in {"N", "S", "E", "W"}


def test_navigate_to_gem_returns_next_pos():
    bot = CollectorBot()
    bot.width = 5
    bot.height = 5
    bot.walls = set()
    game_state = {"bot": [0, 0], "visible_gems": [{"position": [2, 2]}]}
    next_pos = bot.navigate_to_gem(game_state)
    assert isinstance(next_pos, tuple)
    assert next_pos != (0, 0)


def test_get_path_to_closest_top3_gem_returns_path():
    bot = CollectorBot()
    bot.width = 5
    bot.height = 5
    bot.walls = set()
    gems = [{"position": [2, 2]}, {"position": [1, 1]}]
    path = bot.get_path_to_closest_top3_gem((0, 0), gems)
    assert isinstance(path, list)
    assert path[0] == (0, 0)
    assert path[-1] in {(2, 2), (1, 1)}


def test_process_input_move_direction():
    bot = CollectorBot()
    bot.width = 5
    bot.height = 5
    bot.walls = set()
    state = {
        "bot": [0, 0],
        "visible_gems": [{"position": [0, 1]}],
        "config": {"width": 5, "height": 5},
        "wall": [],
    }
    line = json.dumps(state)
    move = bot.process_input(line, first_tick=False)
    assert move in {"N", "S", "E", "W", "WAIT"}

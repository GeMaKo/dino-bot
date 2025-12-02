import json

import pytest

from src.bot import CollectorBot
from src.bot_helper import generate_arena_state
from src.gamestate import GameState
from src.schemas import GameConfig


@pytest.mark.parametrize(
    "strategy",
    [
        "greedy",
        "advanced_greedy",
        "tsm_collection",
        # "cave_explore_greedy",
    ],
)
def test_collector_bot_moves_on_arena(strategy):
    # Generate initial arena state
    state_json = generate_arena_state()
    state = json.loads(state_json)
    config = GameConfig.from_dict(state["config"])
    # Remove config for subsequent ticks
    state_no_config = dict(state)
    state_no_config.pop("config", None)

    # Instantiate bot
    bot = CollectorBot(name="TestBot", strategy=strategy)
    # Initialize game state
    bot.game_state = GameState.from_dict(state_no_config, config)
    bot.game_state.debug_mode = False
    bot.game_state.refresh()

    # Simulate a few moves
    moves = []
    for _ in range(5):
        move, path = bot.process_game_state()
        moves.append(move)
        # Simulate tick update (no gems, bot moves)
        new_x = bot.game_state.bot.x + (1 if move == "E" else 0)
        new_y = bot.game_state.bot.y + (1 if move == "S" else 0)
        # Update bot position using a setter or by creating a new Coords object
        bot.game_state.bot = type(bot.game_state.bot)(x=new_x, y=new_y)
        bot.game_state.refresh()
    # Ensure bot made valid moves
    assert all(m in ["N", "S", "E", "W", "WAIT"] for m in moves)
    assert len(moves) == 5


def test_collector_bot_moves_toward_gem():
    state_json = generate_arena_state()
    state = json.loads(state_json)
    config = GameConfig.from_dict(state["config"])
    state_no_config = dict(state)
    state_no_config.pop("config", None)
    # Place a gem near the bot
    state_no_config["visible_gems"] = [{"position": [5, 12], "ttl": 100}]
    bot = CollectorBot(name="TestBot", strategy="greedy")
    bot.game_state = GameState.from_dict(state_no_config, config)
    bot.game_state.refresh()
    move, path = bot.process_game_state()
    # Bot should move east toward the gem
    assert move == "E"


def test_collector_bot_avoids_wall():
    state_json = generate_arena_state()
    state = json.loads(state_json)
    config = GameConfig.from_dict(state["config"])
    state_no_config = dict(state)
    state_no_config.pop("config", None)
    # Place bot next to a wall on the east
    state_no_config["bot"] = [1, 0]  # Next to wall at [2, 0]
    bot = CollectorBot(name="TestBot", strategy="greedy")
    bot.game_state = GameState.from_dict(state_no_config, config)
    bot.game_state.refresh()
    move, path = bot.process_game_state()
    # Bot should not move east into the wall
    assert move != "E"


def test_collector_bot_reacts_to_enemy():
    state_json = generate_arena_state()
    state = json.loads(state_json)
    config = GameConfig.from_dict(state["config"])
    state_no_config = dict(state)
    state_no_config.pop("config", None)
    # Place an enemy bot near our bot
    state_no_config["visible_bots"] = [{"position": [5, 12]}]
    bot = CollectorBot(name="TestBot", strategy="advanced_greedy")
    bot.game_state = GameState.from_dict(state_no_config, config)
    bot.game_state.refresh()
    move, path = bot.process_game_state()
    # Bot should not move directly into the enemy position
    if path:
        assert [5, 12] not in [[p.x, p.y] for p in path]

from src.bot import CollectorBot
from src.config import Coords, EnemyBot, GameConfig, Gem, Wall
from src.gamestate import GameState


def make_config():
    return GameConfig(
        stage_key="test",
        width=5,
        height=5,
        generator="test",
        max_ticks=100,
        emit_signals=False,
        vis_radius=3,
        max_gems=5,
        gem_spawn_rate=1.0,
        gem_ttl=10,
        signal_radius=1.0,
        signal_cutoff=0.5,
        signal_noise=0.1,
        signal_quantization=1,
        signal_fade=1,
        bot_seed=42,
    )


def make_game_state(bot_pos=(0, 0), gems=None, walls=None, enemies=None):
    if gems is None:
        gems = []
    if walls is None:
        walls = set()
    if enemies is None:
        enemies = []
    game_state = GameState(
        tick=1,
        bot=Coords(*bot_pos),
        wall={Wall(position=Coords(*w)) for w in walls},
        floor=set(),
        initiative=True,
        visible_gems=gems,
        visible_bots=[EnemyBot(position=Coords(*e)) for e in enemies],
        config=make_config(),
    )
    game_state.update_gem_distances()
    game_state.update_distance_matrix()
    return game_state


def test_navigate_to_gem_moves_toward_gem():
    bot = CollectorBot("TestBot")

    gem = Gem(position=Coords(2, 2), ttl=10)
    bot.game_state = make_game_state(bot_pos=(0, 0), gems=[gem])
    gem.distance2bot = 4
    gem.reachable = True
    next_pos = bot.navigate_to_gem([gem])
    assert next_pos != bot.game_state.bot
    assert isinstance(next_pos, Coords)


def test_search_gems_moves_toward_center():
    bot = CollectorBot("TestBot")
    bot.game_state = make_game_state(bot_pos=(0, 0))
    bot.game_state.config = make_config()
    pos = bot.search_gems()
    assert isinstance(pos, Coords)
    assert pos != bot.game_state.bot


def test_enrich_game_state_sets_distances_and_reachable():
    bot = CollectorBot("TestBot")
    gem = Gem(position=Coords(2, 2), ttl=10)
    bot.game_state = make_game_state(bot_pos=(0, 0), gems=[gem], enemies=[(4, 4)])
    bot.game_state.config = make_config()
    assert bot.game_state.visible_gems[0].distance2bot is not None
    assert isinstance(bot.game_state.visible_gems[0].distance2enemies, list)
    assert isinstance(bot.game_state.visible_gems[0].reachable, bool)


def test_process_game_state_returns_move():
    bot = CollectorBot("TestBot")
    gem = Gem(position=Coords(2, 2), ttl=10)
    bot.game_state = make_game_state(bot_pos=(0, 0), gems=[gem])
    bot.game_state.config = make_config()
    gem.distance2bot = 4
    gem.reachable = True
    move = bot.process_game_state()
    assert move in {"N", "S", "E", "W", "WAIT"}


def test_run_reads_and_prints(monkeypatch, capsys):
    bot = CollectorBot("TestBot")
    config = make_config()
    data = {
        "config": config.__dict__,
        "tick": 1,
        "bot": [0, 0],
        "wall": [],
        "floor": [],
        "initiative": True,
        "visible_gems": [{"position": [2, 2], "ttl": 10}],
        "visible_bots": [],
    }
    import json

    lines = [json.dumps(data) + "\n"]
    monkeypatch.setattr("sys.stdin", lines)
    bot.run()
    out = capsys.readouterr().out
    assert out.strip() in {"N", "S", "E", "W", "WAIT"}

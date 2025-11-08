from config import Coords, EnemyBot, Floor, Gem, Wall
from gamestate import GameState


def parse_gamestate(data: dict) -> GameState:
    bot = Coords(x=data["bot"][0], y=data["bot"][1])
    wall = {Wall(position=Coords(x=w[0], y=w[1])) for w in data["wall"]}
    floor = {Floor(position=Coords(x=f[0], y=f[1])) for f in data["floor"]}
    visible_gems = [
        Gem(
            position=Coords(x=g["position"][0], y=g["position"][1]),
            ttl=g["ttl"],
            distance2bot=g.get("distance2bot"),
            distance2enemies=g.get("distance2enemies", []),
            reachable=g.get("reachable", False),
        )
        for g in data["visible_gems"]
    ]
    visible_bots = [
        EnemyBot(position=Coords(x=b["position"][0], y=b["position"][1]))
        for b in data.get("visible_bots", [])
    ]
    return GameState(
        tick=data["tick"],
        bot=bot,
        wall=wall,
        floor=floor,
        initiative=data["initiative"],
        visible_gems=visible_gems,
        visible_bots=visible_bots,
    )

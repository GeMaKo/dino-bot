#!/usr/bin/env python3
from src.bot import CollectorBot
from src.config import NAME, STRATEGY

if __name__ == "__main__":
    bot = CollectorBot(NAME, STRATEGY)
    bot.run()

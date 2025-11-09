#!/usr/bin/env python3
from src.bot import CollectorBot
from src.config import DEBUG_MODE, NAME, STRATEGY

if __name__ == "__main__":
    bot = CollectorBot(NAME, STRATEGY, debug_mode=DEBUG_MODE)
    bot.run()

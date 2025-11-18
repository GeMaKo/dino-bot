# Dino Bot

A Python bot for navigating and collecting gems in a grid-based arena. The bot supports multiple strategies for gem collection and search, including advanced center bias and enemy avoidance. The project demonstrates modular strategy registration, pathfinding, state management, and bot logic for a simple game environment.

## Features
- Multiple strategies: greedy, advanced greedy, TSM collection, center-biased search
- Modular strategy registry for easy extension
- Breadth-First Search (BFS) pathfinding
- Manhattan distance calculation
- Arena state generation for testing
- Configurable grid size, walls, and gem logic
- Center bias and enemy avoidance logic
- Scikit-learn style docstrings for all public functions

## Project Structure
```
├── bot.py              # Main bot logic and entry point
├── bot_helper.py       # Arena state generation utilities
├── pathfinding.py      # Pathfinding and distance functions
├── bot.yaml            # Bot configuration
├── Makefile            # Build and run commands
├── start.sh / .bat     # Startup scripts
├── pyproject.toml      # Poetry dependency management
├── src/                # Source code
│   ├── bot.py          # Bot class and main loop
│   ├── bot_logic.py    # Bot decision logic
│   ├── config.py       # Configuration constants
│   ├── gamestate.py    # Game state management
│   ├── pathfinding.py  # Pathfinding algorithms
│   ├── schemas.py      # Data schemas
│   ├── strategy_register.py # Strategy registry and factory
│   └── strategies/     # Strategy implementations
│       ├── planners.py     # Move planners
│       ├── evaluators.py   # Move evaluators
│       ├── schemas.py      # Strategy schemas
│       └── __init__.py     # Strategy module init
└── tests/              # Unit tests
```

## Getting Started
1. **Install dependencies** (uses Poetry):
   ```bash
   make .venv
   make install
   ```
   For development dependencies:
   ```bash
   make install-dev
   ```
2. **Run tests**:
   ```bash
   make tests
   ```

## Usage
- The bot reads game state from stdin and prints its next move to stdout.
- Multiple strategies are available and can be selected via configuration (see `src/strategy_register.py`).
- Arena state can be generated using `bot_helper.py` for testing.
- Pathfinding is handled in `pathfinding.py`.
- Strategies include greedy collection, advanced search (center bias, enemy avoidance), and TSM collection.
- Extend or add new strategies by editing the `src/strategies/` and `src/strategy_register.py` modules.

## Strategies

The bot supports several strategies for gem collection and movement:

The bot supports several strategies for gem collection and movement:
- **Advanced Greedy**: Combines greedy collection with center bias and enemy avoidance.
- **TSM Collection**: Uses a Traveling Salesman Model (stub) for optimal gem collection.
- **Simple/Advanced Search**: Moves towards the center, avoids enemies, and prefers safe positions.


- **Hidden Exploration**: When gems are not visible or the arena is partially unexplored, the bot will explore unknown tiles to maximize future gem collection and avoid getting stuck. This is especially useful in fog-of-war scenarios or when the arena layout changes dynamically.
Strategies are registered in `src/strategy_register.py` and can be extended or customized.

Exploration logic is integrated into the bot's decision-making, allowing it to switch between collection and exploration modes as needed.
## Configuration

Bot configuration is provided via `bot.yaml` and/or the game state input. See `src/config.py` for constants and tuning parameters.

## Development

- Uses [Poetry](https://python-poetry.org/) for dependency management (`pyproject.toml`).
- Development tools: `pre-commit`, `ruff`, `pytest`.

## License

MIT License.

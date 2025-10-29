# Dino Bot

A Python bot for navigating and collecting gems in a grid-based arena. This project demonstrates pathfinding, state management, and bot logic for a simple game environment.

## Features
- Breadth-First Search (BFS) pathfinding
- Manhattan distance calculation
- Arena state generation for testing
- Configurable grid size, walls, and gem logic
- Scikit-learn style docstrings for all public functions

## Project Structure
```
├── bot.py              # Main bot logic and entry point
├── bot_helper.py       # Arena state generation utilities
├── pathfinding.py      # Pathfinding and distance functions
├── bot.yaml            # Bot configuration
├── Makefile            # Build and run commands
├── start.sh / .bat     # Startup scripts
└── tests/              # Unit tests
```

## Getting Started
1. **Install dependencies**:
   ### For usage
   ```bash
   make .venv
   make install
   ```
   ### For development
   ```bash
   make .venv
   make install-dev
   ```
2. **Run tests**:
   ```bash
   make tests
   ```

## Usage
- The bot reads game state from stdin and prints its next move to stdout.
- Arena state can be generated using `bot_helper.py` for testing.
- Pathfinding is handled in `pathfinding.py`.

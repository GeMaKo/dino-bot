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
├── bot.yaml            # Bot configuration (if used)
├── Makefile            # Build and run commands
├── start.sh / .bat     # Startup scripts
├── tests/              # Unit tests
└── dino_bot_debug.txt  # Debug output
```

## Getting Started
1. **Install dependencies** (if any):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # if exists
   ```
2. **Run the bot**:
   ```bash
   python bot.py
   ```
3. **Run tests**:
   ```bash
   python -m unittest discover tests
   ```

## Usage
- The bot reads game state from stdin and prints its next move to stdout.
- Arena state can be generated using `bot_helper.py` for testing.
- Pathfinding is handled in `pathfinding.py`.

## Example
```python
from bot_helper import generate_arena_state
print(generate_arena_state())
```

## Documentation
All public functions and classes use scikit-learn style docstrings for clarity and consistency.

## Contributing
Pull requests and issues are welcome! Please ensure code is well-documented and tested.

## License
MIT License

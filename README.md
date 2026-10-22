# Fieldwork Tic Tac Toe

A small, animated Tic Tac Toe game for a quick match on desktop or mobile. Play against the computer, share a keyboard for local two-player games, or invite another person on your network with a room code.

Updated October 22, 2026.

## Run It

You need Python 3.10 or newer. The server uses only Python's standard library, so there is nothing extra to install.

```bash
python code1.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser. In a Codespace, open port `8000` from the **Ports** panel and use its forwarded address. Keep the terminal running while you play; press `Ctrl+C` to stop the server.

To use a different port on Linux or macOS:

```bash
PORT=8080 python code1.py
```

## Play

- **Vs Computer**: Play as X and choose a level. Easy makes random moves, Medium wins or blocks immediate threats, and Hard uses minimax search and can force a draw if you play perfectly.
- **Local 2P**: Take turns on the same screen and keyboard. X moves first.
- **LAN Play**: One person creates a room and shares the six-character code and a reachable server address. The other person enters the code to join as O. Moves sync through the Python server.

Click a square, or use the keyboard:

- Arrow keys move the selection; `1` through `9` select a square directly.
- `X` or `O` places that player's mark when it is their turn.
- `R` starts a new round.

After a win or draw, the result dialog starts the next round when dismissed. The match score is for the current page session. Wins, losses, draws, current streak, and best streak are saved in that browser's local storage.

## LAN Notes

LAN play works while the Python server stays running. Both players need to be able to reach the same server address; on a home network, use the host computer's local IP and allow inbound traffic on the chosen port. In Codespaces, use its forwarded port address and make sure the other player has permission to open it. Room state lives in server memory, expires after 12 hours, and is cleared when the server stops. Use room codes only with people you trust; this lightweight game server is intended for casual private play, not public hosting.

## Project Files

- `code1.py` starts the web server and handles LAN rooms and legal moves.
- `tic-tac-toe/index.html` contains the responsive interface and game logic.

The interface respects reduced-motion settings. Player statistics stay in the browser and are not sent to the server.

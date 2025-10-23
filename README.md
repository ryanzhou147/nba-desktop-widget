# NBA Desktop Widget

A lightweight desktop widget that shows live NBA game status, scores, play-by-play, and box scores.

This repository provides a small PyQt5 application that fetches live NBA data and displays it in a compact, themeable UI.

---

## Key features

- Live scoreboard and game details
- Compact, resizable desktop UI built with PyQt5
- Light/dark themes
- Box score and recent plays per game
- Local team logo support (fast lookup and in-memory caching)

---

## Quick start

Prerequisites: Python 3.8+, system packages required for PyQt5 (install via your distro package manager if necessary).

1. Create a virtual environment and run the app (recommended):

```bash
# from project root
./run_venv.sh
```

2. The script creates `.venv/`, installs packages from `requirements.txt`, and launches the application.

---

## Dependencies

- Python 3.8+
- PyQt5
- nba_api
- python-dateutil
- requests

All Python packages are listed in `requirements.txt`.

---

## Configuration

- To run with a specific Python interpreter, set the `PYTHON` env var: `PYTHON=python3.11 ./run_venv.sh`
- The app attempts to preload logo images into memory for common sizes on startup. If PyQt5 is not installed at preload time, the app will still find file paths and load images on demand.

---

## Troubleshooting

- If the UI fails to start, ensure system Qt libraries are installed (Ubuntu: `sudo apt install libxcb-xinerama0 libxkbcommon-x11-0` or install the `python3-pyqt5` package).
- If logos do not display: check `nba-logos/` for correct filenames and supported image formats.
- For API failures, verify network access and consider adding retries or adjusting cache timeouts.

---

## Development

- The codebase separates responsibilities (UI widgets, logo utilities, services). Add tests for pure helpers (e.g., filename matching) using pytest.
- Keep UI code in `app.py` and widget components in separate modules for easier maintenance.

---

## License & Attribution

This project uses data from public NBA APIs. Confirm any licensing requirements for redistribution of logos or API usage before publishing broadly.

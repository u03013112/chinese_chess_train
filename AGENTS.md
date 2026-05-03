# AGENTS.md

Notes for AI agents working in this Chinese Chess (Xiangqi) training repo. Covers only things you would otherwise get wrong. Companion doc `CLAUDE.md` has more prose background — read it if you need more context.

## What this repo is

A personal training pipeline, not a product. Flow:
`screen capture/scrape` → `image → FEN` → `Pikafish UCI analysis` → `CSV` → `tkinter GUIs` for review and puzzle drills.

No package metadata (`pyproject.toml`, `setup.py`), no lockfile, no tests, no CI, no formatter/linter config. Do not invent them unless asked.

## Layout you need to know

- `src/` — all Python. Flat module layout, all imports are by bare module name (`from tools import ...`). Run scripts from inside `src/` or with `src/` on `sys.path`.
- `qipu/` — game records. `.txt` files are line-per-FEN sequences; `.csv` files are Pikafish analysis output (produced by `AnaylizeFenFile.py`). `qipu/raw/<qipuId>.json` holds the structured payload fetched from 天天象棋 H5 (via `fdk.Joa.ba('NOTIFY_QIPU_DATA', ...)` hook — see `docs/playwright_interactive_exploration.md`); `qipu/raw_legacy/` keeps earlier hand-massaged JSON shapes for reference.
- `yolo/` — YOLOv8 training data + `coco8.yaml` (dataset expected at `~/datasets`). Trained weights live under `~/.pyenv/runs/detect/trainN/weights/` after running `yolo train`.
- `img/` — piece templates used by the legacy SIFT recognizer only.
- `screenSnapshot/` — recorded `.avi` clips (gitignored-ish; `*.avi` ignored).
- `docker/` — Docker runtime for the Linux/engine side (lowercase `dockerfile` + `makefile`, not the defaults).
- `docs/`, `src/*.md`, `yolo/train.md` — design notes in Chinese, mostly aspirational. Trust code over these notes when they conflict.

## Running things

### Local (macOS) — GUIs and most dev work

```bash
python src/history.py      # review analyzed games (reads qipu/*.csv)
python src/lookKillUI.py   # checkmate puzzle trainer (reads qipu/*.csv)
python src/exportUI.py     # screen capture → FEN export (tkinter)
python src/tools.py        # smoke test for FEN / move utilities
```

GUI apps assume CWD is `src/` because they read `../qipu` (see `LookKill.__init__`). `cd src && python history.py` is the safe invocation.

### Docker (Linux, for running the engine alongside the app)

```bash
cd docker && make all                         # build u03013112/chinese_chess_train:v1
cd docker && docker-compose up -d              # starts `pikafish` + `chinese_chess` containers
docker exec -it chinese_chess python /src/pikafish.py
```

`docker/docker-compose.yml` mounts `../src` → `/src` and gives `chinese_chess` `privileged: true` + `/proc:/host/proc`. This is required because `pikafish.py` defaults to:

```
nsenter --mount=/host/proc/1/ns/mnt docker exec -i pikafish /app/pikafish
```

i.e. the app container shells out of itself via `nsenter` to reach the sibling `pikafish` container. Do not "simplify" this without understanding the topology.

### YOLO training (Apple Silicon)

```bash
yolo train data=coco8.yaml model=yolov8n.pt epochs=300 lr0=0.01 device=mps
yolo detect predict model=<…>/weights/last.pt source=yolo/images/val/2.jpg
```

### Scraping 天天象棋 (Playwright + Chrome CDP)

```bash
bash start_chess_chrome.sh              # launches Chrome with --remote-debugging-port=9222
python src/extract_chess_data.py        # or: chrome_debug.py / chess_explorer.py / auto_nav.py
```

These scripts talk to a live Chrome via CDP and introspect the Cocos scene (`cc.director.getScene()`). They need a real logged-in session; `src/login_info.json` and `src/chrome_data/` persist browser state and are not in git.

**None of the standalone `.py` scrapers above have produced a real 棋谱 end-to-end** (the pre-2026 `qipu/` CSVs were made by the old image-recognition path). The current working approach is Playwright MCP `evaluate` driven interactively — the canonical playbook (coordinate formula, `MouseEvent` click channel, `StartBtn_1` disambiguation, `fdk.Joa.ba` event hook for the `QipuModel.requestGetQipuInfo` API, etc.) is in [`docs/playwright_interactive_exploration.md`](docs/playwright_interactive_exploration.md). Treat the `.py` scrapers as historical scaffolding, not a recommended entrypoint. `docs/web_data_extraction_workflow.md` keeps only the generic cross-site methodology; its 天天象棋-specific sections are marked 作废.

The H5 API route produces `qipu/raw/<qipuId>.json` (each payload contains `sData` — a JSON string with `moveinfo.binit` + `moveinfo.movelist`, where `movelist` is a compressed `fx fy tx ty` string, 4 chars per ply). `src/qipu2txt.py` converts these into the `qipu/<qipuId>.txt` (one FEN per line) format that `AnaylizeFenFile.py` expects, and is also backward-compatible with the older `{startFen, moves:[[fx,fy,tx,ty]...]}` shape under `qipu/raw_legacy/`. Run `cd src && python3 qipu2txt.py smoke` for a quick sanity check, or `python3 qipu2txt.py` to batch-convert everything under `qipu/raw/`.

## Dependencies — there is no canonical list

`docker/requirements.txt` contains only `opencv-contrib-python`. The rest are implicit. Actually imported across `src/`:

- `cv2`, `numpy`, `pandas`, `tkinter` (stdlib on a full Python)
- `ultralytics` (`img2FenByYolo.py`)
- `pynput`, `mss`, `PIL` (`screenSnapShot.py`)
- `playwright`, `requests`, `websocket` (scrapers)

If `pip install` fails inside the Docker image, it is expected — add to `docker/requirements.txt` or install ad-hoc.

## Pikafish wiring (high-gotcha)

- `src/pikafish.py` — raw subprocess wrapper with non-blocking stdout (`fcntl` + `select`). Default command assumes Docker/`nsenter`.
- `src/pikafishHelper.py` — high-level interface. **Hard-codes a macOS path:**

  ```python
  self.pikafish = Pikafish('/Users/u03013112/Documents/git/Pikafish/src/pikafish')
  ```

  Any other user / machine must edit this or the module fails at import-time call. On Linux it falls through to the default `nsenter` command.
- Default options pushed on init: `Threads=8`, `MultiPV=20`, search `depth=10`.
- `parseGoResponse` returns up to MultiPV entries sorted by score desc. Mate scores are synthesized: `10000 - mateStepCount*100` (win) or `-10000 - mateStepCount*100` (loss). The `9000` threshold in `lookKill.py` relies on this mapping — do not change one without the other.

## FEN / coordinate conventions (READ CAREFULLY)

The README explicitly flags a historical inversion bug. The **correct, UCI-native** convention, which `tools.py`, `pikafishHelper.py`, `pikafish.md`, and the Pikafish engine all use:

- **Uppercase = Black** (top of board), **lowercase = Red** (bottom).
- FEN rows are listed **top-to-bottom** (black side first, red side last).
- Starting position: `rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR`.
- Board is 9×10, files `a`–`i`, ranks `0`–`9`. A UCI move is 4 chars, e.g. `h2e2`.
- `ChessBoard.py::readFen` contains an **inverted color mapping** (`'黑' if char.isupper() == False else '红'` + a commented-out `y = (10 - int(pos[1]))` swap) that is part of the old bug. If you touch board rendering, verify against a known position, do not trust the widget as a reference.

`tools.getMove(lastFen, fen)` returns `(piece_char, uci_move)` and raises `ValueError` if more than two squares changed or a piece "morphed" — do not silently `except`; it is the main integrity check in the pipeline.

`tools.lastFenAndMove2Qp(fen, move)` converts a move to Chinese notation (`红 炮二平五`) using `pNameList`. It is incomplete for some piece types (notation for 兵/卒 and diagonal cases is approximate).

## Module map — who calls whom

GUIs: `history.py`, `lookKillUI.py`, `exportUI.py` → `ChessBoard.py` + `tools.py` + (`lookKill.py` | `export.py`)
Analysis: `AnaylizeFenFile.py` → `pikafishHelper.py` → `pikafish.py`; also `tools.py`
Recognition: `export.py` → `img2Fen.py` (SIFT, legacy); `img2FenByYolo.py` is the YOLO replacement but `export.py` still imports the legacy one
Qipu import (H5 API route): Playwright `evaluate` hook → `qipu/raw/<qipuId>.json` → `qipu2txt.py` → `qipu/<qipuId>.txt` → `AnaylizeFenFile.py` → `qipu/<qipuId>.csv`
Scrapers (standalone, Playwright, historical): `chess_explorer.py`, `auto_nav.py`, `extract_chess_data.py`, `analyze_login.py`, `chrome_debug.py`

## Style conventions (differ from Python defaults)

- **camelCase** for functions/methods/variables (`sendCMD`, `getFenFromImg`, `boardRect`). Do not "fix" to PEP8.
- Classes are PascalCase.
- Module-level constants are camelCase too (`pNameList`), not `UPPER_SNAKE`.
- Imports: stdlib → third-party → local (bare names). No `__init__.py`; no package prefixes.
- No type hints, no docstrings. Comments are Chinese; keep new comments in Chinese when editing existing Chinese-commented code.
- Errors: `raise ValueError(f"…")` with a Chinese message, consistent with `tools.py` and `export.py`.

## Things that look wrong but are intentional

- `docker/dockerfile` and `docker/makefile` are lowercase. `make` still finds `makefile`; `docker build` finds `dockerfile` via default search. Do not rename without updating both scripts and muscle memory.
- `sync.sh` is a personal `fswatch + rsync` loop to a specific LAN host (`root@192.168.40.62`). Ignore unless you own that host.
- `.history/`, `chrome_data/`, `*.avi` are ignored. The committed `.history/` entries in `.gitignore` is intentional.
- `CLAUDE.md` duplicates some of this. Treat it as supplementary; keep AGENTS.md as the source of truth when they drift.

## Tasks that are NOT supported

- No automated tests, pytest config, or test runner. Do not add one without being asked.
- No linter/formatter. Do not run `black`/`ruff`/`isort` over the tree.
- No packaging. `pip install -e .` will not work.
- No CI. `.github/workflows/` does not exist.

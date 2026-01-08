# AGENTS.md

Guidelines for AI coding agents working in this Chinese Chess (Xiangqi) training system.

## Project Overview

Chinese Chess training system: screenshot recognition (OpenCV + YOLO), position analysis (Pikafish UCI engine), checkmate puzzles, and GUI tools.

**Stack:** Python 3.11, tkinter, OpenCV, ultralytics (YOLO), pandas, numpy

## Build & Run Commands

### Docker Environment
```bash
cd docker && make all                    # Build Docker image
docker-compose up -d                     # Start services
docker exec -it chinese_chess python /src/script_name.py  # Run scripts
```

### GUI Apps (run locally on macOS)
```bash
python src/history.py      # Game review
python src/lookKillUI.py   # Checkmate trainer
python src/exportUI.py     # Position export
```

### YOLO Training
```bash
yolo train data=coco8.yaml model=yolov8n.pt epochs=300 lr0=0.01 device=mps
```

### Testing

**No automated tests configured.** Manual testing only:
```bash
python src/tools.py                                        # Test FEN utilities
docker exec -it chinese_chess python /src/pikafish.py      # Test engine connection
```

## Code Style Guidelines

### Naming Conventions

| Element | Style | Examples |
|---------|-------|----------|
| Classes | PascalCase | `ChessBoard`, `PikafishHelper`, `Img2FenByYolo` |
| Functions/Methods | camelCase | `sendCMD()`, `getBoardRect()`, `getFenFromImg()` |
| Variables | camelCase | `boardRect`, `fenList`, `moveFrom` |
| Constants | lowercase with camelCase | `pNameList` (not PEP8 UPPER_SNAKE_CASE) |

**Note:** This project uses camelCase (not PEP8 snake_case) for functions and methods.

### Import Organization

Standard library first, then third-party, then local modules:
```python
import os
import time
import subprocess

import cv2
import numpy as np
import pandas as pd

from pikafish import Pikafish
from tools import getMove
```

### Type Hints

Not used in this codebase. When adding new code, type hints are optional but welcome.

### Error Handling

Use `ValueError` with descriptive f-string messages (Chinese comments acceptable):
```python
if diff_count > 2:
    raise ValueError(f"变化的数量太多了, diff_count={diff_count}")

if pLast != p:
    raise ValueError(f"棋子发生了变化, {pLast} => {p}")
```

### Docstrings & Comments

- Comments are primarily in Chinese
- No formal docstring convention (no module/function docstrings)
- Inline comments explain complex logic:
```python
# 按照中国象棋的规则，棋子是不能凭空消失的
# 找到 红车 与 黑车 的位置，以此确定棋盘的位置
```

### Class Structure

```python
class ClassName:
    def __init__(self, param="default"):
        self.attribute = value
    
    def publicMethod(self):
        pass
    
    def _privateMethod(self):  # underscore for internal methods
        pass

if __name__ == '__main__':
    # Direct execution code
    instance = ClassName()
```

## Critical Domain Knowledge

### FEN Notation (IMPORTANT)

**Known Issue:** The FEN interpretation was historically incorrect. Be careful with piece colors:

- **Lowercase letters = Red pieces** (player at bottom)
- **Uppercase letters = Black pieces** (opponent at top)  
- Rows in FEN are listed top-to-bottom (black side to red side)
- Starting position: `rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR`

### UCI Coordinate System

- Board is 9x10 (columns a-i, rows 1-10)
- Bottom-left is `a1`, top-right is `i10`
- Moves are 4 characters: `h2e2` (from h2 to e2)

### Magic Numbers

- `9000`: Score threshold indicating forced checkmate
- `10`: Default engine analysis depth
- `3`: Default MultiPV value for top moves

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/pikafish.py` | UCI engine subprocess wrapper |
| `src/pikafishHelper.py` | High-level engine interface |
| `src/tools.py` | FEN/move utilities, coordinate conversion |
| `src/ChessBoard.py` | tkinter chess board widget |
| `src/img2FenByYolo.py` | YOLO-based piece detection (current) |
| `src/img2Fen.py` | SIFT-based piece detection (legacy) |
| `src/AnaylizeFenFile.py` | Position analysis pipeline |
| `src/lookKill.py` | Checkmate puzzle extraction |
| `src/history.py` | Game review GUI |

## Common Tasks

### Adding a New Analysis Feature

1. Read position from FEN file or image
2. Use `PikafishHelper` to query engine
3. Parse UCI response for scores/moves
4. Output to CSV for GUI consumption

### Working with Chess Positions

```python
from tools import getMove, lastFenAndMove2Qp

# Calculate move between two positions
piece, move = getMove(fen1, fen2)  # Returns ('c', 'h2e2')

# Convert to Chinese notation
chinese = lastFenAndMove2Qp(fen1, move)  # Returns '红 炮二平五'
```

### GUI Development

Inherit from `ChessBoard` for new chess displays:
```python
from ChessBoard import ChessBoard

class MyChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.board = ChessBoard(self, style=2)  # UCI style
        self.board.pack()
```

## File Locations

- **Source code:** `src/`
- **Game records:** `qipu/` (FEN and CSV files)
- **Chess piece images:** `img/` (for SIFT detection)
- **YOLO training data:** `yolo/` (images and labels)
- **Docker config:** `docker/`
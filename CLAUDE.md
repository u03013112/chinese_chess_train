# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese Chess (Xiangqi) training system that analyzes game records to identify and improve playing weaknesses. The system uses the Pikafish UCI chess engine to evaluate positions and generate training exercises.

**Core Components:**
- Chess position recognition from screenshots (OpenCV + YOLO)
- Position analysis using Pikafish UCI engine
- Training exercise generation (checkmate puzzles)
- GUI tools for reviewing games and practicing positions

## Development Commands

### Docker Environment

The project uses Docker to run the Pikafish chess engine and the main application:

```bash
# Build the Docker image
cd docker
make all

# Push to registry (if needed)
make push

# Start services
docker-compose up -d

# Access the Chinese chess training container
docker exec -it chinese_chess bash

# Access the Pikafish engine container
docker exec -it pikafish bash
```

### Python Development

All Python source files are in the `src/` directory and are mounted into the Docker container at runtime.

Run Python scripts inside the `chinese_chess` container:

```bash
docker exec -it chinese_chess python /src/script_name.py
```

### YOLO Training

Chess piece detection uses YOLOv8. Training is documented in `yolo/train.md`:

```bash
# Train on Apple Silicon (MPS)
yolo train data=coco8.yaml model=yolov8n.pt epochs=300 lr0=0.01 device=mps

# Test detection
yolo detect predict model=/path/to/weights/last.pt source='/path/to/image.jpg'
```

Dataset location: `~/datasets` (configured in `yolo/coco8.yaml`)

## Architecture

### UCI Engine Integration

**Pikafish** is a Chinese Chess UCI engine running in a separate Docker container. The main application communicates with it via subprocess and pipes.

**Key file:** `src/pikafish.py` - Wrapper class that manages the Pikafish process
- Uses `nsenter` to access the Pikafish container from the main container
- Non-blocking I/O with `fcntl` for async communication
- Methods: `sendCMD()`, `sendCMDSync()` for engine commands

**Helper:** `src/pikafishHelper.py` - Higher-level interface for common operations like position evaluation

### UCI Coordinate System

**Critical:** UCI uses algebraic notation with the board oriented from red's (white's) perspective:
- Bottom-left is `a1`, top-right is `i10`
- Red pieces (uppercase letters) at bottom, black pieces (lowercase) at top
- This differs from traditional Chinese chess notation

**FEN Format:**
```
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
```
- Uppercase = black pieces (despite convention)
- Lowercase = red pieces
- Rows are listed from top (black) to bottom (red)

See `src/pikafish.md` for detailed UCI protocol documentation.

### Position Analysis Pipeline

1. **Export/Capture** (`src/export.py`, `src/screenSnapShot.py`)
   - Capture chess positions from screen (e.g., from 天天象棋 app)
   - Convert images to board state

2. **Image Recognition** (`src/img2Fen.py`, `src/img2FenByYolo.py`)
   - SIFT-based piece detection (legacy)
   - YOLO-based piece detection (current)
   - Output: FEN notation strings

3. **Analysis** (`src/AnaylizeFenFile.py`)
   - Read FEN file with position sequence
   - For each move, query Pikafish for top 3 best moves with scores
   - Compare player's move against engine recommendations
   - Output: CSV with position, player move, score, and best moves

4. **Training Exercise Generation**
   - **Checkmate Puzzles** (`src/lookKill.py`): Extract positions where best move score > 9000 (forced checkmate)
   - Filter by steps to mate (1-step, 2-step, 3-step kills)

### GUI Applications

**ChessBoard** (`src/ChessBoard.py`)
- Base tkinter Canvas class for drawing chess boards
- Two coordinate styles: traditional Chinese (style=1) and UCI (style=2)
- Methods: `draw_board()`, `draw_piece()`, `place_piece()`

**History Viewer** (`src/history.py`)
- Review analyzed games step by step
- Shows player move vs. best engine moves
- Displays score differentials
- Input: CSV files from `AnaylizeFenFile`

**Checkmate Trainer** (`src/lookKillUI.py`)
- Interactive checkmate puzzle practice
- Random selection from puzzle database
- Shows answer on demand

**Export UI** (`src/exportUI.py`)
- GUI for capturing positions from screen
- Integrates with image recognition pipeline

### Utility Modules

**tools.py** (`src/tools.py`)
- `getMove(fen1, fen2)`: Calculate move between two FEN positions
- `lastFenAndMove2Qp()`: Convert FEN + moves to Chinese notation
- Helper functions for coordinate conversions

## Known Issues

**CRITICAL FEN INTERPRETATION ERROR (from README):**
> The original understanding of UCI FEN was incorrect. In FEN notation, lowercase letters represent black pieces, and each line represents the board from top to bottom (black to red). The previous understanding was reversed, causing all game records to be inverted. All board drawing and analysis code needs to account for this.

When working with FEN positions and board visualization, verify that the coordinate system and piece colors are correctly interpreted according to UCI standards.

## Project Goals & Workflow

1. **Export**: Extract games from 天天象棋 (Tiantian Xiangqi) or other apps via screenshot recognition
2. **Analyze**: Compare player moves against Pikafish engine at depth 10+
3. **Train**: Generate focused exercises on weaknesses:
   - Checkmate recognition (1-3 step mates)
   - Middle game tactical mistakes (large score drops)
   - Opening repertoire (future)

The training philosophy is to identify specific weaknesses through engine analysis and create targeted drills, rather than general study.

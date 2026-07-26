AI PROJECT
==========

Overview
--------
This repository contains a small collection of interactive Python GUIs and algorithm implementations for demonstrating pathfinding and search algorithms. It includes:

- A grid-based pathfinding editor and visualizer that supports drawing obstacles, painting per-cell costs, and running multiple algorithms (A*, BFS, DFS, Greedy Best-First, UCS, IDA*, Hill Climbing, Beam Search).
- 8-puzzle and 15-puzzle GUIs that demonstrate search algorithms on sliding-tile puzzles.
- A main launcher (`main_gui.py`) to choose which problem GUI to open.

Features
--------
- Live visualization of search exploration using `STATE:` markers.
- Option to run algorithms in-process (import & call) or as a subprocess (shared `grid_runner.py`).
- Per-cell costs on the grid: paint costs with the `cost` tool; higher costs are shown with a blue gradient and can affect cost-sensitive algorithms (UCS, A* variants).
- Final solution path rendered on the grid after a single-algorithm run.
- Performance reporting (nodes expanded, path length, runtime, memory usage). Memory is displayed in KB.
- **Stop/Continue controls**: Click "Stop" to terminate a running algorithm immediately. Pauses animation visualization. Once stopped, algorithms cannot be resumed; start a new solve.
- Dark mode toggle for comfortable viewing in low-light environments.
- Responsive UI with pause-file mechanism for cooperative algorithm termination (no psutil required).

Structure
---------
Top-level files:
- `main_gui.py` - Launcher application to pick which GUI to run (cards for each game).
- `README.md` - (this file)

Folders:
- `Grid/` - Grid editor + pathfinding algorithms and runner.
  - `GUI.py` - Tkinter grid editor and visualizer.
  - `grid_runner.py` - canonical runner used by subprocess mode; emits `STATE:` and `PATH:` lines and prints performance metrics.
  - Algorithm modules: `Astar.py`, `BFS.py`, `UCS.py`, `DFS.py`, `Greedy.py`, `Beem.py`, `IDAstar.py`, `Hillclimping.py`, etc.

- `Graph/` - Graph problem visualizer and algorithms.
  - `GUI.py` - Graph GUI for interactive node/edge visualization and algorithm playback.
  - `_run_gui_headless.py` - headless runner used for automated comparisons and scripted runs.
  - `romania.py` - example graph (Romania road map) used in demos.
  - Algorithm modules: `Astar.py`, `BFS.py`, `DFS.py`, `Greedy.py`, `UCS.py`, `Beem.py`, `IDAstar.py`, `Hillclimping.py`.

- `Maze/` - Maze generation and solving algorithms.
  - `GUI.py` - Tkinter maze visualizer and solver interface.
  - `maze.py`, `mazze.py` - Maze generation and pathfinding utilities.
  - Algorithm modules: `Astar.py`, `BFS.py`, `UCS.py`, `DFS.py`, `Greedy.py`, `Beem.py`, `IDAstar.py`, `Hillclimping.py`, etc.

- `Puzzle 8-type/` - 8-puzzle (3×3 sliding-tile) GUI and algorithms.
  - `GUI.py` - 8-puzzle visualizer and solver.
  - Algorithm modules: `Astar.py`, `BFS.py`, `UCS.py`, `DFS.py`, `Greedy.py`, `Beem.py`, `IDAstar.py`, `Hillclimping.py`, etc.

- `Puzzle 15-type/` - 15-puzzle (4×4 sliding-tile) GUI and algorithms.
  - `GUI.py` - 15-puzzle visualizer with live exploration and comparison modes.
  - Algorithm modules: `Astar.py`, `BFS.py`, `DFS.py`, `Greedy.py`, `UCS.py`, `Hillclimping.py`, `IDAstar.py`, `Beem.py`.
  - Features: Solvability checking, stdin puzzle input, live STATE visualization, Stop/Continue controls.

Quick Start
-----------
Prerequisites:
- Python 3.8+ (Tkinter is required; usually bundled with standard Python on Windows/Mac).

Run the launcher (recommended):
```powershell
python main_gui.py
```
This opens the card-style launcher. Click a card's "Launch" or "Open" button to run the corresponding GUI.

Run the Grid editor directly:
```powershell
python "Grid\GUI.py"
```

Run the Graph GUI directly:
```powershell
python "Graph\GUI.py"
```

Using the Grid editor:
1. Draw obstacles using `Mode = opstacl`.
2. Set Start/Goal either automatically or by enabling "Manual Start/Goal" and selecting `start`/`goal` mode.
3. Set `Mode = cost` and choose a `Cost` value to paint per-cell cost. Costs > 1 appear in blue and are used by cost-aware algorithms.
4. Choose an algorithm and click the corresponding button to run a single algorithm (use the `Delay` spinbox to slow live exploration). Use "Run In-Process" to call local algorithm functions directly.
5. **Stop/Continue buttons**: While an algorithm is solving, click "Stop" to terminate it immediately. The visualization will pause at the current state. Once stopped, you must start a new solve (Continue is for future pause/resume features).
6. After completion the final solution path will be drawn in purple.

Performance comparison:
- Use "Solve & Compare All" to run selected algorithms sequentially and show a performance comparison popup (Nodes, Time, Path, Memory in KB).
- Click "Stop" anytime during comparison to halt all remaining algorithms.

Developer Notes
---------------
- `grid_runner.py` is used in subprocess mode. It accepts optional arguments: `algorithm_name`, `grid` (stringified list), `start`, `goal`, and an optional cost grid (stringified 2D list). It prints `STATE:` lines as it explores and a `PATH:` line with the final path for GUI parsing.
- In-process mode imports `grid_runner.py` directly and calls `run_<algo>` functions. The GUI captures stdout and highlights `STATE:` outputs.
- Memory measurement uses `tracemalloc` and is reported in KB by the GUI.

Stop/Pause Mechanism
--------------------
- When you click "Stop", the GUI creates a `STOP_FILE` in the system temp directory and passes its path to the algorithm subprocess via the `STOP_FILE` environment variable.
- Each algorithm checks for this file at the start of its main loop using `_check_stop()`. If the file exists, the algorithm raises `SystemExit` and terminates immediately.
- All algorithms include `_sleep_with_pause_check()` which checks the pause file every 10ms during sleep operations, ensuring responsive pause detection even during long-running operations.
- The monitoring loop in the GUI also attempts to terminate the subprocess via `proc.terminate()` or `psutil.terminate()` if available.
- This hybrid approach (file-based + subprocess termination) ensures Stop works reliably across all platforms without external dependencies.

Files of interest
-----------------
- `Grid/GUI.py` - main interactive editor for grids.
- `Grid/grid_runner.py` - canonical runner (subprocess) and in-process function map.
- `main_gui.py` - launcher UI.
- `Grid/*.py`, `Puzzle 8-type/*.py`, `Puzzle 15-type/*.py` - algorithm implementations (A*, BFS, UCS, DFS, Greedy, Beam, IDA*, Hill Climbing).

Using the 8-Puzzle GUI:
-----------------------
The 8-puzzle solver works with sliding-tile puzzles (3x3 grid with one blank):
1. Click "Generate Puzzle" to create a random solvable puzzle.
2. Click on tiles adjacent to the blank to manually arrange the puzzle (optional).
3. Select algorithms to run in the checkboxes.
4. Click individual algorithm buttons to run a single solver and see live visualization.
5. Click "Solve & Compare Selected" to run all checked algorithms sequentially.
6. Use "Stop" to terminate any running solver immediately.
7. View results with node count, path length, time, and memory usage in KB.
8. Click "Show Performance Graph" to compare algorithms visually.

Using the 15-Puzzle GUI:
------------------------
The 15-puzzle solver works with sliding-tile puzzles (4x4 grid with one blank):
1. Click "Generate Puzzle" to create a random solvable puzzle.
2. Click on tiles adjacent to the blank to manually arrange the puzzle (optional).
3. Select algorithms to run using the checkboxes on the right.
4. **Run Individual Algorithm**: Click any algorithm button (A*, BFS, DFS, Greedy, UCS, Hill Climbing, IDA*, Beem) to watch live exploration.
5. **Solve & Compare Selected**: Runs all checked algorithms and shows comparison metrics.
6. **Stop Button**: Terminates the currently running algorithm immediately. Visualization freezes at current state.
7. View detailed results including:
   - Nodes expanded during search
   - Path length (number of moves to solve)
   - Execution time
   - Memory usage in KB
   - Solution trace showing final move sequence (up to 25 steps displayed)
8. **Best Algorithm**: Shows which algorithm solved the puzzle with the fewest nodes expanded.

Using the Maze GUI:
-------------------
The maze solver generates and solves mazes using various pathfinding algorithms:
1. Click "Generate Maze" to create a random maze using maze generation algorithms.
2. Set the maze size (rows × columns) before generation.
3. The maze displays walls (black), paths (white), start (green), goal (red), and explored nodes (light colors).
4. Select algorithms to compare (A*, BFS, DFS, Greedy, UCS, Hill Climbing, IDA*, Beem).
5. Click individual algorithm buttons to see live exploration in the maze.
6. **Solve & Compare Selected**: Runs all checked algorithms and compares performance.
7. **Stop Button**: Terminates maze solving immediately.
8. Results show:
   - Nodes explored (lower is better - means efficient pathfinding)
   - Path length (total steps from start to goal)
   - Execution time
   - Memory usage in KB
9. **Performance Graph**: Visual comparison of all algorithms on the current maze.
10. The final solution path is highlighted in purple/magenta on the maze.

Troubleshooting
---------------
- If the GUI fails to start, confirm `tkinter` is available: run `python -c "import tkinter; print('tk ok')"`.
- If subprocess runs fail, check file paths and ensure `python` (same interpreter) is used by the launcher.
- If cost painting doesn't appear: ensure `Mode` is set to `cost`, paint cells, then call `draw_grid` by resizing or clicking to force refresh.
- If Stop button doesn't work: ensure all algorithm files have the `_check_stop()` function. Check for any hanging subprocesses with system task manager.
- If maze doesn't generate: try reducing the maze size or checking available disk space for temporary files.
- If 15-puzzle shows "unsolvable": the generated puzzle was truly unsolvable (odd number of inversions for 4×4 grids). Try generating a new puzzle.
- Memory shows as "N/A": ensure psutil is not required (file-based stop mechanism should work without it); check system permissions.

Contributing
------------
- Add or improve algorithm implementations in the respective folders.
- Keep `grid_runner.py` contract (print `STATE:` during exploration, `PATH:` after completion, and performance lines) so the GUI continues to work.
- For new algorithms: implement `_check_stop()` and `_maybe_pause()` checks in main loops for Stop button compatibility.
- Use `STATE:{state_list}` output format for live visualization in GUIs.

System Requirements
-------------------
- **Python**: 3.8 or later
- **Dependencies**: 
  - `tkinter` (usually bundled with Python on Windows/Mac; install via `sudo apt install python3-tk` on Linux)
  - `psutil` (optional, for enhanced process control; the application works without it)
- **OS**: Windows, macOS, or Linux
- **Display**: Minimum 1400×900 resolution recommended for full GUI experience

Recent Updates
--------------
### Version 2.0 (December 2025)
- **Implemented reliable Stop button** with file-based cooperative termination mechanism:
  - Added `STOP_FILE` environment variable signaling to all algorithms.
  - All algorithms check `_check_stop()` at main loop entry to detect and exit immediately.
  - Fixed A* and other algorithms not responding to Stop button.
  - Stop now terminates algorithms completely (not just pausing).
  
- **Enhanced responsiveness**:
  - Reduced monitoring loop sleep from 50ms to 20ms.
  - Added `_sleep_with_pause_check()` for 10ms pause detection during sleep operations.
  - Stop signal file is flushed to disk with `os.fsync()` for instant detection.
  
- **15-puzzle improvements**:
  - Standardized solvability checking (correct blank-row-from-bottom rules).
  - All algorithms now accept stdin puzzle input.
  - Live STATE visualization with formatted 4×4 grid display in trace window.
  - Fixed tracing to show full solution paths with move counts.
  
- **UI/UX enhancements**:
  - Dark mode toggle support.
  - Memory reporting in KB (more readable than bytes).
  - Improved performance graph with normalized metrics.
  - Better button layout and responsiveness.

- **Maze support** (feature complete):
  - Maze generation and visualization.
  - All pathfinding algorithms compatible.
  - Performance comparison across algorithms.

Known Limitations
-----------------
- **Hill Climbing**: May reach local optima and report "Unsolved" for puzzles requiring global search.
- **IDA***: Recursive implementation may hit stack limits on very deep solutions.
- **Memory tracking**: Requires process introspection (best effort, may vary by OS).
- **Maze generation**: Very large mazes (>200×200) may be slow to generate and solve.
- **15-puzzle solvability**: Half of all random 15-puzzle configurations are mathematically unsolvable (due to permutation parity). The GUI correctly identifies these.

## Contributors

- Jana Elhadidy
- Amr Maarouf
- Mostafa Shehata
- Ayatullah Mohamed
- Omar Hussein
- Hoor Amir
- Mohamed Elaraby
- Yomna Ayman
- Farah Elsaid

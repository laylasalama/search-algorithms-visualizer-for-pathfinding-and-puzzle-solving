# Maze Solver GUI - Visual Algorithm Comparison

A comprehensive GUI application for generating mazes and comparing pathfinding algorithms with real-time visualization.

## Features

### 🎨 Three Interactive Windows:

1. **Main Window - Maze Generation & Menu**
   - Live animation of 50×50 maze generation using DFS algorithm
   - Click to set start position (green) and goal position (red)
   - Generate new mazes at any time
   - Button to open the comparison window

2. **Comparison Window - Algorithm Performance**
   - Run individual algorithms or all at once
   - Compare metrics:
     - Execution time
     - Memory usage
     - Number of nodes expanded
     - Solution path length
     - Success/failure indicator
   - Click algorithm buttons to run and visualize solutions

3. **Visualization Window - Real-time Algorithm Simulation**
   - Play/Pause/Step controls for algorithm execution
   - Speed adjustment (1x to 50x)
   - Color-coded visualization:
     - **Green**: Start position
     - **Red**: Goal position
     - **Yellow**: Solution path
     - **Light Blue**: Visited nodes
   - Live statistics panel showing:
     - Algorithm name
     - Total execution time
     - Memory consumption
     - Nodes expanded
     - Path length
     - Success status

## Implemented Algorithms

1. **BFS (Breadth-First Search)** - Explores level by level
2. **DFS (Depth-First Search)** - Explores deeply first
3. **UCS (Uniform Cost Search)** - Optimizes by cost
4. **Greedy Best-First** - Uses Manhattan distance heuristic
5. **A* Search** - Combines g-cost and heuristic
6. **IDA* (Iterative Deepening A*)** - Memory-efficient variant
7. **Hill Climbing** - Greedy local search
8. **Beam Search** - Limited breadth-first with beam width

## Installation

1. Install Python 3.7+
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies:
- `tkinter` (usually included with Python)
- `psutil` (for memory monitoring)

## Usage

Run the application:
```bash
python maze_gui.py
```

### Step-by-Step Guide:

1. **Generate Maze**
   - The main window opens with automatic maze generation
   - Watch the DFS algorithm carve out paths in real-time

2. **Set Start and Goal**
   - Click on any cell to set it as the start (turns green)
   - Click another cell to set it as the goal (turns red)
   - To reset, click again on the start cell

3. **Compare Algorithms**
   - Click "Compare Algorithms" button
   - Click individual algorithm buttons to test them
   - Or click "Run All Algorithms" to execute all at once

4. **View Results**
   - Results table shows performance metrics for each algorithm
   - Click "✓" or "✗" in the comparison window to visualize successful solutions

5. **Visualize Algorithm**
   - Controls at the bottom of the visualization window:
     - **Play**: Start the animation
     - **Pause**: Pause the animation
     - **Reset**: Return to the beginning
     - **Step**: Move one step forward manually
     - **Speed Slider**: Adjust animation speed (1-50x)

## Performance Metrics Explained

- **Time (s)**: Wall-clock time to find a solution or exhaust search space
- **Memory (MB)**: Peak memory usage above baseline during execution
- **Nodes Expanded**: Number of nodes explored during search
- **Path Length**: Number of steps in the solution path
- **Success**: Whether the algorithm found a valid path (✓/✗)

## File Structure

```
maze/
├── maze.py                 # Original maze code (reference)
├── maze_gui.py            # Main GUI application
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## How It Works

### Maze Generation
- Uses Depth-First Search (DFS) with backtracking
- Generates perfect mazes (every cell reachable, no cycles)
- Animation shows the carving process in real-time

### Search Algorithms
- Each algorithm is adapted to work with the maze structure
- Walls block movement; only open passages are traversed
- Manhattan distance is the primary heuristic for informed search

### Memory Tracking
- Baseline memory captured at algorithm start
- Peak memory calculated from process memory info
- Useful for comparing space complexity

## Customization

You can modify the maze size by editing the `MazeGenerationWindow` initialization:

```python
app = MazeGenerationWindow(root, width=50, height=50)  # Change 50 to desired size
```

Adjust visualization parameters:
```python
CELL_SIZE = 10  # Cell size in pixels
WALL_COLOR = "black"
PATH_COLOR = "yellow"
VISITED_COLOR = "lightblue"
```

## Troubleshooting

**Problem**: GUI doesn't appear
- Solution: Ensure tkinter is installed (`pip install tk`)

**Problem**: Slow animation on large mazes
- Solution: Reduce maze size or increase CELL_SIZE

**Problem**: Memory errors
- Solution: Close other applications, reduce maze size

**Problem**: Algorithm takes too long
- Solution: The visualization includes real-time rendering; pause it or increase speed

## Performance Tips

1. **For faster comparison**: Increase speed slider in visualization window
2. **For better analysis**: Run algorithms sequentially (one at a time)
3. **For detailed observation**: Use Step button and watch node-by-node exploration
4. **For statistical data**: Results persist in comparison window for analysis

## Algorithm Characteristics

| Algorithm | Time Complexity | Space Complexity | Optimal | Complete |
|-----------|-----------------|------------------|---------|----------|
| BFS       | O(V + E)        | O(V)            | ✓       | ✓        |
| DFS       | O(V + E)        | O(h)            | ✗       | ✓        |
| UCS       | O(E log V)      | O(V)            | ✓       | ✓        |
| Greedy    | O(E log V)      | O(V)            | ✗       | ✗        |
| A*        | O(E log V)      | O(V)            | ✓       | ✓        |
| IDA*      | O(V)            | O(h)            | ✓       | ✓        |
| Hill      | O(E)            | O(1)            | ✗       | ✗        |
| Beam      | O(b × w)        | O(b × w)        | ✗       | ✗        |

import random
import os
import time

# ======================== DIRECTIONS ==========================
# All possible move directions: vertical, horizontal, and diagonal
DIRECTIONS = [
    (-1, 0),(1, 0), (0, 1), (0, -1),
    (-1, 1), (-1, -1), (1, 1), (1, -1)
]

# ======================== GRID FUNCTIONS =======================
# Get all valid neighbors for a node (not walls)
def get_neighbors(grid, node):
    r, c = node
    neighbors = []
    n = len(grid)
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        # Check bounds and avoid walls
        if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] != 1:
            neighbors.append((nr, nc))
    return neighbors

# Print the grid to the screen
# S = Start, G = Goal, * = Path, # = Wall, . = Empty cell
def print_grid(grid, start=None, goal=None, path_set=None):
    os.system("cls" if os.name=="nt" else "clear")  # Clear the screen
    n = len(grid)
    for r in range(n):
        row_str = ""
        for c in range(n):
            if (r,c) == start:
                row_str += " S "
            elif (r,c) == goal:
                row_str += " G "
            elif path_set and (r,c) in path_set:
                row_str += " * "
            elif grid[r][c] == 1:
                row_str += " # "
            else:
                row_str += " . "
        print(row_str)
    print()
    time.sleep(0.05)  # Pause to visualize the path step by step

# Create an empty n x n grid
def create_grid(n):
    return [[0]*n for _ in range(n)]

# Create a cost grid with random costs (used for algorithms like Hill Climbing)
def create_cost_grid(grid):
    n = len(grid)
    cost_grid = [[0]*n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if grid[r][c]==1:
                cost_grid[r][c]=None  # Walls have no cost
            else:
                cost_grid[r][c]=random.randint(1,9)  # Random cost between 1-9
    return cost_grid

# ====================== USER INPUT FUNCTIONS ==================
# Get a valid integer from the user
def get_int(prompt, min_value=None):
    while True:
        try:
            value = int(input(prompt))
            if min_value is not None and value < min_value:
                print(f"Value must be >= {min_value}")
                continue
            return value
        except:
            print("Enter a valid number")

# Add walls to the grid
def add_walls(grid):
    n = len(grid)
    print("Enter wall positions (row column), type 'done' to finish:")
    while True:
        s = input("Wall: ").strip()
        if s.lower() == "done":
            break
        parts = s.split()
        if len(parts)!=2:
            print("Enter 2 numbers")
            continue
        try:
            r,c = map(int,parts)
        except:
            print("Invalid numbers")
            continue
        if not (0<=r<n and 0<=c<n):
            print("Out of range")
            continue
        grid[r][c]=1
        print_grid(grid)

# Get a valid point from the user (start or goal)
def get_point(name,n):
    while True:
        s = input(f"Enter {name} (row column): ").split()
        if len(s)!=2:
            print("Enter 2 numbers")
            continue
        try:
            r,c = map(int,s)
        except:
            print("Invalid numbers")
            continue
        if not (0<=r<n and 0<=c<n):
            print("Out of range")
            continue
        return (r,c)

# ======================== HILL CLIMBING ========================
# Run Hill Climbing algorithm
def run_hill_climbing(grid, start, goal, max_steps=200):
    path = [start]  # Store the path
    current = start
    # Heuristic: Manhattan distance to the goal
    current_h = abs(start[0]-goal[0]) + abs(start[1]-goal[1])
    total_cost = cost_grid[start[0]][start[1]]  # Add cost of starting cell

    print_grid(grid, start, goal, set(path))

    for _ in range(max_steps):
        neighbors = get_neighbors(grid, current)
        if not neighbors:
            break  # No possible moves, stuck

        # Choose the neighbor with the lowest heuristic (closest to goal)
        best = min(neighbors, key=lambda s: abs(s[0]-goal[0]) + abs(s[1]-goal[1]))
        best_h = abs(best[0]-goal[0]) + abs(best[1]-goal[1])

        if best_h >= current_h:
            break  # Reached a local maximum

        current = best
        current_h = best_h
        total_cost += cost_grid[current[0]][current[1]]  # Add cost of the cell
        path.append(current)

        print_grid(grid, start, goal, set(path))

        if current == goal:
            break

    reached = current == goal
    if not reached:
        print("\n  Algorithm reached local maximum (could not reach the goal)")
    return path, reached, total_cost

# ========================== TIME MEASUREMENT ===================
# Measure execution time of any function
def measure_time(func, *args):
    start_time = time.time()
    result = func(*args)
    end_time = time.time()
    return result, end_time-start_time

# ========================== ALGORITHMS COMPARISON =============
def compare_algorithms(grid, cost_grid, start, goal, algorithm_choice):
    algorithms = {
        7: ("Hill Climbing", run_hill_climbing)
    }
    if algorithm_choice not in algorithms:
        print("Algorithm not implemented yet.")
        return
    name, algo = algorithms[algorithm_choice]
    print(f"\n→ Running {name} ...")

    path, reached, total_cost = algo(grid, start, goal)

    print(f"\nPath Length: {len(path)}")
    print(f"Reached Goal: {reached}")
    print(f"Total Cost: {total_cost}")
    print(f"Path: {path}")

# ========================== INPUT PROBLEM ======================
def input_problem():
    number = get_int("Enter grid size: ", min_value=2)
    grid = create_grid(number)
    print("\n--- Add Walls ---")
    add_walls(grid)
    print("\n--- Adding Random Costs ---")
    global cost_grid
    cost_grid = create_cost_grid(grid)
    print("\n--- Start & Goal ---")
    start = get_point("Start", number)
    goal = get_point("Goal", number)
    print_grid(grid, start, goal)
    algorithm = 7  # Hill Climbing
    return grid, cost_grid, start, goal, algorithm

# ========================== MAIN ==============================
if __name__=="__main__":
    grid, cost_grid, start, goal, algorithm = input_problem()
    compare_algorithms(grid, cost_grid, start, goal, algorithm)
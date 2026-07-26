#=========================================================================#
#=======================grid of bfs=======================================#
#=========================================================================#
import random                             
from collections import deque              
import os                                  
import time                                 

# 8 directions (horizontal, vertical, diagonal)
DIRECTIONS = [
      (-1, 0),(1, 0), (0, 1), (0, -1), 
      (-1, 1), (-1, -1), (1, 1), (1, -1)  
]

#========================= BFS with visualization ==========================
def BFS_visual(grid, start, goal, delay=0.15, timeout=10):
    start_time = time.time()
    visited = set([start])
    parent = {start: None}
    queue = deque([start])
    nodes = 0

    while queue:
        if time.time() - start_time > timeout:
            return None, "TIMEOUT"

        node = queue.popleft()
        nodes += 1

        current_path = reconstruct_path(parent, start, node) if node in parent else [node]

        # Visualization
        elapsed = time.time() - start_time
        os.system("cls" if os.name == "nt" else "clear")
        print("BFS Visualization:")
        print(f"Nodes Expanded: {nodes}")
        print(f"Elapsed Time: {elapsed:.4f} sec\n")
        print_grid_with_path(grid, start, goal, current_path)
        time.sleep(delay)

        if node == goal:
            return current_path, "FOUND"

        for neighbor in get_neighbors(grid, node):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)

    return None, "NO_PATH"


def run_bfs(grid, cost_grid, start, goal):
    """BFS wrapper compatible with grid_runner API.
    Emits 'STATE:(r, c)' lines and returns (path, nodes).
    """
    from collections import deque
    visited = set([start])
    parent = {start: None}
    queue = deque([start])
    nodes = 0
    start_time = time.time()
    timeout = 60.0

    while queue:
        if time.time() - start_time > timeout:
            return None, nodes

        node = queue.popleft()
        nodes += 1
        # Emit STATE marker for GUI visualization
        try:
            print(f"STATE:{node}")
        except:
            pass

        if node == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, node):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)

    return None, nodes

#========================= Helper Functions ==========================
def get_neighbors(grid, node):
    r, c = node
    neighbors = []
    n = len(grid)
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] != 1:
            neighbors.append((nr, nc))
    return neighbors

def reconstruct_path(parent, start, goal):
    if parent is None or goal not in parent:
        return None
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path

def print_grid(grid,start = None, goal = None):
    os.system("cls" if os.name == "nt" else "clear")
    print("\nThe Grid :")
    number = len(grid)
    for row in range(number):
        row_string_shape= ""
        for column in range(number):
            if (start is not None) and (row, column) == start:
                row_string_shape += " S  "
            elif (goal is not None) and (row, column) == goal:
                row_string_shape += " G  "
            elif grid[row][column] == 1:
                row_string_shape += " #  "
            else:
                row_string_shape += " .  "
        print(row_string_shape)
    print()

def print_grid_with_path(grid, start, goal, path):
    print("\nGrid With Path:")
    number = len(grid)
    for row in range(number):
        row_string = ""
        for colum in range(number):
            if (row, colum) == start:
                row_string += " S  "
            elif (row, colum) == goal:
                row_string += " G  "
            elif grid[row][colum] == 1:
                row_string += " #  "
            elif path and (row, colum) in path:
                row_string += " -  "
            else:
                row_string += " .  "
        print(row_string)
    print()

def get_int(prompt, minimum_value=None):
    while True:
        text = input(prompt)
        try:
            value = int(text)
        except ValueError:
            print("Enter a correct value")
            continue
        if minimum_value is not None and value < minimum_value:
            print(f"The value can't be less than {minimum_value}.")
            continue
        return value

def create_grid(number):
    return [[0] * number for _ in range(number)]

def create_cost_grid(grid):
    number = len(grid)
    cost_grid = [[0]*number for _ in range(number)]
    for r in range(number):
        for c in range(number):
            cost_grid[r][c] = None if grid[r][c]==1 else random.randint(1,9)
    return cost_grid

def add_walls(grid):
    number = len(grid)
    print("\nEnter wall positions (row column). Type 'done' when finished.")
    while True:
        start = input("Wall: ").strip()
        if start.lower() == "done":
            break
        parts = start.split()
        if len(parts) != 2:
            print("Please enter 2 numbers (row column).")
            continue
        try:
            row, column = map(int, parts)
            row -=1
            column -=1
        except ValueError:
            print("Invalid value.")
            continue
        if not (0 <= row < number and 0 <= column < number):
            print("Out of range.")
            continue
        grid[row][column] = 1
        print_grid(grid)

def get_point(name, number):
    while True:
        start = input(f"Enter {name} (row column): ").split()
        if len(start) != 2:
            print("You must enter 2 numbers.")
            continue
        try:
            row, column = map(int, start)
            row -= 1
            column -= 1
        except ValueError:
            print("Invalid value.")
            continue
        if not (0 <= row < number and 0 <= column < number):
            print("Out of range.")
            continue
        return (row, column)

def choose_algorithm():
    options = {
        "1": "BFS",
    }
    print("\nChoose Algorithm :")
    for key, value in options.items():
        print(f"{key}) {value}")
    while True:
        choice = input("Choose one: ").strip()
        if choice in options:
            return int(choice)
        print("Invalid choice.")

def input_problem():
    number = get_int("Enter grid size: ", minimum_value=2)
    grid = create_grid(number)
    print("\n--- Add Walls ---")
    add_walls(grid)
    print("\n--- Adding Random Costs ---")
    cost_grid = create_cost_grid(grid)
    print("\n--- Start & Goal ---")
    start = get_point("Start", number)
    goal = get_point("Goal", number)
    print_grid(grid, start, goal)
    algorithm = choose_algorithm()
    return grid, cost_grid, start, goal, algorithm

#======================== MAIN ===============================
if __name__ == "__main__":
    import sys
    # If script is invoked with arguments, run in non-interactive mode
    # Expected argv: [script, algo_name, grid_str, start, goal, cost_grid?]
    if len(sys.argv) >= 5:
        algo_name = sys.argv[1]
        grid_str = sys.argv[2]
        start = eval(sys.argv[3])
        goal = eval(sys.argv[4])
        grid = eval(grid_str)
        # optional cost grid passed as 6th argument (argv[5])
        cost_grid = [[1 for _ in range(len(grid))] for _ in range(len(grid))]
        if len(sys.argv) >= 6:
            try:
                cost_grid = eval(sys.argv[5])
            except Exception:
                pass
        # Use the in-process wrapper which emits STATE: lines
        run_bfs(grid, cost_grid, start, goal)
    else:
        # fallback to interactive mode
        grid, cost_grid, start, goal, algorithm = input_problem()

        if algorithm == 1:
            path, status = BFS_visual(grid, start, goal, delay=0.25, timeout=10)
            if status=="FOUND":
                print("\nBFS Found a Path!")
                print_grid_with_path(grid, start, goal, path)
                print(f"Path Length: {len(path)}")
            elif status=="TIMEOUT":
                print("\nBFS stopped: exceeded timeout.")
            else:
                print("\nBFS: No Path Found.")
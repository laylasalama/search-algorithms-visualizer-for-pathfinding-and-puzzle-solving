import random                              #To import random costs 
from heapq import heappush, heappop        #priority queue for Greedy Algorithm
from collections import deque              #for 2 di arrays (BFS)
import os                                  #clear terminal screen 
import time                                 #measure time for algorithms

#==============================================================================================
#================= 8 directions for movement horizontal ,diagonal ,vertical====================
#================= we use this for all search algorithm when exploring neighbors===============
#==============================================================================================
DIRECTIONS = [                                      # 8 directions
      (-1, 0),(1, 0), (0, 1), (0, -1), 
      (-1, 1), (-1, -1), (1, 1), (1, -1)  
]

#=============================================================================
#=========================ALGORITHMS==========================================
#=============================================================================

#--------------EXAMPLE :BFS------------------------- 
def BFS(grid, start, goal):
    """
    Returns parent dict (like before). Additionally performs step-by-step visualization
    similar to IDA*: shows current path from start to current node, elapsed time, nodes expanded.
    """
    queue = deque([start])
    visited = set([start])
    parent = {start: None}

    nodes = 0
    start_time = time.time()
    delay = 0.15   # visualization speed (seconds) - same feel as IDA*

    while queue:
        node = queue.popleft()
        nodes += 1

        # build current path to display (if reachable via parent)
        current_path = reconstruct_path(parent, start, node) if parent is not None else None

        # ========== VISUALIZATION ==============
        elapsed = time.time() - start_time
        os.system("cls" if os.name == "nt" else "clear")
        print("BFS Visualization:")
        print(f"Expanded Nodes: {nodes}")
        print(f"Elapsed Time: {elapsed:.4f} sec\n")
        # render the grid using the current path (mimic IDA* style)
        print_grid_with_path(grid, start, goal, current_path)
        time.sleep(delay)
        # =======================================

        if node == goal:
            return parent

        for n in get_neighbors(grid, node):
            if n not in visited:
                visited.add(n)
                parent[n] = node
                queue.append(n)

    return None


def get_neighbors(grid, node):
    r, c = node          
    neighbors = []        
    n = len(grid)        
    for dr, dc in DIRECTIONS:        
        nr, nc = r + dr, c + dc       
        if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] != 1: 
            neighbors.append((nr, nc))    
    return neighbors

#======================A* ALGORITHM=============================
def A_star(grid, start, goal, delay=0.15, timeout=10):
 
    start_time = time.time()
    visited = set()
    parent = {start: None}
    g_costs = {start: 0}

    frontier = []
    heappush(frontier, (heuristic(start, goal), start))  # f = g + h

    nodes = 0

    while frontier:
        if time.time() - start_time > timeout:
            return None, "TIMEOUT"

        f, current = heappop(frontier)

        if current in visited:
            continue
        visited.add(current)
        nodes += 1

        # Reconstruct current path for visualization
        current_path = reconstruct_path(parent, start, current)

        # IDA*-style visualization
        elapsed = time.time() - start_time
        os.system("cls" if os.name == "nt" else "clear")
        print("A* Search Visualization")
        print(f"Nodes Expanded: {nodes}")
        print(f"Elapsed Time: {elapsed:.4f} seconds\n")
        print_grid_with_path(grid, start, goal, current_path)
        time.sleep(delay)

        if current == goal:
            path = current_path
            return path, "FOUND"

        for nxt in get_neighbors(grid, current):
            tentative_g = g_costs[current] + 1  # uniform cost = 1 per move
            if nxt not in g_costs or tentative_g < g_costs[nxt]:
                g_costs[nxt] = tentative_g
                f_cost = tentative_g + heuristic(nxt, goal)
                parent[nxt] = current
                heappush(frontier, (f_cost, nxt))

    return None, "NO_PATH"

#===============================================================
#====================== RECONSTRUCT PATH =======================
#===============================================================
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

#=============================================================================
#============= print grid with walls(#) & empty grid(.)=======================
#=============================================================================
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

#==================================================================
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

#===============================================================
def create_grid(number):
    return [[0] * number for _ in range(number)]

#===============================================================
def create_cost_grid(grid):
    number = len(grid)
    cost_grid = [[0] * number for _ in range(number)]

    for row in range(number):
        for column in range(number):
            if grid[row][column] == 1:
                cost_grid[row][column] = None  
            else:
                cost_grid[row][column] = random.randint(1, 9)  

    return cost_grid

#===============================================================
def measure_time(func, *arguments):
    start = time.time()
    result = func(*arguments)    
    end = time.time()
    return result, end - start

#===============================================================
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
            row -= 1  
            column -= 1  
        except ValueError:
            print("Invalid value.")
            continue

        if not (0 <= row < number and 0 <= column < number):
            print("Out of range.")
            continue

        grid[row][column] = 1

        print_grid(grid)

#===============================================================
def print_grid_with_path(grid, start, goal, path):  
    """
    path can be a list or a set — membership checks work for both.
    This draws S, G, walls(#) and '-' for path cells.
    """
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

#=================================================================
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

#===============================================================
def choose_algorithm():
    options = {
        "1": "BFS",
        "2": "DFS",
        "3": "UCS",
        "4": "Greedy",
        "5": "A*",
        "6": "IDA*",
        "7": "Hill Climbing",
        "8": "Beam",
    }

    print("\nChoose Algorithm :")
    for key, value in options.items():
        print(f"{key}) {value}")

    while True:
        choice = input("Choose one: ").strip()
        if choice in options:
            return int(choice)
        print("Invalid choice.")

#===============================================================
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
    

#===============================================================
#============== GREEDY BEST-FIRST  =====================
#===============================================================
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def greedy_best_first(grid, start, goal, delay=0.15, timeout=10):
    """
    Returns (path, status) where status in {"FOUND","TIMEOUT","NO_PATH"}.
    Performs IDA*-like visualization: shows current path from start to current node,
    elapsed time and expanded nodes; stops if exceeds timeout (seconds).
    """
    start_time = time.time()
    visited = set()
    parent = {start: None}

    frontier = []
    heappush(frontier, (heuristic(start, goal), start))

    nodes = 0
    while frontier:

        if time.time() - start_time > timeout:
            return None, "TIMEOUT"

        h, current = heappop(frontier)

        if current in visited:
            continue
        visited.add(current)
        nodes += 1

        # build current path to current
        current_path = reconstruct_path(parent, start, current) if current in parent else [current]

        # Visualization (IDA*-style)
        elapsed = time.time() - start_time
        os.system("cls" if os.name == "nt" else "clear")
        print("Greedy Best-First Search Visualization")
        print(f"Nodes Expanded: {nodes}")
        print(f"Elapsed Time: {elapsed:.4f} seconds\n")
        print_grid_with_path(grid, start, goal, current_path)
        time.sleep(delay)

        if current == goal:
            path = current_path
            return path, "FOUND"

        for nxt in get_neighbors(grid, current):
            if nxt not in visited and nxt not in [n for _, n in frontier]:
                parent[nxt] = current
                heappush(frontier, (heuristic(nxt, goal), nxt))

    return None, "NO_PATH"


#===============================================================
#================== COMPARE ALGORITHMS ==========================
#===============================================================
def compare_algorithms(grid, cost_grid, start, goal):
    """
    Runs automated comparison for BFS and Greedy.
    Both algorithms will show their step-by-step visualization while running.
    For BFS we time the function (it returns parent dict). For Greedy the function
    returns (path, status) and already visualizes while running.
    """
    algorithms = {
        "BFS": BFS,
        "Greedy": greedy_best_first,
    }

    print("\n================ ALGORITHMS COMPARISON ================")

    for name, algorithm in algorithms.items():
        print(f"\n→ Testing {name} ...")

        if name == "BFS":
            # BFS returns parent dict and does visualization internally.
            start_t = time.time()
            parent = algorithm(grid, start, goal)
            elapsed = time.time() - start_t
            path = reconstruct_path(parent, start, goal) if parent else None

        else:  # Greedy
            start_t = time.time()
            path, status = algorithm(grid, start, goal, delay=0.25, timeout=10)  # fast mode (delay=0) for comparison
            elapsed = time.time() - start_t
            # status may be "FOUND","TIMEOUT","NO_PATH"

        print("\nOriginal Grid:")
        print_grid(grid, start, goal)

        if path:
            print("\nPath Grid:")
            print_grid_with_path(grid, start, goal, path)

        print(f"Time: {elapsed:.6f} sec")
        if path:
            print(f"Path Length: {len(path)}")
            print(f"Path: {path}")
        else:
            print("Path Not Found")

    print("\n========================================================\n")


#================================================================
#================== main start program===========================
#================================================================
if __name__ == "__main__":

    grid, cost_grid, start, goal, algorithm = input_problem()

    # ==========================================================
    # =============== RUN SELECTED ALGORITHM ====================
    # ==========================================================

    if algorithm == 1:
        result, elapsed = measure_time(BFS, grid, start, goal)
        print(f"\nBFS Execution Time: {elapsed:.6f} seconds")

        path = reconstruct_path(result, start, goal)
        if path:
            print("\nFinal Path Grid:")
            print_grid_with_path(grid, start, goal, path)
        else:
            print("No Path Found.")

    elif algorithm == 4:

        print("\nRunning Greedy Best-First Search (10 sec timeout)...")

        path, status = greedy_best_first(grid, start, goal, delay=0.25, timeout=10)

        if status == "TIMEOUT":
            print("\nGreedy stopped: exceeded 10 seconds.")
        elif status == "FOUND":
            print("\nGreedy Found a Path!")
            print_grid_with_path(grid, start, goal, path)
            print(f"Path Length: {len(path)}")
        else:
            print("\nGreedy: No Path Found.")

    elif algorithm == 5:  # A*
        print("\nRunning A* Search (10 sec timeout)...")
        path, status = A_star(grid, start, goal, delay=0.25, timeout=10)

        if status == "TIMEOUT":
            print("\nA* stopped: exceeded 10 seconds.")
        elif status == "FOUND":
            print("\nA* Found a Path!")
            print_grid_with_path(grid, start, goal, path)
            print(f"Path Length: {len(path)}")
        else:
            print("\nA*: No Path Found.")

    # ==========================================================
    # ================ COMPARISON TABLE  ==================
    # ==========================================================

    print("\n================= COMPARISON TABLE =================\n")
    print("{:<20} {:<20} {:<20}".format("Algorithm", "Time (sec)", "Path Length"))
    print("-" * 60)

    # BFS row (if just ran BFS)
    if algorithm == 1:
        bfs_time = elapsed
        bfs_path = reconstruct_path(result, start, goal)
        bfs_length = len(bfs_path) if bfs_path else "NOT FOUND"
        print("{:<20} {:<20.6f} {:<20}".format("BFS", bfs_time, bfs_length))

    # Greedy row (if just ran Greedy)
    if algorithm == 4:
        greedy_time = 0 if status != "TIMEOUT" else 10
        greedy_length = len(path) if path else "NOT FOUND"
        print("{:<20} {:<20} {:<20}".format("Greedy", greedy_time, greedy_length))

    if algorithm == 5:
        A_star_time = elapsed
        A_star_length = len(path) if path else "NOT FOUND"
        print("{:<20} {:<20.6f} {:<20}".format("A*", A_star_time, A_star_length))


    print("\n====================================================\n")

    # ==========================================================
    # ============= FULL AUTOMATED COMPARISON ==================
    # ==========================================================

    compare_algorithms(grid, cost_grid, start, goal)

    print("\nInputs:")
    print("Grid Size:", len(grid))
    print("Start:", start)
    print("Goal:", goal)
    print("Algorithm:", algorithm)

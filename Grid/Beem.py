import random                              # To import random costs 
import os                                  # clear terminal screen 
import time                                # measure time for algorithms
from collections import deque

#===========================================================================================
#===================================== BEAM SEARCH =========================================
#===========================================================================================

def beam_search(start, goal, neighbors_fn, heuristic_fn, beam_width, delay=0.3, render_fn=None, timeout=None):
    beam = [(start, [start], heuristic_fn(start, goal))]
    visited = set([start])
    visited_order = []

    start_time = time.time() if timeout is not None else None

    while beam:
        # Visualize current beam and visited nodes
        if render_fn:
            render_fn(beam=[node for node, _, _ in beam], visited=visited)
            time.sleep(delay)

        # Check if goal reached
        for node, path, h in beam:
            if node == goal:
                return {
                    "path": path,
                    "visited_order": visited_order,
                    "visited_count": len(visited_order)
                }

        candidates = []
        for node, path, h in beam:
            visited_order.append(node)

            if timeout is not None and start_time is not None:
                if time.time() - start_time > timeout:
                    return {
                        "timeout": True,
                        "path": None,
                        "visited_order": visited_order,
                        "visited_count": len(visited_order)
                    }

            for child, cost in neighbors_fn(node):
                if child not in visited:
                    visited.add(child)
                    new_path = path + [child]
                    new_h = heuristic_fn(child, goal)
                    candidates.append((child, new_path, new_h))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[2])
        beam = candidates[:beam_width]

    return None

#==============================================================================================
#================= 8 directions for movement horizontal ,diagonal ,vertical====================
#================= we use this for all search algorithm when exploring neighbors===============
#==============================================================================================
DIRECTIONS = [
      (-1, 0),(1, 0), (0, 1), (0, -1), 
      (-1, 1), (-1, -1), (1, 1), (1, -1)  
]

#=============================================================================
#=========================ALGORITHMS==========================================
#=============================================================================
#--------------EXAMPLE :BFS------------------------- 
def BFS(grid, start, goal):
    queue = deque([start])
    visited = set([start])
    parent = {start: None}

    while queue:
        node = queue.popleft()

        if node == goal:
            return parent   # return parent to reconstruct path

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
    
#===============================================================
#====================== RECONSTRUCT PATH ========================
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
#=============print start(S) & goal(G) to the grid============================
#============ clear screen every time we index a new wall or point============
#=============================================================================
def print_grid(grid, start=None, goal=None, beam=None, visited=None, path=None):
    os.system("clear")          #clear the last grid
    number = len(grid)
    path_set = set(path) if path else set()
    for r in range(number):
        row_str = ""
        for c in range(number):
            cell = (r, c)
            if cell == start:
                row_str += " S  "
            elif cell == goal:
                row_str += " G  "
            elif path and cell in path_set:
                row_str += " o  "  # path
            elif beam and cell in beam:
                row_str += " *  "  # beam/frontier
            elif visited and cell in visited:
                row_str += " x  "  # visited nodes
            elif grid[r][c] == 1:
                row_str += " #  "  # wall
            else:
                row_str += " .  "
        print(row_str)
    print()

#==================================================================
#=============== read a valid integer from the user ==============================
#=============== ensure the input is vaild number & miniumum value================
#==================================================================
def get_int(prompt, min_value=None):
    while True:
        text = input(prompt)
        try:
            value = int(text)
        except ValueError:
            print("Enter a correct value")
            continue

        #validate minimum allowed value
        if min_value is not None and value < min_value:
            print(f"The value can't be less than {min_value}.")
            continue
        return value

#===============================================================
#================== create grid NUMBER × NUMBER=================
#================= 0 is empty cell & 1 is walls ================
#===============================================================
def create_grid(number):
    return [[0] * number for _ in range(number)]

#===============================================================
#======================MEASURE TIME=============================
#===============================================================
def measure_time(func, *arguments):
    start = time.time()
    result = func(*arguments)    #run example algorithm
    end = time.time()
    return result, end - start

#===============================================================
#=========== add walls + update the grid after each add=========
#===============================================================
def add_walls(grid):
    number = len(grid)
    print("\nEnter wall positions (row column). Type 'done' when finished.")

    while True:
        start = input("Wall: ").strip()

        # stop adding walls when the user type "done"
        if start.lower() == "done":
            break

        parts = start.split()
        if len(parts) != 2:
            print("Please enter 2 numbers (row column).")
            continue

        try:
            row, column = map(int, parts)
        except ValueError:
            print("Invalid value.")
            continue
        # ensure walls is inside the grid bounds
        if not (0 <= row < number and 0 <= column < number):
            print("Out of range.")
            continue
        # place wall
        grid[row][column] = 1

        # update the grid display
        print_grid(grid)

# read valid point(start ,goal)
def get_point(name, number):
    while True:
        start = input(f"Enter {name} (row column): ").split()
        if len(start) != 2:
            print("You must enter 2 numbers.")
            continue

        try:
            row, column = map(int, start)
        except ValueError:
            print("Invalid value.")
            continue

        if not (0 <= row < number and 0 <= column < number):
            print("Out of range.")
            continue

        return (row, column)


#=========================================================
#==============collect right input problem================
#=========================================================
def input_problem():
    number = get_int("Enter grid size: ", min_value=2)
    grid = create_grid(number)

    print("\n--- Add Walls ---")
    add_walls(grid)

    print("\n--- Adding Random Costs ---")
    cost_grid = create_cost_grid(grid)
    # draw start and goal on grid
    print("\n--- Start & Goal ---")
    start = get_point("Start", number)
    goal = get_point("Goal", number)
    print_grid(grid, start, goal)
    return grid, cost_grid, start, goal

#================================================================
#==================== cost grid creation ========================
#================================================================
def create_cost_grid(grid):
    n = len(grid)
    cost_grid = [[random.randint(1, 10) for _ in range(n)] for _ in range(n)]
    return cost_grid

#================================================================
#===================== neighbors function =======================
#================================================================
def beam_neighbors_fn(node, grid, cost_grid):
    neighbors = []
    for r, c in get_neighbors(grid, node):
        neighbors.append(((r, c), cost_grid[r][c]))
    return neighbors

#================================================================
#===================== heuristic function =======================
#================================================================
def heuristic_fn(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

#===============================================================
#===================== beam search wrapper =====================
#===============================================================
def run_beam_search(grid, cost_grid, start, goal, beam_width=3):
    return beam_search(
        start=start,
        goal=goal,
        neighbors_fn=lambda n: beam_neighbors_fn(n, grid, cost_grid),
        heuristic_fn=heuristic_fn,
        beam_width=beam_width,
        delay=0.3,
        render_fn=lambda beam, visited: print_grid(grid, start, goal, beam, visited)
    )

#================================================================
#================== main start program===========================
#================================================================
if __name__ == "__main__":
    grid, cost_grid, start, goal = input_problem()
    result = run_beam_search(grid, cost_grid, start, goal)
    print("Result:", result)
    
if result and result.get("path"):
    print("\n--- Final Path Visualization ---")
    print_grid(grid, start, goal, path=result["path"])
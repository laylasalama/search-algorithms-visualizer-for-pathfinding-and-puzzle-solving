import random
import os
import time

# ===============================================================
# DIRECTIONS
# ===============================================================
DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East": (1, 0),
    "West": (-1, 0)
}

OPPOSITE = {"North": "South", "South": "North", "East": "West", "West": "East"}

# ===============================================================
# RENDER MAZE (ASCII)
# ===============================================================
def render_maze(maze, width, hight):
    """Draws the maze as ASCII"""
    out = "+" + "---+" * width + "\n"
    for y in range(hight):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x, y)]
            row1 += "   "
            row1 += " " if cell["East"] == False else "|"
            row2 += "   " if cell["South"] == False else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"
    return out

# ===============================================================
# MAZE GENERATOR (DFS)
# ===============================================================
def generate_maze(width, hight):
    """Generates a random maze using DFS with animation"""
    maze = {(x, y): {"North": True, "South": True, "East": True, "West": True}
            for y in range(hight) for x in range(width)}

    visited = set()
    stack = []

    x, y = random.randint(0, width - 1), random.randint(0, hight - 1)
    visited.add((x, y))
    stack.append((x, y))

    while stack:
        os.system("cls" if os.name == "nt" else "clear")
        print(render_maze(maze, width, hight))
        time.sleep(0.0005)

        x, y = stack[-1]
        neighbors = []

        for d, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < hight and (nx, ny) not in visited:
                neighbors.append((d, nx, ny))

        if neighbors:
            d, nx, ny = random.choice(neighbors)
            maze[(x, y)][d] = False
            maze[(nx, ny)][OPPOSITE[d]] = False
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    return maze

# ===============================================================
# RENDER MAZE WITH PATH
# ===============================================================
def render_maze_with_path(maze, width, hight, path=None, start=None, goal=None):
    """Draws the maze showing path, start, and goal"""
    path_set = set(path) if path else set()
    out = "+" + "---+" * width + "\n"

    for y in range(hight):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x, y)]

            if (x, y) == start:
                row1 += " S "
            elif (x, y) == goal:
                row1 += " G "
            elif (x, y) in path_set:
                row1 += " * "
            else:
                row1 += "   "

            row1 += " " if not cell["East"] else "|"
            row2 += "   " if not cell["South"] else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"
    return out

# ===============================================================
# INPUT START & GOAL
# ===============================================================
def input_start_goal(maze, width, hight):
    """Ask user for start and goal positions"""
    while True:
        try:
            sx, sy = map(int, input("Start (x y): ").split())
            gx, gy = map(int, input("Goal  (x y): ").split())
        except:
            print("Invalid input. Try again.")
            continue
        if not (0 <= sx < width and 0 <= sy < hight): continue
        if not (0 <= gx < width and 0 <= gy < hight): continue
        if (sx, sy) == (gx, gy):
            print("Start and goal cannot be the same. Try again.")
            continue
        return (sx, sy), (gx, gy)

# ===============================================================
# RESULTS TABLE
# ===============================================================
def print_results_table(results):
    """Print a table comparing algorithms"""
    header = f"{'Algorithm':10} | {'Time (s)':>9} | {'Nodes':>8} | {'PathLen':>7} | {'Cost':>6}"
    print(header)
    print("-" * len(header))
    for name, stats in results.items():
        print(f"{name:10} | "
              f"{stats['time']:.6f} | "
              f"{stats['nodes_expanded']:>8} | "
              f"{stats['path_length']:>7} | "
              f"{stats['cost'] if stats['cost'] is not None else 'N/A':>6}")

# ===============================================================
# EMPTY PLACEHOLDER ALGORITHMS
# ===============================================================
def BFS(maze, start, goal): return [], 0, 0
def DFS(maze, start, goal): return [], 0, 0
def UCS(maze, start, goal): return [], 0, 0
def Greedy(maze, start, goal): return [], 0, 0
def A(maze, start, goal): return [], 0, 0
def Hill(maze, start, goal): return [], 0, 0
def Beam(maze, start, goal): return [], 0, 0

# ===============================================================
# UNIVERSAL IDA* TEMPLATE (WITH TIMEOUT)
# ===============================================================
def IDA_star(start_state, goal_test, get_neighbors, heuristic, debug=False):
    """IDA* algorithm with animation and step-by-step path rendering"""
    start_time = time.time()
    threshold = heuristic(start_state)
    path = [start_state]
    nodes_expanded = 0

    def search(g_cost, threshold):
        nonlocal nodes_expanded

        if time.time() - start_time > 10:
            return "TIMEOUT"

        node = path[-1]
        f_cost = g_cost + heuristic(node)

        if f_cost > threshold:
            return f_cost

        if goal_test(node):
            return "FOUND"

        nodes_expanded += 1
        min_threshold = float("inf")

        for neighbor, step_cost in get_neighbors(node):
            if neighbor in path:
                continue

            path.append(neighbor)

            if debug:
                os.system("cls" if os.name == "nt" else "clear")
                print("Searching...\n")
                print(render_maze_with_path(global_maze, global_w, global_h, path))
                time.sleep(0.25)

            result = search(g_cost + step_cost, threshold)

            if result == "FOUND":
                return "FOUND"

            if isinstance(result, (int, float)) and result < min_threshold:
                min_threshold = result

            path.pop()

        return min_threshold

    while True:
        result = search(0, threshold)

        if result == "TIMEOUT":
            return "TIMEOUT", nodes_expanded, None

        if result == "FOUND":
            return path[:], nodes_expanded, len(path) - 1

        if result == float("inf"):
            return None, nodes_expanded, None

        threshold = result

# ===============================================================
# MAZE IDA* HELPERS
# ===============================================================
def maze_heuristic(a, b):
    """Manhattan distance"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def maze_goal_test(n, goal):
    return n == goal

def maze_get_neighbors(node, maze):
    x, y = node
    neighbors = []
    for d, (dx, dy) in DIRECTIONS.items():
        nx, ny = x + dx, y + dy
        if (nx, ny) in maze and maze[(x, y)][d] == False:
            neighbors.append(((nx, ny), 1))
    return neighbors

def IDA(maze, start, goal):
    """Wrapper for IDA* specific to maze"""
    global global_maze, global_w, global_h
    global_maze = maze
    global_w = max(x for x, y in maze.keys()) + 1
    global_h = max(y for x, y in maze.keys()) + 1

    return IDA_star(
        start_state=start,
        goal_test=lambda n: maze_goal_test(n, goal),
        get_neighbors=lambda n: maze_get_neighbors(n, maze),
        heuristic=lambda n: maze_heuristic(n, goal),
        debug=True
    )

# ===============================================================
# RUN WITH TIMEOUT
# ===============================================================
def run_with_timeout(func, *args):
    """Run an algorithm and stop after 10 seconds"""
    start_time = time.time()
    try:
        result = func(*args)
    except RecursionError:
        return "TIMEOUT", None, None

    # Check if it exceeded timeout (special for IDA*)
    if result[0] == "TIMEOUT":
        return "TIMEOUT", None, None

    if time.time() - start_time > 10:
        return "TIMEOUT", None, None
    return result

# ===============================================================
# RUN SINGLE ALGORITHM
# ===============================================================
def run_single_algorithm(choice, maze, start, goal):
    mapping = {
        "1": ("BFS", BFS),
        "2": ("DFS", DFS),
        "3": ("UCS", UCS),
        "4": ("Greedy", Greedy),
        "5": ("A*", A),
        "6": ("IDA*", IDA),
        "7": ("Hill", Hill),
        "8": ("Beam", Beam)
    }

    if choice not in mapping:
        return None

    name, function = mapping[choice]

    t0 = time.perf_counter()
    path, nodes, cost = run_with_timeout(function, maze, start, goal)
    t1 = time.perf_counter()

    if path == "TIMEOUT":
        print("\n This algorithm is NOT suitable for this problem (Exceeded 10 seconds)\n")
        return name, {
            "time": 10,
            "nodes_expanded": 0,
            "path_length": 0,
            "cost": None,
            "path": None
        }

    return name, {
        "time": t1 - t0,
        "nodes_expanded": nodes,
        "path_length": len(path) if path else 0,
        "cost": cost,
        "path": path
    }

# ===============================================================
# INTERACTIVE MENU
# ===============================================================
def interactive_menu(maze, width, hight, start, goal):
    results = {}
    delay_seconds = 0

    menu = """
Choose algorithm:
1) BFS
2) DFS
3) UCS
4) Greedy
5) A*
6) IDA*
7) Hill
8) Beam
9) Compare
10) Exit
11) Set Time Delay After Search
>>> """

    while True:
        choice = input(menu).strip()

        if choice == "10":  # Exit
            break

        if choice == "9":  # Compare
            print_results_table(results)
            continue

        if choice == "11":  # Set delay
            try:
                delay_seconds = float(input("Enter delay in seconds: "))
                print(f"Delay set to {delay_seconds} seconds.")
            except:
                print("Invalid.")
            continue

        sel = run_single_algorithm(choice, maze, start, goal)
        if sel is None:
            print("Invalid selection.")
            continue

        name, stats = sel
        results[name] = stats

        if not stats["path"]:
            continue

        print(f"\n*** Result of {name} ***")
        print("Time:", stats["time"])
        print("Nodes:", stats["nodes_expanded"])
        print("Path len:", stats["path_length"])
        print("Cost:", stats["cost"])
        print(render_maze_with_path(maze, width, hight, stats["path"], start, goal))

        if delay_seconds > 0:
            time.sleep(delay_seconds)

# ===============================================================
# MAIN
# ===============================================================
def main():
    print("Maze Generator:\n")
    width = int(input("Maze width: "))
    hight = int(input("Maze height: "))

    maze = generate_maze(width, hight)
    print("\nGenerated Maze:")
    print(render_maze(maze, width, hight))

    start, goal = input_start_goal(maze, width, hight)
    interactive_menu(maze, width, hight, start, goal)

# Run main
if __name__ == "__main__":
    main()

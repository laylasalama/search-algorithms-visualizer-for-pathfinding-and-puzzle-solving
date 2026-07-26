#=========================================================================#
#=======================maze of bfs=======================================#
#=========================================================================#

import random
import os
import time
from collections import deque

# ===============================================================
# DIRECTIONS
# ===============================================================
DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East": (1, 0),
    "West": (-1, 0)
}

OPPOSITE = {"North":"South", "South":"North", "East":"West", "West":"East"}

# ===============================================================
# RENDER MAZE (ASCII)
# ===============================================================
def render_maze(maze, width, hight):
    out = ""
    out += "+" + "---+" * width + "\n"
    for y in range(hight):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x,y)]
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
    maze = {(x,y):{"North":True,"South":True,"East":True,"West":True}
             for y in range(hight) for x in range(width)}

    visited = set()
    stack = []

    x, y = random.randint(0,width-1), random.randint(0,hight-1)
    visited.add((x,y))
    stack.append((x,y))

    while stack:
        os.system("cls" if os.name=="nt" else "clear")
        print(render_maze(maze, width, hight))
        time.sleep(0.0005)

        x, y = stack[-1]
        neighbors = []

        for d,(dx,dy) in DIRECTIONS.items():
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < hight and (nx,ny) not in visited:
                neighbors.append((d,nx,ny))

        if neighbors:
            d, nx, ny = random.choice(neighbors)
            maze[(x,y)][d] = False
            maze[(nx,ny)][OPPOSITE[d]] = False
            visited.add((nx,ny))
            stack.append((nx,ny))
        else:
            stack.pop()

    return maze

# ===============================================================
# RENDER WITH PATH
# ===============================================================
def render_maze_with_path(maze, width, hight, path=None, start=None, goal=None):
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
    while True:
        try:
            sx, sy = map(int, input("Start (x y): ").split())
            gx, gy = map(int, input("Goal  (x y): ").split())
        except:
            print("Invalid input.")
            continue
        if not (0 <= sx < width and 0 <= sy < hight): continue
        if not (0 <= gx < width and 0 <= gy < hight): continue
        return (sx, sy), (gx, gy)

# ===============================================================
# RESULTS TABLE
# ===============================================================
def print_results_table(results):
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
# BFS (FULL IMPLEMENTATION)
# ===============================================================
def BFS(maze, start, goal):
    from collections import deque
    global global_maze, global_w, global_h
    global_maze = maze
    global_w = max(x for x, y in maze.keys()) + 1
    global_h = max(y for x, y in maze.keys()) + 1

    frontier = deque([start])
    came_from = {start: None}
    nodes_expanded = 0

    while frontier:
        node = frontier.popleft()
        nodes_expanded += 1

        # Visualization
        os.system("clear")  # or "cls" if Windows
        path = []
        n = node
        while n is not None:
            path.append(n)
            n = came_from[n]
        path.reverse()
        print("Searching BFS...\n")
        print(render_maze_with_path(global_maze, global_w, global_h, path))
        time.sleep(0.05)

        if node == goal:
            # Reconstruct path
            path = []
            n = node
            while n is not None:
                path.append(n)
                n = came_from[n]
            path.reverse()
            return path, nodes_expanded, len(path)-1

        # Explore neighbors
        x, y = node
        for d, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < global_w and 0 <= ny < global_h:
                if not maze[(x, y)][d] and (nx, ny) not in came_from:
                    frontier.append((nx, ny))
                    came_from[(nx, ny)] = node

    return None, nodes_expanded, None

# EMPTY placeholders
def DFS(maze, start, goal): return [], 0, 0
def UCS(maze, start, goal): return [], 0, 0
def Greedy(maze, start, goal): return [], 0, 0
def A(maze, start, goal): return [], 0, 0
def IDA(maze, start, goal): return [], 0, 0    
def Hill(maze, start, goal): return [], 0, 0
def Beam(maze, start, goal): return [], 0, 0

# ===============================================================
# RUN ALGORITHM
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
    path, nodes, cost = function(maze, start, goal)
    t1 = time.perf_counter()

    return name, {
        "time": t1 - t0,
        "nodes_expanded": nodes,
        "path_length": len(path) if path else 0,
        "cost": cost,
        "path": path
    }

# ===============================================================
# MENU
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
6) BFS (instead of IDA*)
7) Hill
8) Beam
9) Compare
10) Exit
11) Set delay
>>> """

    while True:
        choice = input(menu).strip()

        if choice == "10":
            break

        if choice == "9":
            print_results_table(results)
            continue

        if choice == "11":
            try:
                delay_seconds = float(input("Enter delay: "))
            except:
                print("Invalid.")
            continue

        sel = run_single_algorithm(choice, maze, start, goal)
        if sel is None:
            print("Invalid.")
            continue

        name, stats = sel
        results[name] = stats

        if not stats["path"]:
            print("No path.")
            continue

        print(f"\n*** Result of {name} ***")
        print("Time:", stats["time"])
        print("Nodes:", stats["nodes_expanded"])
        print("Path len:", stats["path_length"])
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

if __name__ == "__main__":
    main()
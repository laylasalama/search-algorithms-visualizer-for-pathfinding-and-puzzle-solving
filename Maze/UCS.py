#=========================================================================#
#=======================maze of ucs=======================================#
#=========================================================================#
import random
import os
import time
import heapq

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
    out = ""
    out += "+" + "---+" * width + "\n"
    for y in range(hight):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x, y)]
            row1 += "   "
            row1 += " " if not cell["East"] else "|"
            row2 += "   " if not cell["South"] else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"
    return out

# ===============================================================
# MAZE GENERATION (DFS)
# ===============================================================
def generate_maze(width, hight):
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
# INPUT START / GOAL
# ===============================================================
def input_start_goal(maze, width, hight):
    while True:
        try:
            sx, sy = map(int, input("Start (x y): ").split())
            gx, gy = map(int, input("Goal  (x y): ").split())
        except:
            print("Invalid input.")
            continue

        if not (0 <= sx < width < 9999 and 0 <= sy < hight): continue
        if not (0 <= gx < width and 0 <= gy < hight): continue
        return (sx, sy), (gx, gy)

# ===============================================================
# PRINT RESULTS TABLE
# ===============================================================
def print_results_table(results):
    header = f"{'Algorithm':10} | {'Time (s)':>9} | {'Nodes':>8} | {'PathLen':>7} | {'Cost':>6}"
    print(header)
    print("-" * len(header))
    for n, s in results.items():
        print(f"{n:10} | {s['time']:.6f} | {s['nodes_expanded']:8} | {s['path_length']:7} | {s['cost']:6}")

# ===============================================================
# UCS (REAL IMPLEMENTATION)
# ===============================================================
def UCS(maze, start, goal):
    import heapq
    import os
    import time
    global global_maze, global_w, global_h
    global_maze = maze
    global_w = max(x for x, y in maze.keys()) + 1
    global_h = max(y for x, y in maze.keys()) + 1

    pq = [(0, start)]
    visited = {start: None}
    cost_so_far = {start: 0}
    nodes_expanded = 0

    while pq:
        cost, node = heapq.heappop(pq)
        nodes_expanded += 1

        # Visualization
        os.system("cls" if os.name == "nt" else "clear")
        path = []
        n = node
        while n is not None:
            path.append(n)
            n = visited[n]
        path.reverse()
        print("Searching UCS...\n")
        print(render_maze_with_path(global_maze, global_w, global_h, path))
        time.sleep(0.05)

        if node == goal:
            # Reconstruct final path
            path = []
            n = node
            while n is not None:
                path.append(n)
                n = visited[n]
            path.reverse()
            return path, nodes_expanded, cost

        x, y = node
        for d, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < global_w and 0 <= ny < global_h:
                if not maze[(x, y)][d]:
                    new_cost = cost_so_far[node] + 1
                    if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                        cost_so_far[(nx, ny)] = new_cost
                        visited[(nx, ny)] = node
                        heapq.heappush(pq, (new_cost, (nx, ny)))

    return None, nodes_expanded, None

# ===============================================================
# Empty Algorithms
# ===============================================================
def BFS(maze, start, goal): return [], 0, 0
def DFS(maze, start, goal): return [], 0, 0
def Greedy(maze, start, goal): return [], 0, 0
def A(maze, start, goal): return [], 0, 0
def IDA(maze, start, goal): return [], 0, 0    
def Hill(maze, start, goal): return [], 0, 0
def Beam(maze, start, goal): return [], 0, 0

# ===============================================================
# RUN SINGLE ALGO
# ===============================================================
def run_single_algorithm(choice, maze, start, goal):
    mapping = {
    "1": ("BFS", BFS),
    "2": ("DFS", DFS),
    "3": ("UCS", UCS),
    "4": ("Greedy", Greedy),
    "5": ("A*", A),
    "6": ("IDA*", IDA),
    "7": ("Hill Climbing", Hill),
    "8": ("Beam", Beam)
    }

    if choice not in mapping:
        return None

    name, func = mapping[choice]

    t0 = time.perf_counter()
    path, nodes, cost = func(maze, start, goal)
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
    delay = 0

    menu = """
Choose algorithm:
1) DFS
2) BFS
3) UCS
4) Greedy
5) A*
6) UCS (instead of IDA*)
7) Hill
8) Beam
9) Compare results
10) Exit
11) Set delay
>>> """

    while True:
        c = input(menu).strip()

        if c == "10":
            break

        if c == "9":
            print_results_table(results)
            continue

        if c == "11":
            delay = float(input("Enter delay seconds: "))
            continue

        sel = run_single_algorithm(c, maze, start, goal)
        if sel is None:
            print("Invalid choice.")
            continue

        name, stats = sel
        results[name] = stats

        if not stats["path"]:
            print("NO PATH.")
            continue

        print(f"\n*** Result of {name} ***")
        print(f"Time: {stats['time']}")
        print(f"Nodes expanded: {stats['nodes_expanded']}")
        print(f"Path length: {stats['path_length']}")
        print(f"Cost: {stats['cost']}")

        print(render_maze_with_path(maze, width, hight, stats["path"], start, goal))

        if delay > 0:
            time.sleep(delay)

# ===============================================================
# MAIN
# ===============================================================
def main():
    print("Maze Generator:\n")
    width = int(input("Maze width: "))
    hight = int(input("Maze height: "))

    maze = generate_maze(width, hight)
    print(render_maze(maze, width, hight))

    start, goal = input_start_goal(maze, width, hight)
    interactive_menu(maze, width, hight, start, goal)

if __name__ == "__main__":
    main()
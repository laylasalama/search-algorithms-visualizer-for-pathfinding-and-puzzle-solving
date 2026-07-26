import random
import os
import time
from collections import deque

# =====================================================================
# 8 directions for BFS/DFS/IDA*
# =====================================================================
DIRECTIONS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),   # horizontal & vertical
    (-1, 1), (-1, -1), (1, 1), (1, -1)  # diagonals
]

# =====================================================================
# GRID CREATION AND INPUT FUNCTIONS
# =====================================================================
def create_grid(size):
    return [[0]*size for _ in range(size)]

def add_walls(grid):
    size = len(grid)
    print("\nEnter wall positions (row column). Type 'done' when finished.")
    while True:
        inp = input("Wall: ").strip()
        if inp.lower() == "done":
            break
        parts = inp.split()
        if len(parts) != 2:
            print("Enter 2 numbers.")
            continue
        try:
            r, c = map(int, parts)
            r -= 1
            c -= 1
        except ValueError:
            print("Invalid.")
            continue
        if not (0 <= r < size and 0 <= c < size):
            print("Out of range.")
            continue
        grid[r][c] = 1
        print_grid(grid)

def get_point(name, size):
    while True:
        inp = input(f"Enter {name} (row column): ").split()
        if len(inp) != 2:
            print("Enter 2 numbers.")
            continue
        try:
            r, c = map(int, inp)
            r -= 1
            c -= 1
        except ValueError:
            print("Invalid.")
            continue
        if not (0 <= r < size and 0 <= c < size):
            print("Out of range.")
            continue
        return (r, c)

def print_grid(grid, start=None, goal=None, path=None):
    os.system("cls" if os.name=="nt" else "clear")
    size = len(grid)
    for r in range(size):
        line = ""
        for c in range(size):
            if (r,c) == start:
                line += " S "
            elif (r,c) == goal:
                line += " G "
            elif path and (r,c) in path:
                line += " - "
            elif grid[r][c] == 1:
                line += " # "
            else:
                line += " . "
        print(line)
    print()

# =====================================================================
# BFS ALGORITHM WITH ANIMATION
# =====================================================================
def BFS(grid, start, goal):
    queue = deque([start])
    visited = set([start])
    parent = {start: None}
    nodes = 0
    start_time = time.time()
    delay = 0.15

    while queue:
        node = queue.popleft()
        nodes += 1
        # current path for visualization
        current_path = reconstruct_path(parent, start, node)

        print_grid(grid, start, goal, current_path)
        print(f"BFS | Expanded Nodes: {nodes} | Time: {time.time()-start_time:.2f}s")
        time.sleep(delay)

        if node == goal:
            return reconstruct_path(parent, start, goal), nodes

        for n in get_neighbors_grid(node, grid):
            if n not in visited:
                visited.add(n)
                parent[n] = node
                queue.append(n)
    return None, nodes

def get_neighbors_grid(node, grid):
    r, c = node
    neighbors = []
    size = len(grid)
    for dr, dc in DIRECTIONS:
        nr, nc = r+dr, c+dc
        if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] != 1:
            neighbors.append((nr,nc))
    return neighbors

def reconstruct_path(parent, start, goal):
    if goal not in parent:
        return None
    path = []
    node = goal
    while node:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path

# =====================================================================
# IDA*  HELPER FUNCTIONS
# =====================================================================
def manhattan(node, goal):
    return abs(node[0]-goal[0]) + abs(node[1]-goal[1])

def goal_test_grid(node, goal):
    return node == goal

def visualize_path_ida(path, grid, start, goal):
    print_grid(grid, start, goal, path)
# =====================================================================
# IDA* templete
# =====================================================================
def IDA_star_template(start_state, goal, grid, timeout=10, debug=True):
    start_time = time.time()
    threshold = manhattan(start_state, goal)
    path = [start_state]
    nodes_expanded = 0

    def search(g_cost, threshold):
        nonlocal nodes_expanded
        if time.time() - start_time > timeout:
            return "TIMEOUT"
        node = path[-1]
        f = g_cost + manhattan(node, goal)
        if f > threshold:
            return f
        if goal_test_grid(node, goal):
            return "FOUND"

        nodes_expanded += 1
        min_threshold = float("inf")
        for neighbor in get_neighbors_grid(node, grid):
            if neighbor in path:
                continue
            path.append(neighbor)
            if debug:
                visualize_path_ida(path, grid, start_state, goal)
                time.sleep(0.15)
            result = search(g_cost+1, threshold)
            if result == "FOUND":
                return "FOUND"
            if isinstance(result,(int,float)) and result<min_threshold:
                min_threshold = result
            path.pop()
        return min_threshold

    while True:
        result = search(0, threshold)
        if result == "TIMEOUT":
            return None, nodes_expanded, "Timeout"
        if result == "FOUND":
            return path[:], nodes_expanded, "Success"
        threshold = result

# =====================================================================
# MAIN FUNCTION
# =====================================================================
def main():
    print("Grid Search with BFS and IDA*\n")
    size = int(input("Enter grid size: "))
    grid = create_grid(size)

    print("\n--- Add Walls ---")
    add_walls(grid)

    start = get_point("Start", size)
    goal = get_point("Goal", size)

    print("\nInitial Grid:")
    print_grid(grid, start, goal)

    while True:
        print("\nChoose Algorithm:")
        print("1) BFS\n2) IDA*\n3) Exit")
        choice = input("Choice: ").strip()
        if choice=="1":
            path, nodes = BFS(grid, start, goal)
            if path:
                print_grid(grid, start, goal, path)
                print(f"BFS Finished | Nodes Expanded: {nodes}")
            else:
                print("No path found by BFS")
        elif choice=="2":
            path, nodes, status = IDA_star_template(start, goal, grid)
            if path:
                print_grid(grid, start, goal, path)
            print(f"IDA* Status: {status} | Nodes Expanded: {nodes}")
        elif choice=="3":
            break
        else:
            print("Invalid choice.")
            

if __name__=="__main__":
    main()

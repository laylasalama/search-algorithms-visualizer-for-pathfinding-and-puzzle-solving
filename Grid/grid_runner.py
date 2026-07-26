"""
Grid Algorithm Runner - Reads grid from command line and runs pathfinding
Emits STATE markers showing exploration progress
"""
import sys
import ast
import os
import time
import tracemalloc

# Import common utilities from Astar.py
from Astar import (
    DIRECTIONS, get_neighbors, reconstruct_path, 
    print_grid_with_path, heuristic
)

def run_bfs(grid, cost_grid, start, goal):
    """BFS pathfinding - emits STATE markers"""
    from collections import deque
    
    visited = set([start])
    parent = {start: None}
    queue = deque([start])
    nodes = 0
    start_time = time.time()
    timeout = 10

    while queue:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        node = queue.popleft()
        nodes += 1

        # Emit STATE marker
        print(f"STATE:{node}")

        if node == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, node):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)

    print("Status: Unsolved (no path found)")
    return None, nodes


def run_dfs(grid, cost_grid, start, goal):
    """DFS pathfinding - emits STATE markers"""
    visited = set()
    parent = {start: None}
    stack = [start]
    nodes = 0
    start_time = time.time()
    timeout = 10

    while stack:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        node = stack.pop()
        if node in visited:
            continue
        
        visited.add(node)
        nodes += 1

        # Emit STATE marker
        print(f"STATE:{node}")

        if node == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, node):
            if neighbor not in visited:
                parent[neighbor] = node
                stack.append(neighbor)

    print("Status: Unsolved (no path found)")
    return None, nodes


def run_greedy(grid, cost_grid, start, goal):
    """Greedy Best-First Search - emits STATE markers"""
    from heapq import heappush, heappop
    
    visited = set()
    parent = {start: None}
    frontier = []
    heappush(frontier, (heuristic(start, goal), start))
    nodes = 0
    start_time = time.time()
    timeout = 10

    while frontier:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        h, current = heappop(frontier)

        if current in visited:
            continue
        
        visited.add(current)
        nodes += 1

        # Emit STATE marker
        print(f"STATE:{current}")

        if current == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, current):
            if neighbor not in visited:
                parent[neighbor] = current
                heappush(frontier, (heuristic(neighbor, goal), neighbor))

    print("Status: Unsolved (no path found)")
    return None, nodes


def run_ucs(grid, cost_grid, start, goal):
    """Uniform Cost Search - emits STATE markers"""
    from heapq import heappush, heappop
    
    visited = set()
    parent = {start: None}
    frontier = []
    heappush(frontier, (0, start))
    cost_so_far = {start: 0}
    nodes = 0
    start_time = time.time()
    timeout = 10

    while frontier:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        current_cost, current = heappop(frontier)

        if current in visited:
            continue
        
        visited.add(current)
        nodes += 1

        # Emit STATE marker
        print(f"STATE:{current}")

        if current == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, current):
            if neighbor not in visited:
                new_cost = current_cost + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    parent[neighbor] = current
                    heappush(frontier, (new_cost, neighbor))

    print("Status: Unsolved (no path found)")
    return None, nodes


def run_astar(grid, cost_grid, start, goal):
    """A* Search - emits STATE markers"""
    from heapq import heappush, heappop
    
    def f_score(node):
        g = len(reconstruct_path({start: None}, start, node) or [start]) - 1
        h = heuristic(node, goal)
        return g + h
    
    visited = set()
    parent = {start: None}
    frontier = []
    heappush(frontier, (f_score(start), start))
    nodes = 0
    start_time = time.time()
    timeout = 10

    while frontier:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        _, current = heappop(frontier)

        if current in visited:
            continue
        
        visited.add(current)
        nodes += 1

        # Emit STATE marker
        print(f"STATE:{current}")

        if current == goal:
            path = reconstruct_path(parent, start, goal)
            return path, nodes

        for neighbor in get_neighbors(grid, current):
            if neighbor not in visited:
                parent[neighbor] = current
                heappush(frontier, (f_score(neighbor), neighbor))

    print("Status: Unsolved (no path found)")
    return None, nodes


def run_ida_star(grid, cost_grid, start, goal):
    """IDA* Search - emits STATE markers"""
    nodes_expanded = [0]  # Use list to allow modification in nested function
    
    def search(path, g, threshold):
        node = path[-1]
        f = g + heuristic(node, goal)
        
        if f > threshold:
            return f, None
        
        if node == goal:
            return f, path
        
        print(f"STATE:{node}")
        nodes_expanded[0] += 1
        
        min_threshold = float('inf')
        for neighbor in get_neighbors(grid, node):
            if neighbor not in path:
                path.append(neighbor)
                t, result = search(path, g + 1, threshold)
                if result is not None:
                    return t, result
                min_threshold = min(min_threshold, t)
                path.pop()
        
        return min_threshold, None

    threshold = heuristic(start, goal)
    start_time = time.time()
    timeout = 10

    while threshold != float('inf'):
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes_expanded[0]

        _, path = search([start], 0, threshold)
        if path is not None:
            return path, nodes_expanded[0]
        
        threshold = float('inf')  # Simplified - real IDA* tracks this

    print("Status: Unsolved (no path found)")
    return None, nodes_expanded[0]


def run_hill_climbing(grid, cost_grid, start, goal):
    """Hill Climbing - emits STATE markers"""
    current = start
    path = [current]
    nodes = 1
    start_time = time.time()
    timeout = 10

    while current != goal:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (reached the local maximum)")
            return None, nodes

        neighbors = get_neighbors(grid, current)
        if not neighbors:
            print("Status: Unsolved (reached the local maximum)")
            return None, nodes

        # Choose neighbor with best heuristic
        best_neighbor = min(neighbors, key=lambda n: heuristic(n, goal))
        best_h = heuristic(best_neighbor, goal)
        current_h = heuristic(current, goal)

        if best_h >= current_h:
            # Local maximum
            print("Status: Unsolved (reached the local maximum)")
            return None, nodes

        current = best_neighbor
        path.append(current)
        nodes += 1

        print(f"STATE:{current}")

    return path, nodes


def run_beem(grid, cost_grid, start, goal):
    """Beam Search - emits STATE markers"""
    from heapq import heappush, heappop
    
    beam = [(heuristic(start, goal), start, [start])]
    visited = set([start])
    nodes = 0
    start_time = time.time()
    timeout = 10
    beam_width = 3

    while beam:
        if time.time() - start_time > timeout:
            print("Status: Unsolved (timeout)")
            return None, nodes

        candidates = []
        for h, node, path in beam:
            if node == goal:
                return path, nodes

            for neighbor in get_neighbors(grid, node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    nodes += 1
                    new_path = path + [neighbor]
                    new_h = heuristic(neighbor, goal)
                    
                    print(f"STATE:{neighbor}")
                    
                    candidates.append((new_h, neighbor, new_path))

        if not candidates:
            print("Status: Unsolved (no solution found)")
            return None, nodes

        candidates.sort()
        beam = candidates[:beam_width]

    print("Status: Unsolved (no solution found)")
    return None, nodes


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python grid_runner.py <algorithm> <grid> <start> <goal>")
        sys.exit(1)

    algorithm = sys.argv[1].lower()
    grid_str = sys.argv[2]
    start_str = sys.argv[3]
    goal_str = sys.argv[4]

    # Parse grid
    try:
        grid = ast.literal_eval(grid_str)
    except:
        print("Error: Invalid grid format")
        sys.exit(1)

    # Parse start and goal
    try:
        start = ast.literal_eval(start_str)
        goal = ast.literal_eval(goal_str)
    except:
        print("Error: Invalid start/goal format")
        sys.exit(1)

    # Create cost grid (all costs = 1) or parse optional cost grid argument
    cost_grid = [[1 for _ in range(len(grid[0]))] for _ in range(len(grid))]
    if len(sys.argv) >= 6:
        # argv[5] expected to be a stringified Python list (e.g. str(costs))
        cost_str = sys.argv[5]
        try:
            parsed = ast.literal_eval(cost_str)
            # basic validation: must be 2D list matching grid size
            if (isinstance(parsed, list) and len(parsed) == len(grid)
                    and all(isinstance(row, list) and len(row) == len(grid[0]) for row in parsed)):
                cost_grid = parsed
        except Exception:
            pass

    # Run algorithm with memory tracking
    algo_map = {
        'a*': run_astar,
        'bfs': run_bfs,
        'dfs': run_dfs,
        'greedy': run_greedy,
        'ucs': run_ucs,
        'hillclimbing': run_hill_climbing,
        'hill climbing': run_hill_climbing,
        'ida*': run_ida_star,
        'beem': run_beem,
    }

    if algorithm not in algo_map:
        print(f"Unknown algorithm: {algorithm}")
        sys.exit(1)

    # Start memory tracking
    tracemalloc.start()
    path, nodes = algo_map[algorithm](grid, cost_grid, start, goal)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Convert to MB
    memory_mb = peak / (1024 * 1024)

    print(f"Nodes Expanded: {nodes}")
    # Print full path for GUI to consume (as Python literal)
    print(f"PATH:{path}")
    if path:
        print(f"Path Length: {len(path)}")
    else:
        print(f"Path Length: -1")
    print(f"Memory Used: {memory_mb:.2f} MB")

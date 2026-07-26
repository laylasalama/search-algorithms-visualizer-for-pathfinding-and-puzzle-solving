import os
import time
from heapq import heappush, heappop

# ================================
#   CLEAR SCREEN
# ================================
def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass
 #os.system("clear")   LINUX
# ================================
#   DISPLAY 8-PUZZLE
# ================================
def display_puzzle(tiles):
    for i in range(0, 9, 3):
        print(" ".join(str(x) if x != 0 else " " for x in tiles[i:i+3]))
    print()

# ================================
#   GOAL TEST
# ================================
def goal_test_puzzle(state):
    return state == [1,2,3,4,5,6,7,8,0]

# ================================
#   MANHATTAN HEURISTIC
# ================================
def heuristic_puzzle(state):
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0: 
            continue
        r, c = divmod(index, 3)
        gr, gc = divmod(tile - 1, 3)
        distance += abs(r - gr) + abs(c - gc)
    return distance

# ================================
#   NEIGHBORS
# ================================
def neighbors_puzzle(state):
    neighbors = []
    blank = state.index(0)
    r, c = divmod(blank, 3)
    moves = [(1,0),(-1,0),(0,1),(0,-1)]

    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            new_state = state[:]
            new_state[blank], new_state[nr*3 + nc] = new_state[nr*3 + nc], new_state[blank]
            neighbors.append((new_state, 1))

    return neighbors

# ================================
#   GREEDY BEST FIRST SEARCH
# ================================
def greedy_search(start):
    frontier = []
    heappush(frontier, (heuristic_puzzle(start), start))
    visited = set()
    parent = {tuple(start): None}

    nodes_expanded = 0

    while frontier:
        h, current = heappop(frontier)
        key = tuple(current)

        if key in visited:
            continue

        visited.add(key)
        nodes_expanded += 1

        if goal_test_puzzle(current):
            return parent, current, nodes_expanded

        for neighbor, _ in neighbors_puzzle(current):
            nkey = tuple(neighbor)
            if nkey not in visited:
                parent[nkey] = current
                heappush(frontier, (heuristic_puzzle(neighbor), neighbor))

    return None, None, nodes_expanded

# ================================
#   RECONSTRUCT PATH
# ================================
def reconstruct_path(parent, goal):
    path = []
    state = goal
    while state is not None:
        path.append(state)
        state = parent.get(tuple(state))
    return list(reversed(path))

# ================================
#   MAIN + VISUALIZATION + LIVE TIMER
# ================================
if __name__ == "__main__":
    puzzle = [1,4,2,3,7,5,6,0,8]

    print("Initial Puzzle:\n")
    display_puzzle(puzzle)

    # Start measuring time
    start_time = time.time()

    parent, goal, nodes = greedy_search(puzzle)

    if goal:
        path = reconstruct_path(parent, goal)

        print("\nSolving with Greedy Best-First Search...")
        time.sleep(1)

        for step_i, step in enumerate(path):
            clear_screen()

            live_time = time.time() - start_time

            print(f"Step: {step_i + 1}/{len(path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")

            display_puzzle(step)
            time.sleep(0.10)

        final_time = time.time() - start_time

        print("Puzzle Solved!")
        print("Nodes Expanded:", nodes)
        print("Path Length:", len(path)-1)
        print(f"Total Time: {final_time:.6f} seconds")

    else:
        print("No solution found.")
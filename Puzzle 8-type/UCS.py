#=========================================================================#
#===================puzzle_8 type of ucs==================================#
#=========================================================================#
import os
import time
from heapq import heappush, heappop

# ================================
#   CLEAR SCREEN
# ================================
def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass

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
            neighbors.append((new_state, 1))  # UCS cost = 1 per move
    return neighbors

# ================================
#   UCS SEARCH WITH SAME OUTPUT AS GREEDY
# ================================
def ucs_search(start, delay=0.10):
    frontier = []
    heappush(frontier, (0, start))
    visited = set()
    parent = {tuple(start): None}
    cost_so_far = {tuple(start): 0}

    nodes_expanded = 0
    start_time = time.time()
    timeout = 8  # 8 second timeout

    while frontier:
        # Check timeout
        if time.time() - start_time > timeout:
            return None, None, nodes_expanded
            
        cost, current = heappop(frontier)
        key = tuple(current)

        if key in visited:
            continue
        visited.add(key)
        nodes_expanded += 1

        # Emit STATE for the current node so GUI can display tries in real-time
        try:
            print(f"STATE:{current}")
        except Exception:
            pass
        if delay and delay > 0:
            time.sleep(delay)

        if goal_test_puzzle(current):
            return parent, current, nodes_expanded

        for neighbor, step_cost in neighbors_puzzle(current):
            nkey = tuple(neighbor)
            new_cost = cost_so_far[key] + step_cost
            if nkey not in cost_so_far or new_cost < cost_so_far[nkey]:
                cost_so_far[nkey] = new_cost
                parent[nkey] = key
                heappush(frontier, (new_cost, neighbor))

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

    start_time = time.time()
    parent, goal, nodes = ucs_search(puzzle, delay=0.10)

    if goal:
        path = reconstruct_path(parent, goal)

        for step_i, step in enumerate(path):
            clear_screen()
            live_time = time.time() - start_time
            print(f"STATE:{step}")
            display_puzzle(step)
            time.sleep(0.10)

    else:
        pass
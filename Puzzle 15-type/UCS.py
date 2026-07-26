#=========================================================================#
#=======================puzzle_15 type of ucs==================================#
#=========================================================================#
import os
import time
from heapq import heappush, heappop

PAUSE_FILE = os.environ.get('PAUSE_FILE')
STOP_FILE = os.environ.get('STOP_FILE')

def _maybe_pause():
    if PAUSE_FILE:
        try:
            while os.path.exists(PAUSE_FILE):
                time.sleep(0.05)
        except Exception:
            pass

def _check_stop():
    """Check if algorithm should stop. Raise SystemExit if stop signal received."""
    if STOP_FILE and os.path.exists(STOP_FILE):
        raise SystemExit("Stop signal received")

def _sleep_with_pause_check(duration, check_interval=0.01):
    """Sleep while frequently checking for pause file."""
    elapsed = 0.0
    while elapsed < duration:
        _maybe_pause()
        sleep_time = min(check_interval, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time


# ================================
#   CLEAR SCREEN
# ================================
def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass

# ================================
#   DISPLAY 15-PUZZLE
# ================================
def display_puzzle(tiles):
    for i in range(0, 16, 4):
        print(" ".join(f"{x:2d}" if x != 0 else "  " for x in tiles[i:i+4]))
    print()

# ================================
#   GOAL TEST
# ================================
def goal_test_puzzle(state):
    return state == [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0]

# ================================
#   NEIGHBORS
# ================================
def neighbors_puzzle(state):
    neighbors = []
    blank = state.index(0)
    r, c = divmod(blank, 4)
    moves = [(1,0),(-1,0),(0,1),(0,-1)]

    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            new_state = state[:]
            new_state[blank], new_state[nr*4 + nc] = new_state[nr*4 + nc], new_state[blank]
            neighbors.append((new_state, 1))  # UCS cost = 1 per move
    return neighbors

# ================================
#   UCS SEARCH
# ================================
def ucs_search(start, delay=0.10):
    frontier = []
    heappush(frontier, (0, start))
    visited = set()
    parent = {tuple(start): None}
    cost_so_far = {tuple(start): 0}

    nodes_expanded = 0
    start_time = time.time()
    timeout = 15  # 15 second timeout for 15-puzzle

    while frontier:
        _check_stop()
        _maybe_pause()
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
    import sys
    # Read puzzle from stdin if provided by GUI, otherwise use default test puzzle
    try:
        puzzle_input = sys.stdin.readline().strip()
        if puzzle_input:
            puzzle = [int(x) for x in puzzle_input.split(',')]
        else:
            puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]
    except:
        puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]

    start_time = time.time()
    parent, goal, nodes = ucs_search(puzzle, delay=0.10)

    if goal:
        path = reconstruct_path(parent, goal)

        for step_i, step in enumerate(path):
            _maybe_pause()
            clear_screen()
            live_time = time.time() - start_time
            print(f"STATE:{step}")
            display_puzzle(step)
            _sleep_with_pause_check(0.10)

    else:
        pass
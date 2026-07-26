#=========================================================================#
#=======================puzzle_15 type of bfs==============================#
#=========================================================================#
import os
import time
from collections import deque

# ======== STOP & CONTINUE CONTROL ========
CONTINUE_FILE = os.environ.get('CONTINUE_FILE')
STOP_FILE = os.environ.get('STOP_FILE')

def _maybe_continue():
    if CONTINUE_FILE:
        try:
            while os.path.exists(CONTINUE_FILE):
                time.sleep(0.05)
        except Exception:
            pass

def _check_stop():
    """Stop execution immediately if stop file exists"""
    if STOP_FILE and os.path.exists(STOP_FILE):
        raise SystemExit("Stop signal received")

def _sleep_with_continue_check(duration, check_interval=0.01):
    elapsed = 0.0
    while elapsed < duration:
        _maybe_continue()
        _check_stop()
        sleep_time = min(check_interval, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time


# ================================
#   CLEAR SCREEN
# ================================
def clear_screen():
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
            neighbors.append((new_state, 1))
    return neighbors

# ================================
#   BFS SEARCH
# ================================
def bfs_search(start, delay=0.10):
    frontier = deque([start])
    frontier_set = {tuple(start)}
    visited = set()
    parent = {tuple(start): None}
    nodes_expanded = 0
    start_time = time.time()
    timeout = 15  # 15 second timeout for 15-puzzle

    while frontier:
        _check_stop()
        _maybe_continue()

        if time.time() - start_time > timeout:
            return None, None, nodes_expanded
            
        current = frontier.popleft()
        key = tuple(current)
        frontier_set.discard(key)

        if key in visited:
            continue
        visited.add(key)
        nodes_expanded += 1

        try:
            print(f"STATE:{current}")
        except Exception:
            pass

        if delay and delay > 0:
            _sleep_with_continue_check(delay)

        if goal_test_puzzle(current):
            return parent, current, nodes_expanded

        for neighbor, _ in neighbors_puzzle(current):
            nkey = tuple(neighbor)
            if nkey not in visited and nkey not in frontier_set:
                parent[nkey] = key
                frontier.append(neighbor)
                frontier_set.add(nkey)

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
    try:
        puzzle_input = sys.stdin.readline().strip()
        if puzzle_input:
            puzzle = [int(x) for x in puzzle_input.split(',')]
        else:
            puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]
    except:
        puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]

    start_time = time.time()
    parent, goal, nodes = bfs_search(puzzle, delay=0.10)

    if goal:
        path = reconstruct_path(parent, goal)

        for step_i, step in enumerate(path):
            _check_stop()
            _maybe_continue()
            clear_screen()
            live_time = time.time() - start_time
            print(f"STATE:{step}")
            display_puzzle(step)
            _sleep_with_continue_check(0.10)

    else:
        pass

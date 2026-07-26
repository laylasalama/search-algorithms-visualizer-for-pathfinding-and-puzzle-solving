import os
import time
from heapq import heappush, heappop

# ✅ Stop = Pause , Continue = Resume
STOP_FILE = os.environ.get('STOP_FILE')        # pause file
CONTINUE_FILE = os.environ.get('CONTINUE_FILE')  # resume file

def _maybe_pause():
    try:
        while STOP_FILE and os.path.exists(STOP_FILE):
            time.sleep(0.05)
    except Exception:
        pass

def _check_continue():
    """Wait until continue file appears if stop is active"""
    try:
        if STOP_FILE and os.path.exists(STOP_FILE):
            while not (CONTINUE_FILE and os.path.exists(CONTINUE_FILE)):
                time.sleep(0.05)
            # Resume → remove stop file
            try:
                os.remove(STOP_FILE)
            except:
                pass
    except Exception:
        pass

def _sleep_with_pause_check(duration, check_interval=0.01):
    elapsed = 0.0
    while elapsed < duration:
        _maybe_pause()
        _check_continue()
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
#   MANHATTAN HEURISTIC
# ================================
def heuristic_puzzle(state):
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0: 
            continue
        r, c = divmod(index, 4)
        gr, gc = divmod(tile - 1, 4)
        distance += abs(r - gr) + abs(c - gc)
    return distance

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
#   GREEDY BEST FIRST SEARCH
# ================================
def greedy_search(start):
    frontier = []
    heappush(frontier, (heuristic_puzzle(start), start))
    visited = set()
    parent = {tuple(start): None}

    nodes_expanded = 0

    while frontier:
        _maybe_pause()
        _check_continue()

        h, current = heappop(frontier)
        key = tuple(current)

        if key in visited:
            continue

        visited.add(key)
        nodes_expanded += 1

        try:
            print(f"STATE:{current}", flush=True)
        except Exception:
            pass

        try:
            time.sleep(0.01)
        except Exception:
            pass

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
    import sys

    try:
        puzzle_input = sys.stdin.readline().strip()
        if puzzle_input:
            puzzle = [int(x) for x in puzzle_input.split(',')]
        else:
            puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]
    except:
        puzzle = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15]

    print("Initial Puzzle:\n")
    display_puzzle(puzzle)

    start_time = time.time()

    parent, goal, nodes = greedy_search(puzzle)

    if goal:
        path = reconstruct_path(parent, goal)

        print("\nSolving with Greedy Best-First Search...")
        time.sleep(1)

        for step_i, step in enumerate(path):
            _maybe_pause()
            _check_continue()
            clear_screen()

            live_time = time.time() - start_time

            print(f"Step: {step_i + 1}/{len(path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")

            display_puzzle(step)
            _sleep_with_pause_check(0.10)

        final_time = time.time() - start_time

        print("Puzzle Solved!")
        print("Nodes Expanded:", nodes)
        print("Path Length:", len(path)-1)
        print(f"Total Time: {final_time:.6f} seconds")

    else:
        print("No solution found.")

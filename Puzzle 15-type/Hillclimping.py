import os
import time

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
#   HILL CLIMBING ALGORITHM
# ================================
def hill_climbing(start):
    current = start
    current_h = heuristic_puzzle(current)
    parent = {tuple(start): None}
    nodes_expanded = 0

    while True:
        _check_stop()
        _maybe_pause()
        nodes_expanded += 1

        # Emit current state so GUI can visualize exploration live
        try:
            print(f"STATE:{current}", flush=True)
        except Exception:
            pass
        try:
            time.sleep(0.02)
        except Exception:
            pass

        # Generate neighbors
        neighbors = neighbors_puzzle(current)

        best = current
        best_h = current_h

        for n, _ in neighbors:
            h = heuristic_puzzle(n)
            if h < best_h:      # Better state?
                best = n
                best_h = h
                parent[tuple(n)] = current

        # LOCAL MAXIMUM
        if best_h >= current_h:
            return parent, current, nodes_expanded, True

        # Move
        current = best
        current_h = best_h

        if goal_test_puzzle(current):
            return parent, current, nodes_expanded, False

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
#   MAIN + VISUALIZATION + TIMER
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

    print("Initial Puzzle:\n")
    display_puzzle(puzzle)

    start_time = time.time()

    parent, goal, nodes, local_max = hill_climbing(puzzle)

    if goal:
        path = reconstruct_path(parent, goal)

        print("\nSolving with Hill Climbing...\n")
        time.sleep(1)

        for step_i, step in enumerate(path):
            _maybe_pause()
            clear_screen()
            live_time = time.time() - start_time

            print(f"Step: {step_i + 1}/{len(path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")

            display_puzzle(step)
            _sleep_with_pause_check(0.10)

        final_time = time.time() - start_time

        if local_max:
            print("Reached Local Maximum — No better moves available.\n")
            print("Status: Unsolved (reached the local maximum)")

        print("Nodes Expanded:", nodes)
        print("Path Length:", len(path)-1)
        print(f"Total Time: {final_time:.6f} seconds")

    else:
        print("No solution found.")
else:
    print("No solution found.")

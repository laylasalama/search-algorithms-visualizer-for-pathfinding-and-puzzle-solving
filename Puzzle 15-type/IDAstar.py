import os
import random
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


def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass


def display_puzzle(tiles):
    for i in range(0, 16, 4):
        row = tiles[i:i+4]
        print(' '.join(f'{x:2d}' if x != 0 else '  ' for x in row))


# ================================
# 15-Puzzle Support for IDA*
# ================================


def goal_test(state):
    """Check if puzzle is solved."""
    return state == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0]


def get_neighbors(state):
    """Return all children of the current puzzle state."""
    neighbors = []
    blank = state.index(0)
    row, col = divmod(blank, 4)

    moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    for dr, dc in moves.values():
        nr, nc = row + dr, col + dc

        if 0 <= nr < 4 and 0 <= nc < 4:
            new_index = nr * 4 + nc

            new_state = state[:]
            new_state[blank], new_state[new_index] = new_state[new_index], new_state[blank]

            neighbors.append((new_state, 1))

    return neighbors


def heuristic(state):
    """Manhattan distance heuristic."""
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        r, c = divmod(index, 4)
        gr, gc = divmod(tile - 1, 4)
        distance += abs(r - gr) + abs(c - gc)
    return distance


# =====================================================
# UNIVERSAL IDA* TEMPLATE
# =====================================================


def IDA_star(start_state, goal_test, get_neighbors, heuristic):
    threshold = heuristic(start_state)
    path = [start_state]
    nodes_expanded = 0

    def search(g_cost, threshold):
        nonlocal nodes_expanded

        _check_stop()
        _maybe_pause()
        node = path[-1]
        f_cost = g_cost + heuristic(node)

        if f_cost > threshold:
            return f_cost

        if goal_test(node):
            return "FOUND"

        nodes_expanded += 1

        # Emit current state so GUI can visualize exploration live
        try:
            print(f"STATE:{node}", flush=True)
        except Exception:
            pass
        try:
            time.sleep(0.01)
        except Exception:
            pass

        min_threshold = float("inf")

        for neighbor, step_cost in get_neighbors(node):

            if neighbor in path:
                continue

            path.append(neighbor)
            result = search(g_cost + step_cost, threshold)

            if result == "FOUND":
                return "FOUND"

            if isinstance(result, (int, float)) and result < min_threshold:
                min_threshold = result

            path.pop()

        return min_threshold

    while True:
        result = search(0, threshold)

        if result == "FOUND":
            return path[:], nodes_expanded, len(path) - 1

        if result == float("inf"):
            return None, nodes_expanded, None

        threshold = result


# =====================================================
# RUN IDA*
# =====================================================

if __name__ == "__main__":
    import sys
    # Read puzzle from stdin if provided by GUI, otherwise use default test puzzle
    try:
        puzzle_input = sys.stdin.readline().strip()
        if puzzle_input:
            puzzle = [int(x) for x in puzzle_input.split(',')]
        else:
            puzzle = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 0, 15]
    except:
        puzzle = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 0, 15]
    print("Generated Puzzle:\n")
    display_puzzle(puzzle)

    print("\nSolving puzzle using IDA*...\n")

    solution_path, nodes, cost = IDA_star(
        puzzle,
        goal_test,
        get_neighbors,
        heuristic
    )

    print("\n===================================")
    print("            IDA* RESULT")
    print("===================================\n")

    print("Nodes Expanded:", nodes)
    print("Path Length:", cost)

    print("\nSolution Steps:\n")

    if solution_path:
        start_time = time.time()
        for step in solution_path:
            _maybe_pause()
            clear_screen()      
            live_time = time.time() - start_time

            print(f"step: {solution_path.index(step)+1}/{len(solution_path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")
            display_puzzle(step)
            print()
            _sleep_with_pause_check(0.1)
    else:
        print("No solution found.")
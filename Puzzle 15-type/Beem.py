import random                              
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

#===========================================================================================
#===================================== BEAM SEARCH =========================================
#===========================================================================================

def beam_search(start, goal, neighbors_fn, heuristic_fn, beam_width, delay=0.0, render_fn=None, timeout=None):
    beam = [(start, [start], heuristic_fn(start, goal))]
    visited = set([tuple(start) if isinstance(start, list) else start])
    frontiers_log = []
    visited_order = []

    start_time = time.time() if timeout is not None else None

    while beam:
        _check_stop()
        _maybe_continue()

        frontiers_log.append([node for node, _, _ in beam])

        for node, path, h in beam:
            if node == goal or list(node) == list(goal):
                return {
                    "path": path,
                    "frontiers": frontiers_log,
                    "visited_order": visited_order,
                    "visited_count": len(visited_order)
                }

        candidates = []
        for node, path, h in beam:
            visited_order.append(node)

            if timeout is not None and start_time is not None:
                if time.time() - start_time > timeout:
                    return {
                        "timeout": True,
                        "path": None,
                        "frontiers": frontiers_log,
                        "visited_order": visited_order,
                        "visited_count": len(visited_order)
                    }

            if delay and delay > 0:
                _sleep_with_continue_check(delay)

            for child, cost in neighbors_fn(node):
                child_key = tuple(child) if isinstance(child, list) else child
                if child_key not in visited:
                    visited.add(child_key)
                    new_path = path + [child]
                    new_h = heuristic_fn(child, goal)

                    try:
                        print(f"STATE:{list(child)}")
                    except Exception:
                        pass
                    
                    candidates.append((child, new_path, new_h))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[2])
        beam = candidates[:beam_width]

    return None

# ============================
#   15-PUZZLE: NEIGHBORS
# ============================
def neighbors_fn_15puzzle(state):
    state = list(state) if isinstance(state, tuple) else state
    neighbors = []
    idx = state.index(0)
    row, col = divmod(idx, 4)
    moves = {
        "up": -4,
        "down": 4,
        "left": -1,
        "right": 1
    }
    for move, offset in moves.items():
        new_idx = idx + offset
        if move == "left" and col == 0: continue
        if move == "right" and col == 3: continue
        if move == "up" and row == 0: continue
        if move == "down" and row == 3: continue
        new_state = state[:]
        new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
        neighbors.append((new_state, 1))
    return neighbors

# ============================
#   15-PUZZLE: HEURISTIC
# ============================
goal_state_15 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0]

def heuristic_fn_15puzzle(state, goal):
    state = list(state) if isinstance(state, tuple) else state
    goal = list(goal) if isinstance(goal, tuple) else goal
    dist = 0
    for i, tile in enumerate(state):
        if tile == 0:
            continue
        goal_index = goal.index(tile)
        dist += abs(goal_index//4 - i//4) + abs(goal_index%4 - i%4)
    return dist

# ============================
#   15-PUZZLE: DISPLAY
# ============================
def display_puzzle(tiles):
    for i in range(0, 16, 4):
        row = tiles[i:i+4]
        print(" ".join(f"{x:2d}" if x != 0 else "  " for x in row))

# ============================
#   15-PUZZLE: SOLVER
# ============================
def solve_15puzzle(puzzle, beam_width=5, delay=0.0, timeout=15, render_fn=None):
    result = beam_search(
        start=puzzle,
        goal=goal_state_15,
        neighbors_fn=neighbors_fn_15puzzle,
        heuristic_fn=heuristic_fn_15puzzle,
        beam_width=beam_width,
        delay=delay,
        render_fn=render_fn,
        timeout=timeout
    )
    return result


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

    print("Generated 15-puzzle:")
    display_puzzle(puzzle)
    
    result = solve_15puzzle(puzzle, beam_width=5, delay=0.03, timeout=15, render_fn=None)
    
    if result and isinstance(result, dict) and result.get('path'):
        path = result['path']
        print(f"\nNodes Expanded: {result.get('visited_count', 0)}")
        print(f"Path Length: {len(path)-1}")
        for step in path:
            _check_stop()
            _maybe_continue()
            print(f"STATE:{step}")
            display_puzzle(step)
            _sleep_with_continue_check(0.05)

    elif result and isinstance(result, dict) and result.get('timeout'):
        print(f"Nodes Expanded: {result.get('visited_count', 0)}")
        print("Status: Unsolved (timeout)")
    else:
        print("Status: Unsolved (no solution found)")

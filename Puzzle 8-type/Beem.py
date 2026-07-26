import random                              #To import random costs 
import os                                  #clear terminal screen 
import time                                #measure time for algorithms
from collections import deque
#===========================================================================================
#===================================== BEAM SEARCH =========================================
#===========================================================================================

def beam_search(start, goal, neighbors_fn, heuristic_fn, beam_width, delay=0.0, render_fn=None, timeout=None):
    beam = [(start, [start], heuristic_fn(start, goal))]
    visited = set([start])
    frontiers_log = []
    visited_order = []

    start_time = time.time() if timeout is not None else None

    while beam:
        frontiers_log.append([node for node, _, _ in beam])

        for node, path, h in beam:
            if node == goal:
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
                time.sleep(delay)

            for child, cost in neighbors_fn(node):
                if child not in visited:
                    visited.add(child)
                    new_path = path + [child]
                    new_h = heuristic_fn(child, goal)

                    # Always emit STATE for live visualization in GUI
                    try:
                        print(f"STATE:{child}")
                    except Exception:
                        pass
                    
                    # Also call render_fn if provided
                    if render_fn is not None:
                        render_fn(child)

                    candidates.append((child, new_path, new_h))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[2])
        beam = candidates[:beam_width]

    return None
# ============================
#   8-PUZZLE: SOLVABILITY
# ============================
def count_inversions_8(tiles):
    """Count inversions in puzzle to check solvability"""
    inv_count = 0
    nums = [t for t in tiles if t != 0]
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] > nums[j]:
                inv_count += 1
    return inv_count

def is_solvable_8(tiles):
    """Check if 8-puzzle is solvable"""
    return count_inversions_8(tiles) % 2 == 0

def generate_solvable_puzzle_8():
    """Generate a solvable 8-puzzle"""
    while True:
        tiles = list(range(9))
        random.shuffle(tiles)
        if is_solvable_8(tiles):
            return tiles

def display_puzzle_8(tiles):
    """Display 8-puzzle in grid format"""
    for i in range(0, 9, 3):
        print(" ".join(str(x) if x != 0 else " " for x in tiles[i:i+3]))
    print("-------------------------------")

# ============================
#   8-PUZZLE: NEIGHBORS
# ============================
def neighbors_fn_8puzzle(state):
    """Get valid neighbors for 8-puzzle state"""
    state = list(state)
    neighbors = []

    idx = state.index(0)
    row, col = divmod(idx, 3)

    moves = {
        "up": -3,
        "down": 3,
        "left": -1,
        "right": 1
    }

    for move, offset in moves.items():
        new_idx = idx + offset

        # Boundaries
        if move == "left" and col == 0: continue
        if move == "right" and col == 2: continue
        if move == "up" and row == 0: continue
        if move == "down" and row == 2: continue

        # Create new state
        new_state = state[:]
        new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
        neighbors.append((tuple(new_state), 1))  # cost = 1

    return neighbors


# ============================
#   8-PUZZLE: HEURISTIC
# ============================
goal_state_8 = (1,2,3,4,5,6,7,8,0)

def heuristic_fn_8puzzle(state, goal):
    """Manhattan distance heuristic for 8-puzzle"""
    dist = 0
    for i, tile in enumerate(state):
        if tile == 0:
            continue
        goal_index = goal.index(tile)
        dist += abs(goal_index//3 - i//3) + abs(goal_index%3 - i%3)
    return dist


# ============================
#   8-PUZZLE: SOLVER
# ============================
def solve_8puzzle(puzzle, beam_width=3, delay=0.0, render_fn=None, timeout=None):
    """Solve 8-puzzle using beam search"""
    result = beam_search(
        start=puzzle,
        goal=goal_state_8,
        neighbors_fn=neighbors_fn_8puzzle,
        heuristic_fn=heuristic_fn_8puzzle,
        beam_width=beam_width,
        delay=delay,
        render_fn=render_fn,
        timeout=timeout
    )
    return result

#=============================
#        RENDER STEP 
#=============================
def render_step(state):
    # Avoid clearing the terminal in subprocess mode; just print the state for GUI
    try:
        print(f"STATE:{state}")
        print_puzzle_grid_8(state)
    except Exception:
        pass
    time.sleep(0.2)  # Control speed

# ============================
#   8-PUZZLE: DISPLAY
# ============================
def print_puzzle_grid_8(state):
    """Print a puzzle state in grid format"""
    n = len(state)
    side = int(n ** 0.5)
    if side * side != n:
        print(state)
        return
    
    for r in range(side):
        row = state[r*side:(r+1)*side]
        print(' '.join(f"{x if x != 0 else ' ':>2}" for x in row))
    print()


if __name__ == "__main__":
    # Test the 8-puzzle
    puzzle = tuple(generate_solvable_puzzle_8())
    print("Generated puzzle:")
    display_puzzle_8(puzzle)
    
    result = solve_8puzzle(puzzle, beam_width=3, delay=0.06, render_fn=render_step, timeout=10)
    
    if result and isinstance(result, dict) and result.get('path'):
        path = result['path']
        print(f"\nNodes Expanded: {result.get('visited_count', 0)}")
        print(f"Path Length: {len(path)-1}")
        for step in path:
            print(f"STATE:{step}")
            print_puzzle_grid_8(step)
            time.sleep(0.05)
    elif result and isinstance(result, dict) and result.get('timeout'):
        print(f"Nodes Expanded: {result.get('visited_count', 0)}")
        print("Status: Unsolved (timeout)")
    else:
        print("Status: Unsolved (no solution found)")

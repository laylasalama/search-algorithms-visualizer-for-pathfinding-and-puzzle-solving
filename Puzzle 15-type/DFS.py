#=========================================================================#
#=======================puzzle_15 of dfs===================================#
#=========================================================================#
import random
import time
import os

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
    """Sleep while frequently checking for continue + stop file"""
    elapsed = 0.0
    while elapsed < duration:
        _maybe_continue()
        _check_stop()
        sleep_time = min(check_interval, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time


# ================================
#  15-Puzzle Utilities
# ================================
def count_inversions(tiles):
    inv_count = 0
    nums = [t for t in tiles if t != 0]
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] > nums[j]:
                inv_count += 1
    return inv_count

def is_solvable(tiles):
    return count_inversions(tiles) % 2 == 0

def generate_solvable_puzzle():
    while True:
        tiles = list(range(16))
        random.shuffle(tiles)
        if is_solvable(tiles):
            return tiles

def display_puzzle(tiles):
    for i in range(0, 16, 4):
        row = tiles[i:i+4]
        print(' '.join(f'{x:2d}' if x != 0 else '  ' for x in row))
    print()

# ================================
#  BFS / DFS Support
# ================================
def goal_test(state):
    return state == [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0]

def get_neighbors(state):
    neighbors = []
    blank = state.index(0)
    row, col = divmod(blank, 4)
    moves = [(-1,0),(1,0),(0,-1),(0,1)]  # UP, DOWN, LEFT, RIGHT

    for dr, dc in moves:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            new_index = nr * 4 + nc
            new_state = state[:]
            new_state[blank], new_state[new_index] = new_state[new_index], new_state[blank]
            neighbors.append((new_state, 1))
    return neighbors

# ================================
#  DFS Algorithm with Visualization
# ================================
def dfs_puzzle(start_state, timeout=30, delay=0.25):
    start_time = time.time()
    stack = [(start_state, 0)]  # state, depth
    parent = {tuple(start_state): None}
    visited = set()
    nodes_expanded = 0

    while stack:
        _check_stop()
        _maybe_continue()

        current, depth = stack.pop()
        key = tuple(current)
        nodes_expanded += 1

        try:
            print(f"STATE:{current}", flush=True)
        except Exception:
            pass

        try:
            _sleep_with_continue_check(0.02)
        except Exception:
            pass

        if goal_test(current):
            path = []
            state = current
            while state is not None:
                path.append(state)
                state = parent[tuple(state)]
            path.reverse()
            return path, nodes_expanded

        if key not in visited:
            visited.add(key)
            for neighbor, _ in reversed(get_neighbors(current)):
                nkey = tuple(neighbor)
                if nkey not in visited:
                    parent[nkey] = current
                    stack.append((neighbor, depth+1))

        if time.time() - start_time > timeout:
            return None, nodes_expanded

    return None, nodes_expanded

# ================================
#  MAIN
# ================================
import sys

try:
    puzzle_input = sys.stdin.readline().strip()
    if puzzle_input:
        puzzle = [int(x) for x in puzzle_input.split(',')]
    else:
        puzzle = generate_solvable_puzzle()
except:
    puzzle = generate_solvable_puzzle()

print("Generated Puzzle:\n")
display_puzzle(puzzle)
time.sleep(1)

print("Solving puzzle using Depth-First Search (DFS)...\n")
solution_path, nodes = dfs_puzzle(puzzle, timeout=30, delay=0.1)

if solution_path:
    print("\nPuzzle Solved!")
    print("Nodes Expanded:", nodes)
    print("Path Length:", len(solution_path)-1)
    print("\nSolution Steps:\n")
    for step in solution_path:
        _check_stop()
        _maybe_continue()
        print(f"STATE:{step}")
        display_puzzle(step)
        _sleep_with_continue_check(0.05)
else:
    print("\nNo solution found within the time limit.")
    print("Nodes Expanded:", nodes)

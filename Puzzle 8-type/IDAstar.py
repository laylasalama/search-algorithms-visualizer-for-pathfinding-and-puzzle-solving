import os
import random
import time


def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass


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
        tiles = list(range(9))
        random.shuffle(tiles)
        if is_solvable(tiles):
            return tiles


def display_puzzle(tiles):
    for i in range(0, 9, 3):
        row = tiles[i:i+3]
        print(' '.join(str(x) if x != 0 else ' ' for x in row))


# ================================
# 8-PUZZLE Support for IDA*
# ================================


def goal_test(state):
    """Check if puzzle is solved."""
    return state == [1, 2, 3, 4, 5, 6, 7, 8, 0]


def get_neighbors(state):
    """Return all children of the current puzzle state."""
    neighbors = []
    blank = state.index(0)
    row, col = divmod(blank, 3)

    moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }

    for dr, dc in moves.values():
        nr, nc = row + dr, col + dc

        if 0 <= nr < 3 and 0 <= nc < 3:
            new_index = nr * 3 + nc

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
        r, c = divmod(index, 3)
        gr, gc = divmod(tile - 1, 3)
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

        node = path[-1]
        f_cost = g_cost + heuristic(node)

        if f_cost > threshold:
            return f_cost

        if goal_test(node):
            return "FOUND"

        nodes_expanded += 1
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
    puzzle = generate_solvable_puzzle()
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
            clear_screen()      #Clear terminal screen
            live_time = time.time() - start_time

            print(f"step: {solution_path.index(step)+1}/{len(solution_path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")
            display_puzzle(step)
            print()
            time.sleep(0.1)   # <<< SLEEP ADDED HERE
    else:
        print("No solution found.")


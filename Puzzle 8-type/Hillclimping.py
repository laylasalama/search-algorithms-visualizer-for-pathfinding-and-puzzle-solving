import os
import time

# ================================
#   CLEAR SCREEN
# ================================
def clear_screen():
    # Disabled for subprocess - clearing screen blocks I/O
    pass
 #os.system("clear")   LINUX

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
#   MANHATTAN HEURISTIC
# ================================
def heuristic_puzzle(state):
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0: 
            continue
        r, c = divmod(index, 3)
        gr, gc = divmod(tile - 1, 3)
        distance += abs(r - gr) + abs(c - gc)
    return distance

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
        nodes_expanded += 1

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
    puzzle = [1,4,2,3,7,5,6,0,8]

    print("Initial Puzzle:\n")
    display_puzzle(puzzle)

    start_time = time.time()

    parent, goal, nodes, local_max = hill_climbing(puzzle)

    if goal:
        path = reconstruct_path(parent, goal)

        print("\nSolving with Hill Climbing...\n")
        time.sleep(1)

        for step_i, step in enumerate(path):
            clear_screen()
            live_time = time.time() - start_time

            print(f"Step: {step_i + 1}/{len(path)}")
            print(f"Time Elapsed: {live_time:.4f} seconds\n")
            print(f"STATE:{step}")

            display_puzzle(step)
            time.sleep(0.10)

        final_time = time.time() - start_time

        if local_max:
            print("Reached Local Maximum — No better moves available.\n")
            print("Status: Unsolved (reached the local maximum)")

        print("Nodes Expanded:", nodes)
        print("Path Length:", len(path)-1)
        print(f"Total Time: {final_time:.6f} seconds")

    else:
        print("No solution found.")

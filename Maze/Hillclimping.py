import random
import os
import time

#===========================================================================================
#=========================================DIRECTIONS========================================
#===========================================================================================
DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East": (1, 0),
    "West": (-1, 0)
}

OPPOSITE = {"North":"South", "South":"North", "East":"West", "West":"East"}

#===========================================================================================
#=========================================MAZE RENDER(ASCII)===============================
#===========================================================================================
def render_maze(maze, width, height):
    out = "+"
    out += "---+" * width + "\n"
    for y in range(height):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x,y)]
            row1 += "   "
            row1 += " " if cell["East"] == False else "|"
            row2 += "   " if cell["South"] == False else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"
    return out

#===========================================================================================
#=========================================MAZE GENERATION===================================
#===========================================================================================
def generate_maze(width, height):
    maze = { (x,y): {"North":True, "South":True, "East":True, "West":True} 
             for y in range(height) for x in range(width) }
    visited = set()
    stack = []
    x, y = random.randint(0,width-1), random.randint(0,height-1)
    stack.append((x,y))
    visited.add((x,y))

    while stack:
        os.system("cls" if os.name == "nt" else "clear")
        print(render_maze(maze, width, height))
        time.sleep(0.003)
        x, y = stack[-1]

        neighbors = []
        for d,(dx, dy) in DIRECTIONS.items():
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                neighbors.append((d, nx, ny))
        if neighbors:
            d, nx, ny = random.choice(neighbors)
            maze[(x,y)][d] = False
            maze[(nx,ny)][OPPOSITE[d]] = False
            visited.add((nx,ny))
            stack.append((nx,ny))
        else:
            stack.pop()
    return maze

#===========================================================================================
#==================================GET NEIGHBORS & HEURISTIC===============================
#===========================================================================================
def get_neighbors(cell, maze):
    """Return neighboring cells that can be moved to (no wall)."""
    x, y = cell
    neighbors = []
    for d, (dx, dy) in DIRECTIONS.items():
        if not maze[(x, y)][d]:
            nx, ny = x + dx, y + dy
            neighbors.append((nx, ny))
    return neighbors

def heuristic(cell, goal):
    """Manhattan distance."""
    x, y = cell
    gx, gy = goal
    return abs(x - gx) + abs(y - gy)

#===========================================================================================
#=========================================HILL CLIMBING====================================
#===========================================================================================
def hill_climbing(start, goal, maze):
    current = start
    path = [current]

    while True:
        if current == goal:
            return path, len(path)

        neighbors = get_neighbors(current, maze)
        if not neighbors:
            return path, -1

        best = min(neighbors, key=lambda x: heuristic(x, goal))

        if heuristic(best, goal) >= heuristic(current, goal):
            return path, -1

        current = best
        path.append(current)

def measure_time(start, goal, maze):
    t0 = time.perf_counter()
    path, cost = hill_climbing(start, goal, maze)
    t1 = time.perf_counter()
    return path, cost, t1 - t0

#===========================================================================================
#=========================================START / GOAL INPUT================================
#===========================================================================================
def input_start_goal(width, height):
    print(f"Maze size: {width}x{height}")
    print("Enter coordinates as: x y")
    while True:
        try:
            sx, sy = map(int, input("Start (x y): ").split())
            gx, gy = map(int, input("Goal  (x y): ").split())
        except:
            print("Invalid input. Enter two integers.")
            continue

        if not (0 <= sx < width and 0 <= sy < height and 0 <= gx < width and 0 <= gy < height):
            print("Coordinates out of range.")
            continue

        return (sx, sy), (gx, gy)

#===========================================================================================
#===========================================MAIN============================================
#===========================================================================================
def main():
    print("Maze Generator and Hill Climbing:\n")
    width = int(input("Maze width: "))
    height = int(input("Maze height: "))

    maze = generate_maze(width, height)
    print("\nGenerated maze:")
    print(render_maze(maze, width, height))

    start, goal = input_start_goal(width, height)

    path, cost, elapsed = measure_time(start, goal, maze)

    print("\n===== Hill Climbing Result =====")
    if cost == -1:
        print("Reached a local maximum before reaching the goal.")
        print("Path:", path)
    else:
        print("Path:", path)
        print("Path length:", cost)
    print("Time elapsed:", round(elapsed,6), "seconds")

#===========================================================================================
#=============================RUN PROGRAM===============================================
#===========================================================================================
if __name__ == "__main__":
    main()

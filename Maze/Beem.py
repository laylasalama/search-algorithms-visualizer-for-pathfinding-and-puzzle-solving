import random
import os
import time

#===========================================================================================
#                                   BEAM SEARCH
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
                    candidates.append((child, new_path, new_h))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[2])
        beam = candidates[:beam_width]

    return None

#===========================================================================================
#                                         DIRECTIONS
#===========================================================================================

DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East":  (1, 0),
    "West":  (-1, 0)
}

OPPOSITE = {"North":"South", "South":"North", "East":"West", "West":"East"}

#===========================================================================================
#                                     MAZE RENDERING
#===========================================================================================

def render_maze(maze, width, height):
    out = "+" + "---+" * width + "\n"
    for y in range(height):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x,y)]
            row1 += "   "
            row1 += " " if not cell["East"] else "|"
            row2 += "   " if not cell["South"] else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"
    return out

def render_maze_with_path(maze, width, height, path=None, start=None, goal=None):
    path_set = set(path) if path else set()
    out = "+" + "---+" * width + "\n"

    for y in range(height):
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x, y)]
            if (x, y) == start:
                row1 += " S "
            elif (x, y) == goal:
                row1 += " G "
            elif (x, y) in path_set:
                row1 += " * "
            else:
                row1 += "   "

            row1 += " " if not cell["East"] else "|"
            row2 += "   " if not cell["South"] else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"

    return out

#===========================================================================================
#                                     MAZE GENERATION
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
        os.system("clear")
        print(render_maze(maze, width, height))
        time.sleep(0.001)

        x, y = stack[-1]
        neighbors = []

        for d,(dx,dy) in DIRECTIONS.items():
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height and (nx,ny) not in visited:
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
#                                     INPUT START/GOAL
#===========================================================================================

def input_start_goal(width, height):
    print(f"Maze size: {width}x{height}")
    print("Enter coordinates as: x y")

    while True:
        try:
            sx, sy = map(int, input("Start (x y): ").split())
            gx, gy = map(int, input("Goal  (x y): ").split())
        except:
            print("Invalid format. Enter two integers.")
            continue

        if not (0 <= sx < width and 0 <= sy < height and 0 <= gx < width and 0 <= gy < height):
            print("Coordinates out of range.")
            continue

        return (sx, sy), (gx, gy)

#===========================================================================================
#                                NEIGHBORS & HEURISTIC
#===========================================================================================

def maze_neighbors(node, maze):
    x, y = node
    for direction, (dx, dy) in DIRECTIONS.items():
        if maze[(x,y)][direction] == False:
            nx, ny = x+dx, y+dy
            yield ( (nx, ny), 1 )

def maze_heuristic(node, goal):
    x1, y1 = node
    x2, y2 = goal
    return abs(x1 - x2) + abs(y1 - y2)

#===========================================================================================
#                                  BEAM SEARCH WRAPPER
#===========================================================================================

def run_beam(maze, start, goal):
    result = beam_search(
        start=start,
        goal=goal,
        neighbors_fn=lambda n: maze_neighbors(n, maze),
        heuristic_fn=maze_heuristic,
        beam_width=5
    )

    if result is None or "path" not in result:
        return [], 0, 0

    path = result["path"]
    nodes = result["visited_count"]
    return path, nodes, len(path)

#===========================================================================================
#                                         MAIN
#===========================================================================================

if __name__ == "__main__":
    width = int(input("Maze width: "))
    height = int(input("Maze height: "))

    maze = generate_maze(width, height)

    start, goal = input_start_goal(width, height)

    path, nodes, cost = run_beam(maze, start, goal)

    print("\n=== RESULT ===")
    print("Nodes Expanded:", nodes)
    print("Path Length:", cost)
    print(render_maze_with_path(maze, width, height, path, start, goal))

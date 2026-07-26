
import random   #to can select a random points 
#directions of DX ,DY
import heapq 
         #priority queue for Greedy Algorithm
import os                                  #clear terminal screen (LINUX) 
#os.system("cls" if os.name == "nt" else "clear")    we use this if it was (WINDOWS)
import time                                #measure time for algorithms
#===========================================================================================
#=========================================DIRECTIONS========================================
#===========================================================================================
DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East": (1, 0),
    "West": (-1, 0)
}
#===========================================================================================
#=========================================MAZE RENDER(ASCII)===============================
#===========================================================================================

#the opposite direction
OPPOSITE = {"North":"South", "South":"North", "East":"West", "West":"East"}
def render_maze(maze, width, height):
    out = ""
    # the first one
    out += "+" + "---+" * width + "\n"
    for y in range(height):
        row1 = "|"    #Vertical walls row
        row2 = "+"    #Horizontal walls row
        for x in range(width):   
            cell = maze[(x,y)]    #  x->x_axis ,y->y_axis
            # empty spaces in the cell
            row1 += "   "
            #East wall
            row1 += " " if cell["East"] == False else "|"
            #South wall
            row2 += "   " if cell["South"] == False else "---"
            row2 += "+"
        out += row1 + "\n"
        out += row2 + "\n"
    return out

#===========================================================================================
#=========================================MAZE GENERATION===================================
#===========================================================================================

def generate_maze(width, height):
    #create maze structure that every cell has 4 walls 
    maze = { (x,y): {"North":True, "South":True, "East":True, "West":True} 
             for y in range(height) for x in range(width) }
    visited = set()     #track visited cells
    stack = []          #DFS stack
    #select a random cell in the first 
    x, y = random.randint(0,width-1), random.randint(0,height-1) #random cell
    stack.append((x,y))
    visited.add((x,y))
        # DFS for maze ----------------example algorithm----------------
    while stack:
       #os.system("clear")       #clear the screen (only linux)
        os.system("cls" if os.name == "nt" else "clear") #clear the screen (windows or linux)
        print(render_maze(maze, width, height))
        time.sleep(0.003)         #  display maze step by step
        x, y = stack[-1]
        #has related with dfs algorithm
        # find the neighbors that cannot visit
        neighbors = []
        for d,(direction_x_axis,direction_y_axis) in DIRECTIONS.items():# dx is change in x_axis & dy is change in y_axis
            new_x_axis, new_y_axis = x+direction_x_axis, y+direction_y_axis  #nx is new x_axis & ny is new y_axis
            if 0 <= new_x_axis < width and 0 <= new_y_axis < height and (new_x_axis,new_y_axis) not in visited:
                neighbors.append((d, new_x_axis, new_y_axis))
                #choose randomly if the unvisited neighbors exist
        if neighbors:
            d, new_x_axis, new_y_axis = random.choice(neighbors) #d is direction
            # Remove wall between current and next cell
            maze[(x,y)][d] = False   #break wall from current cell
            maze[(new_x_axis,new_y_axis)][OPPOSITE[d]] = False #break wall from the other side
            visited.add((new_x_axis,new_y_axis))
            stack.append((new_x_axis,new_y_axis))
        else:
            #back track
            stack.pop()
    return maze
#=====================can add more algorithms for maze here:)===============================
#=========================Greedy Algorithm===========================
def get_neighbors_maze(cell, maze):
    x, y = cell
    neighbors_greedy = []

    for d, (direction_x_axis, direction_y_axis) in DIRECTIONS.items():
        if maze[(x, y)][d] == False:  # no wall
            new_x_axis, new_y_axis = x + direction_x_axis, y + direction_y_axis
            neighbors_greedy.append((new_x_axis, new_y_axis))

    return neighbors_greedy


def heuristic_maze(cell, goal):
    x, y = cell
    goal_x_axis, goal_y_axis = goal
    return abs(x - goal_x_axis) + abs(y - goal_y_axis)   # Manhattan


def is_goal_maze(cell, goal):
    return cell == goal

def greedy_search(start, goal, get_neighbors, heuristic, is_goal):
    frontier = []
    heapq.heappush(frontier, (heuristic(start, goal), start))

    came_from = {start: None}
    nodes_expanded = 0
    visited = set()
    start_time = time.time()

    while frontier:
        _, current = heapq.heappop(frontier)

        if current in visited:
            continue
        visited.add(current)

        nodes_expanded += 1

        if is_goal(current, goal):
            # reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path, nodes_expanded, len(path)

        for nxt in get_neighbors(current):
            if nxt not in visited:
                came_from[nxt] = current
                heapq.heappush(frontier, (heuristic(nxt, goal), nxt))

    return [], nodes_expanded, None

#===========================================================================================
#=================== RENDER MAZE WITH PATH / START(S) / GOAL(G) ============================
#===========================================================================================
def render_maze_with_path(maze, width, hight, path=None, start=None, goal=None):
    path_set = set(path) if path else set() #convert path to set for faster lookup
     # the first one
    out = "+" + "---+" * width + "\n"

    for y in range(hight): #y is y_axis
        row1 = "|"
        row2 = "+"
        for x in range(width):
            cell = maze[(x, y)] # x is x_axis ,y is y_axis
# draw the info in the maze
            if (x, y) == start:
                row1 += " S "
            elif (x, y) == goal:
                row1 += " G "
            elif (x, y) in path_set:
                row1 += " * "
            else:
                row1 += "   "
#East &South walls
            row1 += " " if not cell["East"] else "|"
            row2 += "   " if not cell["South"] else "---"
            row2 += "+"
        out += row1 + "\n" + row2 + "\n"

    return out

#===========================================================================================
#================================ START / GOAL INPUT =======================================
#===========================================================================================
def input_start_goal(maze, width, hight):
    print(f"Maze size: {width}x{hight}")
    print("Enter coordinates as: x y")
#print the size of the maze and how to enter the coordinates
    while True:
        try:
            start_x_axis, start_y_axis = map(int, input("Start (x y): ").split())   #start of x,start of y
            goal_x_axis, goal_y_axis = map(int, input("Goal  (x y): ").split())   #goal of x,goal of y
        except:
            print("Invalid format. Enter two integers.")
            continue

        if not (0 <= start_x_axis < width and 0 <= start_y_axis < hight and 0 <= goal_x_axis < width and 0 <= goal_y_axis < hight):
            print("Coordinates out of range.")
            continue

        return (start_x_axis, start_y_axis), (goal_x_axis, goal_y_axis)

#===========================================================================================
#=============================== PRINT RESULTS TABLE ========================================
#===========================================================================================
def print_results_table(results):
    header = f"{'Algorithm':10} | {'Time (s)':>9} | {'Nodes':>8} | {'PathLen':>7} | {'Cost':>6}"
    print(header)
    print("-" * len(header))
    for name, stats in results.items():
        print(f"{name:10} | "
              f"{stats['time']:.6f} | "
              f"{stats['nodes_expanded']:>8} | "
              f"{stats['path_length']:>7} | "
              f"{stats['cost'] if stats['cost'] is not None else 'N/A':>6}") #none->N/A
#===========================================================================================
#=============================== definition of algorithms ======================================
#===========================================================================================
# These functions will later be replaced with real implementations.
def BFS(maze, start, goal): return [], 0, 0
def DFS(maze, start, goal): return [], 0, 0
def UCS(maze, start, goal): return [], 0, 0
#======================================================================
#===========================return Greedy Search ======================
#======================================================================
#def Greedy(maze, start, goal): return [], 0, 0
def Greedy(maze, start, goal):
    path, nodes, cost = greedy_search(
        start,
        goal,
        lambda cell: get_neighbors_maze(cell, maze), #lambda function to get neighbors
        heuristic_maze,
        is_goal_maze
    )
    return path, nodes, cost
#=======================================================================
def A(maze, start, goal): return [], 0, 0   # insted of A*
def IDA(maze, start, goal): return [], 0, 0
def Hill(maze, start, goal): return [], 0, 0
def Beam(maze, start, goal): return [], 0, 0

#===========================================================================================
#=============================== RUN SINGLE ALGORITHM ======================================
#===========================================================================================
def run_single_algorithm(choice, maze, start, goal, width, hight):
    mapping = {
    "1": ("BFS", BFS),
    "2": ("DFS", DFS),
    "3": ("UCS", UCS),
    "4": ("Greedy", Greedy),
    "5": ("A*", A),
    "6": ("IDA*", IDA),
    "7": ("Hill Climbing", Hill),
    "8": ("Beam", Beam)
    }

    if choice not in mapping:
        return None
    name, function = mapping[choice]

    t0 = time.perf_counter()
    path, nodes_expanded, cost = function(maze, start, goal)
    t1 = time.perf_counter()

    stats = {
        "time": t1 - t0,
        "nodes_expanded": nodes_expanded,
        "path_length": len(path) if path else 0,    #len->length
        "cost": cost,
        "path": path
    }
    
    # ======================
    #  LIVE VISUALIZATION (PUZZLE-LIKE STYLE)
    # ======================
    if name == "Greedy" and stats["path"]:
        print("\n Visualizing Greedy search...\n")
        time.sleep(1)

        start_time = time.time()

        for i, cell in enumerate(stats["path"]):
            os.system("cls" if os.name == "nt" else "clear")

            live_time = time.time() - start_time

            print(f"────────── GREEDY SEARCH ──────────")
            print(f"Step: {i+1}/{len(stats['path'])}")
            print(f"Elapsed Time: {live_time:.4f}s")
            print(f"Current Cell: {cell}")
            print(f"────────────────────────────────────\n")

            # render exactly like puzzle animation style
            print(render_maze_with_path(
                maze,
                width,
                hight,
                path=stats["path"][:i+1],
                start=start,
                goal=goal
            ))

            time.sleep(0.20)

        print("\n Greedy Completed!")

    return name, stats

#===========================================================================================
#==================================== INTERACTIVE MENU =====================================
#===========================================================================================
def interactive_menu(maze, width, hight, start, goal):

    results = {}

    menu = """
Choose algorithm:
1) BFS
2) DFS
3) UCS
4) Greedy
5) A*
6) IDA*
7) Hill Climbing
8) Beam
9) Compare results
10) Exit
>>> """

    while True:
        choice = input(menu).strip()

        if choice == "10":
            print("Exiting.")
            break

        if choice == "9":
            if results:
                print_results_table(results)
            else:
                print("No algorithms run yet.")
            continue

        sel = run_single_algorithm(choice, maze, start, goal, width, hight)

        if sel is None:
            print("Invalid choice.")
            continue

        name, stats = sel
        results[name] = stats

        print(f"\n*** Result of {name} ***")
        if not stats["path"]:
            print("No path found.")
            continue

        print(f"Time: {stats['time']:.6f}s")
        print(f"Nodes Expanded: {stats['nodes_expanded']}")
        print(f"Path Length: {stats['path_length']}")
        print(f"Cost: {stats['cost']}")

        print("\nMaze with path:")
        print(render_maze_with_path(maze, width, hight, stats["path"], start, goal))

#===========================================================================================
#========================================== MAIN ===========================================
#===========================================================================================
def main():
    print("Maze Generator :\n")
    width = int(input("Maze width: "))
    hight = int(input("Maze height: "))
  #  print("\nGenerating...")
    maze = generate_maze(width, hight)
    print("\nGenerated maze:")
    print(render_maze(maze, width, hight))
    
    start, goal = input_start_goal(maze, width, hight)
    interactive_menu(maze, width, hight, start, goal)
    
#================================================================
#================== main start program===========================
#================================================================
if __name__ == "__main__":
    main()
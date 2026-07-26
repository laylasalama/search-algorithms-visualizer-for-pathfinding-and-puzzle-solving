import time

def beam_search(start, goal, neighbors_fn, heuristic_fn, beam_width, delay=0.0, render_fn=None, timeout=None):
    beam = [(start, [start], 0, heuristic_fn(start, goal))]  # (node, path, cost_so_far, h)

    visited = set([start])        # global visited
    frontiers_log = []
    visited_order = []

    start_time = time.time() if timeout is not None else None

    while beam:
        frontiers_log.append([node for node, _, _, _ in beam])

        # Goal check
        for node, path, cost, h in beam:
            if node == goal:
                return {
                    "path": path,
                    "frontiers": frontiers_log,
                    "visited_order": visited_order,
                    "visited_count": len(visited_order),
                    "total_cost": cost
                }

        candidates = []

        for node, path, cost_so_far, h in beam:
            visited_order.append(node)

            # Timeout
            if timeout and time.time() - start_time > timeout:
                return {
                    "timeout": True,
                    "path": None,
                    "frontiers": frontiers_log,
                    "visited_order": visited_order,
                    "visited_count": len(visited_order)
                }

            if render_fn:
                render_fn(beam, frontiers_log, node, visited_order)

            if delay > 0:
                import time
                time.sleep(delay)

            # Expand neighbors
            for child, edge_cost in neighbors_fn(node):
                if child not in visited:
                    visited.add(child)
                    new_path = path + [child]
                    new_cost = cost_so_far + edge_cost
                    new_h = heuristic_fn(child, goal)
                    candidates.append((child, new_path, new_cost, new_h))

        if not candidates:
            return None

        # Sort by heuristic (best first)
        candidates.sort(key=lambda x: x[3])
        beam = candidates[:beam_width]

    return None


# --------------------------
# ROMANIA MAP SECTION
# --------------------------

graph = {
    'Arad': {'Zerind': 75, 'Timisoara': 118, 'Sibiu': 140},
    'Zerind': {'Arad': 75, 'Oradea': 71},
    'Oradea': {'Zerind': 71, 'Sibiu': 151},
    'Timisoara': {'Arad': 118, 'Lugoj': 111},
    'Lugoj': {'Timisoara': 111, 'Mehadia': 70},
    'Mehadia': {'Lugoj': 70, 'Dobreta': 75},
    'Dobreta': {'Mehadia': 75, 'Craiova': 120},
    'Craiova': {'Dobreta': 120, 'Rimnicu Vilcea': 146, 'Pitesti': 138},
    'Rimnicu Vilcea': {'Sibiu': 80, 'Craiova': 146, 'Pitesti': 97},
    'Sibiu': {'Arad': 140, 'Oradea': 151, 'Fagaras': 99, 'Rimnicu Vilcea': 80},
    'Fagaras': {'Sibiu': 99, 'Bucharest': 211},
    'Pitesti': {'Rimnicu Vilcea': 97, 'Craiova': 138, 'Bucharest': 101},
    'Bucharest': {'Fagaras': 211, 'Pitesti': 101, 'Giurgiu': 90, 'Urziceni': 85},
    'Giurgiu': {'Bucharest': 90},
    'Urziceni': {'Bucharest': 85, 'Hirsova': 98, 'Vaslui': 142},
    'Hirsova': {'Urziceni': 98, 'Eforie': 86},
    'Eforie': {'Hirsova': 86},
    'Vaslui': {'Urziceni': 142, 'Iasi': 92},
    'Iasi': {'Vaslui': 92, 'Neamt': 87},
    'Neamt': {'Iasi': 87},
}

def neighbors_fn(city):
    return [(n, c) for n, c in graph[city].items()]

heuristic_straight_line = {
    'Arad': 366, 'Zerind': 374, 'Oradea': 380, 'Timisoara': 329,
    'Lugoj': 244, 'Mehadia': 241, 'Dobreta': 242, 'Craiova': 160,
    'Rimnicu Vilcea': 193, 'Sibiu': 253, 'Fagaras': 176, 'Pitesti': 100,
    'Bucharest': 0, 'Giurgiu': 77, 'Urziceni': 80, 'Hirsova': 151,
    'Eforie': 161, 'Vaslui': 199, 'Iasi': 226, 'Neamt': 234
}

def heuristic_fn(city, goal):
    return heuristic_straight_line[city]


# -------------------------
# VISUALIZATION CALLBACK
# -------------------------

def visualize_step(beam, frontiers, current, visited):
    print("\n--- EXPANDING:", current, "---")
    print("Current Beam:", [b[0] for b in beam])
    print("Visited so far:", visited)
    print("-------------")


# -------------------------
# VISUALIZE FINAL PATH
# -------------------------

def print_path(path, total_cost):
    print("\n===== FINAL PATH =====")
    cost = 0
    for i in range(len(path)):
        if i == len(path) - 1:
            print(path[i])
        else:
            step_cost = graph[path[i]][path[i+1]]
            cost += step_cost
            print(f"{path[i]} --({step_cost})--> ", end="")
    print("======================")
    print(f"Total Cost from search: {total_cost}")
    print("======================\n")


# -------------------------
# MAIN
# -------------------------

print("Beam Search on Romania Map")
print("Available cities:", list(graph.keys()))
start = input("Enter start city: ")
goal = input("Enter goal city: ")

if start not in graph or goal not in graph:
    print("Invalid city name!")
    exit()

if start == goal:
    print("Start and goal cannot be the same.")
    exit()

result = beam_search(start, goal, neighbors_fn, heuristic_fn,
                     beam_width=5,
                     render_fn=visualize_step,
                     delay=0.3)

if result and "path" in result and result["path"]:
    print_path(result["path"], result["total_cost"])
else:
    print("No path found or pruned by beam search.")

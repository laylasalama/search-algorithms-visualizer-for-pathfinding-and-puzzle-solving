#greedy_best_first_search_romania

import math
import time
import heapq

#====================================================
# ================== Romania Graph ==================
#====================================================
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

coords = {
    "Arad": (46.1667, 21.3167),
    "Bucharest": (44.4268, 26.1025),
    "Craiova": (44.3167, 23.8000),
    "Dobreta": (44.6369, 22.6597),
    "Eforie": (44.0733, 28.6525),
    "Fagaras": (45.8416, 24.9731),
    "Giurgiu": (43.9000, 25.9667),
    "Hirsova": (44.6894, 27.9481),
    "Iasi": (47.1622, 27.5889),
    "Lugoj": (45.6886, 21.9031),
    "Mehadia": (44.9000, 22.3667),
    "Neamt": (46.9167, 26.3333),
    "Oradea": (47.0722, 21.9211),
    "Pitesti": (44.8565, 24.8692),
    "Rimnicu Vilcea": (45.0997, 24.3693),
    "Sibiu": (45.7928, 24.1522),
    "Timisoara": (45.7489, 21.2087),
    "Urziceni": (44.7167, 26.6333),
    "Vaslui": (46.6333, 27.7333),
    "Zerind": (46.6167, 21.5167)
}

def haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def heuristic(city, goal):
    return haversine(coords[city], coords[goal])

def get_neighbors(city):
    return [(neighbor, cost) for neighbor, cost in graph[city].items()]

#=========================================================
# =============== GREEDY BEST-FIRST SEARCH ===============
#=========================================================
def greedy_search(start, goal):
    frontier = []
    heapq.heappush(frontier, (heuristic(start, goal), start))

    visited = set()
    parent = {start: None}
    nodes_expanded = 0

    start_time = time.time()

    while frontier:
        h, current = heapq.heappop(frontier)

        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            # compute total cost
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()

            total_cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1))
            return path, nodes_expanded, total_cost

        nodes_expanded += 1

        print(f"\nVisiting: {current}  (h={round(h,2)})")
        time.sleep(0.25)

        for neighbor, cost in get_neighbors(current):
            if neighbor not in visited:
                parent[neighbor] = current
                heapq.heappush(frontier, (heuristic(neighbor, goal), neighbor))

        if time.time() - start_time > 10:
            return None, nodes_expanded, None

    return None, nodes_expanded, None

#=========================================================
# ================== PATH VISUALIZATION ==================
#=========================================================
def visualize_path(path):
    print("\nStep-by-step path progression:")
    for i in range(1, len(path)+1):
        print(" → ".join(path[:i]))

#=========================================================
# ===================== RUN SEARCH =======================
#=========================================================
print("\nAvailable Cities:")
print(" | ".join(graph.keys()))
print("\n  *** Write city names with Capital first letter *** .\n")

while True:
    start = input("Enter START city: ").strip()
    if start in graph: break
    print("Invalid city.\n")

while True:
    goal = input("Enter GOAL city: ").strip()
    if goal in graph: break
    print("Invalid city.\n")

print("\nRunning Greedy Best-First Search...\n")

start_time = time.time()

path, expanded, cost = greedy_search(start, goal)

elapsed = time.time() - start_time

print("\n========== RESULT ==========")

if elapsed > 10:
    print("Invalid algorithm: Execution time exceeded 10 seconds.")
elif path:
    print("Full Path:", " → ".join(path))
    print("Total cost:", cost)
    print("Nodes expanded:", expanded)
    print("Time taken:", round(elapsed, 6), "seconds")
    visualize_path(path)
else:
    print("No path found.")

print("============================")
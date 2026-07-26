import math
import time

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
#====================================================
# Coordinates for straight-line distance heuristic
#====================================================
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
    
    lat1, lon1 = coord1           # Extract latitude and longitude from the first coordinate tuple 
    lat2, lon2 = coord2             # Extract latitude and longitude from the second coordinate tuple
    R = 6371  # km                  # # Earth's radius in kilometers (used to convert angular distance to linear distance)
    dlat = math.radians(lat2 - lat1)    # Calculate the difference in latitude and convert it from degrees to radians
    dlon = math.radians(lon2 - lon1)     # Calculate the difference in longitude and convert it from degrees to radians

    # Apply the Haversine formula:
    # Compute 'a' as the square of half the latitude difference plus
    # the cosine of both latitudes multiplied by the square of half the longitude difference
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Compute 'c' as the angular distance in radians using the arctangent function

    return R * c            # Multiply by Earth's radius to get the distance in kilometers


def heuristic(city, goal):
    return haversine(coords[city], coords[goal])

def get_neighbors(city):
    return [(neighbor, cost) for neighbor, cost in graph[city].items()]
#=========================================================
# ==================== A* Algorithm ====================
#=========================================================
import heapq

def A_star(start, goal):

    nodes_expanded = 0
    visited = set()            
    g_costs = {start: 0}     

    class Node:
        def __init__(self, city, parent=None, g_cost=0):
            self.city = city
            self.parent = parent
            self.g_cost = g_cost
            self.h_cost = heuristic(city, goal)
            self.f_cost = self.g_cost + self.h_cost

        def __lt__(self, other):
            if self.f_cost == other.f_cost:
                return self.h_cost < other.h_cost
            return self.f_cost < other.f_cost

    open_heap = []
    start_node = Node(start, parent=None, g_cost=0)
    heapq.heappush(open_heap, start_node)

    while open_heap:
        node = heapq.heappop(open_heap)

        if node.g_cost > g_costs.get(node.city, float("inf")):
            continue
        
        if node.city == goal:
            path = []
            cur = node
            while cur:
                path.append(cur.city)
                cur = cur.parent
            path.reverse()
            total_cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
            return path, nodes_expanded, total_cost

        visited.add(node.city)
        nodes_expanded += 1

        for neighbor, step_cost in get_neighbors(node.city):
            tentative_g = node.g_cost + step_cost

            if neighbor in visited and tentative_g >= g_costs.get(neighbor, float("inf")):
                continue

            if tentative_g < g_costs.get(neighbor, float("inf")):
                g_costs[neighbor] = tentative_g
                child = Node(neighbor, parent=node, g_cost=tentative_g)
                heapq.heappush(open_heap, child)

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

# Get START city
while True:
    start = input("Enter START city: ").strip()
    if start in graph: break
    print("Invalid city, try again.\n")

# Get GOAL city
while True:
    goal = input("Enter GOAL city: ").strip()
    if goal in graph: break
    print("Invalid city, try again.\n")

print("\nRunning IDA*...\n")

# ---- TIMEOUT CHECK ----
import time
start_time = time.time()

# Run the algorithm
path, expanded, cost = A_star(start, goal)

end_time = time.time()
elapsed = end_time - start_time

# Check if it took more than 10 seconds
if elapsed > 10:
    print("\n========== RESULT ==========")
    print("Invalid algorithm: Execution time exceeded 10 seconds.")
else:
    print("\n========== RESULT ==========")
    if path:
        print("Full Path:", " → ".join(path))
        print("Total cost:", cost)
        print("Nodes expanded:", expanded)
        print("Time taken:", round(elapsed, 6), "seconds")
        visualize_path(path)
    else:
        print("No path found.")
print("============================")



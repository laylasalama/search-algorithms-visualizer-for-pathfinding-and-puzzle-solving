#=========================================================================#
#=======================graph of ucs======================================#
#=========================================================================#
import time
import heapq

# ====================================================
# Romania Graph
# ====================================================
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

# ====================================================
# UCS Algorithm
# ====================================================
def UCS(start, goal):
    frontier = []
    heapq.heappush(frontier, (0, start))  # (cost_so_far, node)
    parent = {start: None}
    cost_so_far = {start: 0}
    nodes_expanded = 0

    while frontier:
        current_cost, node = heapq.heappop(frontier)
        nodes_expanded += 1

        if node == goal:
            # Build path
            path = []
            current = goal
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()
            total_cost = current_cost
            return path, nodes_expanded, total_cost

        for neighbor, step_cost in graph[node].items():
            new_cost = current_cost + step_cost
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                parent[neighbor] = node
                heapq.heappush(frontier, (new_cost, neighbor))

    return None, nodes_expanded, None

# ====================================================
# Visualization
# ====================================================
def visualize_path(path):
    print("\nStep-by-step path progression:")
    for i in range(1, len(path)+1):
        print(" → ".join(path[:i]))

# ====================================================
# RUN UCS
# ====================================================
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

print("\nRunning UCS...\n")

start_time = time.time()
path, expanded, cost = UCS(start, goal)
end_time = time.time()
elapsed = end_time - start_time

# ====================================================
# Result Output
# ====================================================
print("\n========== RESULT ==========")
if path:
    print("Full Path:", " → ".join(path))
    print("Total cost:", cost)
    print("Nodes expanded:", expanded)
    print("Time taken:", f"{elapsed:.6f}", "seconds")
    visualize_path(path)
else:
    print("No path found.")
print("============================")
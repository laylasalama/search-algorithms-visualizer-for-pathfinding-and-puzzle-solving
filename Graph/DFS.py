#=========================================================================#
#=======================graph of dfs======================================#
#=========================================================================#
import time

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
# DFS Algorithm
# ====================================================
def DFS(start, goal):
    stack = [(start, [start])]  # (current_node, path_so_far)
    visited = set()
    nodes_expanded = 0

    while stack:
        node, path = stack.pop()
        nodes_expanded += 1

        if node == goal:
            # Calculate total cost along path
            total_cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1))
            return path, nodes_expanded, total_cost

        if node not in visited:
            visited.add(node)
            # Add neighbors to stack
            for neighbor in reversed(list(graph[node].keys())):
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))

    return None, nodes_expanded, None

# ====================================================
# Visualization
# ====================================================
def visualize_path(path):
    print("\nStep-by-step path progression:")
    for i in range(1, len(path)+1):
        print(" → ".join(path[:i]))

# ====================================================
# RUN DFS
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

print("\nRunning DFS...\n")

start_time = time.time()
path, expanded, cost = DFS(start, goal)
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
    print("Time taken:", round(elapsed, 6), "seconds")
    visualize_path(path)
else:
    print("No path found.")
print("============================")
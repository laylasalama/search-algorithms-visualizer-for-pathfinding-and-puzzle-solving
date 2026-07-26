import sys
import os
from copy import deepcopy
from tkinter import Tk, StringVar, OptionMenu, Label, Frame, Button, Canvas, GROOVE, RIGHT, BOTTOM, E, W
from collections import deque

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Simple PriorityQueue implementation
class PriorityQueue:
    def __init__(self, order='min', f=lambda x: x):
        self.A = []
        self.order = order
        self.f = f
    
    def append(self, item):
        self.A.append(item)
    
    def __len__(self):
        return len(self.A)
    
    def __contains__(self, item):
        return any(x == item for x in self.A)
    
    def __getitem__(self, key):
        for item in self.A:
            if item == key:
                return item
        return None
    
    def __delitem__(self, key):
        self.A = [x for x in self.A if x != key]
    
    def pop(self):
        if not self.A:
            return None
        if self.order == 'min':
            item = min(self.A, key=self.f)
        else:
            item = max(self.A, key=self.f)
        self.A.remove(item)
        return item

# Node class for search
class Node:
    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
    
    def expand(self, problem):
        children = []
        for action in problem.actions(self.state):
            child_state = problem.result(self.state, action)
            cost = self.path_cost + problem.path_cost(self.state, action, child_state)
            child = Node(child_state, self, action, cost)
            children.append(child)
        return children
    
    def solution(self):
        path = []
        node = self
        while node.parent is not None:
            path.append(node.state)
            node = node.parent
        return list(reversed(path))

# GraphProblem class
class GraphProblem:
    def __init__(self, initial, goal, graph):
        self.initial = initial
        self.goal = goal
        self.graph = graph
        self.locations = getattr(graph, 'locations', {})
    
    def actions(self, state):
        return list(self.graph.get(state, {}).keys())
    
    def result(self, state, action):
        return action
    
    def path_cost(self, state1, action, state2):
        return self.graph[state1].get(action, float('inf'))
    
    def goal_test(self, state):
        return state == self.goal
    
    def h(self, node):
        if node.state in self.locations and self.goal in self.locations:
            loc1 = self.locations[node.state]
            loc2 = self.locations[self.goal]
            return ((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)**0.5
        return 0

# Romania map data
romania_map_data = {
    'Arad': {'Sibiu': 140, 'Timisoara': 118, 'Zerind': 75},
    'Sibiu': {'Arad': 140, 'Oradea': 151, 'Fagaras': 99, 'Rimnicu': 80},
    'Timisoara': {'Arad': 118, 'Lugoj': 111},
    'Zerind': {'Arad': 75, 'Oradea': 71},
    'Oradea': {'Zerind': 71, 'Sibiu': 151},
    'Lugoj': {'Timisoara': 111, 'Mehadia': 70},
    'Mehadia': {'Lugoj': 70, 'Drobeta': 75},
    'Drobeta': {'Mehadia': 75, 'Craiova': 120},
    'Craiova': {'Drobeta': 120, 'Rimnicu': 146, 'Pitesti': 138},
    'Rimnicu': {'Sibiu': 80, 'Craiova': 146, 'Pitesti': 97},
    'Fagaras': {'Sibiu': 99, 'Bucharest': 211},
    'Pitesti': {'Rimnicu': 97, 'Craiova': 138, 'Bucharest': 101},
    'Bucharest': {'Fagaras': 211, 'Pitesti': 101, 'Giurgiu': 90, 'Urziceni': 85},
    'Giurgiu': {'Bucharest': 90},
    'Urziceni': {'Bucharest': 85, 'Hirsova': 98, 'Vaslui': 142},
    'Hirsova': {'Urziceni': 98, 'Eforie': 86},
    'Eforie': {'Hirsova': 86},
    'Vaslui': {'Urziceni': 142, 'Iasi': 92},
    'Iasi': {'Vaslui': 92, 'Neamt': 87},
    'Neamt': {'Iasi': 87}
}

romania_locations = {
    'Arad': (91, 492),
    'Sibiu': (400, 449),
    'Timisoara': (118, 392),
    'Zerind': (455, 528),
    'Oradea': (131, 571),
    'Lugoj': (165, 299),
    'Mehadia': (168, 246),
    'Drobeta': (71, 172),
    'Craiova': (212, 155),
    'Rimnicu': (220, 289),
    'Fagaras': (533, 372),
    'Pitesti': (444, 275),
    'Bucharest': (495, 201),
    'Giurgiu': (214, 56),
    'Urziceni': (645, 331),
    'Hirsova': (655, 274),
    'Eforie': (672, 87),
    'Vaslui': (642, 429),
    'Iasi': (520, 571),
    'Neamt': (406, 537)
}

# MapWrapper class
class MapWrapper:
    def __init__(self, data, locations):
        self.data = data
        self.locations = locations
    
    def __getitem__(self, key):
        return self.data.get(key, {})
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def keys(self):
        return self.data.keys()

romania_map = MapWrapper(romania_map_data, romania_locations)

# Global variables
city_coord = {}
romania_problem = None
counter = -1
city_map = None
frontier = None
front = None
node = None
explored = None
algo = None
start = None
goal = None
next_button = None
root = None


def create_map(root):
    """This function draws out the required map."""
    global city_map, start, goal
    width = 750
    height = 670
    margin = 5
    city_map = Canvas(root, width=width, height=height)
    city_map.pack()

    # Since lines have to be drawn between particular points, we need to list them separately
    make_line(city_map, romania_locations['Arad'][0], height - romania_locations['Arad'][1],
              romania_locations['Sibiu'][0], height - romania_locations['Sibiu'][1],
              romania_map.get('Arad', {}).get('Sibiu', ''))
    make_line(city_map, romania_locations['Arad'][0], height - romania_locations['Arad'][1],
              romania_locations['Zerind'][0], height - romania_locations['Zerind'][1],
              romania_map.get('Arad', {}).get('Zerind', ''))
    make_line(city_map, romania_locations['Arad'][0], height - romania_locations['Arad'][1],
              romania_locations['Timisoara'][0], height - romania_locations['Timisoara'][1],
              romania_map.get('Arad', {}).get('Timisoara', ''))
    make_line(city_map, romania_locations['Oradea'][0], height - romania_locations['Oradea'][1],
              romania_locations['Zerind'][0], height - romania_locations['Zerind'][1],
              romania_map.get('Oradea', {}).get('Zerind', ''))
    make_line(city_map, romania_locations['Oradea'][0], height - romania_locations['Oradea'][1],
              romania_locations['Sibiu'][0], height - romania_locations['Sibiu'][1],
              romania_map.get('Oradea', {}).get('Sibiu', ''))
    make_line(city_map, romania_locations['Lugoj'][0], height - romania_locations['Lugoj'][1],
              romania_locations['Timisoara'][0], height - romania_locations['Timisoara'][1],
              romania_map.get('Lugoj', {}).get('Timisoara', ''))
    make_line(city_map, romania_locations['Lugoj'][0], height - romania_locations['Lugoj'][1],
              romania_locations['Mehadia'][0], height - romania_locations['Mehadia'][1],
              romania_map.get('Lugoj', {}).get('Mehadia', ''))
    make_line(city_map, romania_locations['Drobeta'][0], height - romania_locations['Drobeta'][1],
              romania_locations['Mehadia'][0], height - romania_locations['Mehadia'][1],
              romania_map.get('Drobeta', {}).get('Mehadia', ''))
    make_line(city_map, romania_locations['Drobeta'][0], height - romania_locations['Drobeta'][1],
              romania_locations['Craiova'][0], height - romania_locations['Craiova'][1],
              romania_map.get('Drobeta', {}).get('Craiova', ''))
    make_line(city_map, romania_locations['Pitesti'][0], height - romania_locations['Pitesti'][1],
              romania_locations['Craiova'][0], height - romania_locations['Craiova'][1],
              romania_map.get('Pitesti', {}).get('Craiova', ''))
    make_line(city_map, romania_locations['Rimnicu'][0], height - romania_locations['Rimnicu'][1],
              romania_locations['Craiova'][0], height - romania_locations['Craiova'][1],
              romania_map.get('Rimnicu', {}).get('Craiova', ''))
    make_line(city_map, romania_locations['Rimnicu'][0], height - romania_locations['Rimnicu'][1],
              romania_locations['Sibiu'][0], height - romania_locations['Sibiu'][1],
              romania_map.get('Rimnicu', {}).get('Sibiu', ''))
    make_line(city_map, romania_locations['Rimnicu'][0], height - romania_locations['Rimnicu'][1],
              romania_locations['Pitesti'][0], height - romania_locations['Pitesti'][1],
              romania_map.get('Rimnicu', {}).get('Pitesti', ''))
    make_line(city_map, romania_locations['Bucharest'][0], height - romania_locations['Bucharest'][1],
              romania_locations['Pitesti'][0], height - romania_locations['Pitesti'][1],
              romania_map.get('Bucharest', {}).get('Pitesti', ''))
    make_line(city_map, romania_locations['Fagaras'][0], height - romania_locations['Fagaras'][1],
              romania_locations['Sibiu'][0], height - romania_locations['Sibiu'][1],
              romania_map.get('Fagaras', {}).get('Sibiu', ''))
    make_line(city_map, romania_locations['Fagaras'][0], height - romania_locations['Fagaras'][1],
              romania_locations['Bucharest'][0], height - romania_locations['Bucharest'][1],
              romania_map.get('Fagaras', {}).get('Bucharest', ''))
    make_line(city_map, romania_locations['Giurgiu'][0], height - romania_locations['Giurgiu'][1],
              romania_locations['Bucharest'][0], height - romania_locations['Bucharest'][1],
              romania_map.get('Giurgiu', {}).get('Bucharest', ''))
    make_line(city_map, romania_locations['Urziceni'][0], height - romania_locations['Urziceni'][1],
              romania_locations['Bucharest'][0], height - romania_locations['Bucharest'][1],
              romania_map.get('Urziceni', {}).get('Bucharest', ''))
    make_line(city_map, romania_locations['Urziceni'][0], height - romania_locations['Urziceni'][1],
              romania_locations['Hirsova'][0], height - romania_locations['Hirsova'][1],
              romania_map.get('Urziceni', {}).get('Hirsova', ''))
    make_line(city_map, romania_locations['Eforie'][0], height - romania_locations['Eforie'][1],
              romania_locations['Hirsova'][0], height - romania_locations['Hirsova'][1],
              romania_map.get('Eforie', {}).get('Hirsova', ''))
    make_line(city_map, romania_locations['Urziceni'][0], height - romania_locations['Urziceni'][1],
              romania_locations['Vaslui'][0], height - romania_locations['Vaslui'][1],
              romania_map.get('Urziceni', {}).get('Vaslui', ''))
    make_line(city_map, romania_locations['Iasi'][0], height - romania_locations['Iasi'][1],
              romania_locations['Vaslui'][0], height - romania_locations['Vaslui'][1],
              romania_map.get('Iasi', {}).get('Vaslui', ''))
    make_line(city_map, romania_locations['Iasi'][0], height - romania_locations['Iasi'][1],
              romania_locations['Neamt'][0], height - romania_locations['Neamt'][1],
              romania_map.get('Iasi', {}).get('Neamt', ''))

    for city in romania_locations.keys():
        make_rectangle(city_map, romania_locations[city][0],
                      height - romania_locations[city][1], margin, city)

    make_legend(city_map)


def make_line(map, x0, y0, x1, y1, distance):
    """This function draws out the lines joining various points."""
    map.create_line(x0, y0, x1, y1)
    map.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=distance)


def make_rectangle(map, x0, y0, margin, city_name):
    """This function draws out rectangles for various points."""
    global city_coord
    rect = map.create_rectangle(
        x0 - margin,
        y0 - margin,
        x0 + margin,
        y0 + margin,
        fill="white")
    if "Bucharest" in city_name or "Pitesti" in city_name or "Lugoj" in city_name \
            or "Mehadia" in city_name or "Drobeta" in city_name:
        map.create_text(
            x0 - 2 * margin,
            y0 - 2 * margin,
            text=city_name,
            anchor=E)
    else:
        map.create_text(
            x0 - 2 * margin,
            y0 - 2 * margin,
            text=city_name,
            anchor=E)
    city_coord.update({city_name: rect})


def make_legend(map):
    rect1 = map.create_rectangle(600, 100, 610, 110, fill="white")
    text1 = map.create_text(615, 105, anchor=W, text="Un-explored")

    rect2 = map.create_rectangle(600, 115, 610, 125, fill="orange")
    text2 = map.create_text(615, 120, anchor=W, text="Frontier")

    rect3 = map.create_rectangle(600, 130, 610, 140, fill="red")
    text3 = map.create_text(615, 135, anchor=W, text="Currently Exploring")

    rect4 = map.create_rectangle(600, 145, 610, 155, fill="grey")
    text4 = map.create_text(615, 150, anchor=W, text="Explored")

    rect5 = map.create_rectangle(600, 160, 610, 170, fill="dark green")
    text5 = map.create_text(615, 165, anchor=W, text="Final Solution")


def tree_search(problem):
    """Search through the successors of a problem to find a goal."""
    global counter, frontier, node

    if counter == -1:
        frontier.append(Node(problem.initial))
        display_frontier(frontier)
    if counter % 3 == 0 and counter >= 0:
        node = frontier.pop()
        display_current(node)
    if counter % 3 == 1 and counter >= 0:
        if problem.goal_test(node.state):
            return node
        frontier.extend(node.expand(problem))
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def graph_search(problem):
    """Search through the successors of a problem to find a goal."""
    global counter, frontier, node, explored
    if counter == -1:
        frontier.append(Node(problem.initial))
        explored = set()
        display_frontier(frontier)
    if counter % 3 == 0 and counter >= 0:
        node = frontier.pop()
        display_current(node)
    if counter % 3 == 1 and counter >= 0:
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
        frontier.extend(child for child in node.expand(problem)
                        if child.state not in explored and
                        child not in frontier)
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def display_frontier(queue):
    """This function marks the frontier nodes (orange) on the map."""
    global city_map, city_coord
    qu = deepcopy(queue) if isinstance(queue, (list, deque)) else list(queue.A) if hasattr(queue, 'A') else []
    while qu:
        if isinstance(qu, deque):
            n = qu.popleft()
        else:
            n = qu.pop() if qu else None
        if n is None:
            break
        for city in city_coord.keys():
            if n.state == city:
                city_map.itemconfig(city_coord[city], fill="orange")


def display_current(node):
    """This function marks the currently exploring node (red) on the map."""
    global city_map, city_coord
    city = node.state
    city_map.itemconfig(city_coord[city], fill="red")


def display_explored(node):
    """This function marks the already explored node (gray) on the map."""
    global city_map, city_coord
    city = node.state
    city_map.itemconfig(city_coord[city], fill="gray")


def display_final(cities):
    """This function marks the final solution nodes (green) on the map."""
    global city_map, city_coord
    for city in cities:
        city_map.itemconfig(city_coord[city], fill="green")


def breadth_first_tree_search(problem):
    """Search the shallowest nodes in the search tree first."""
    global frontier, counter, node
    if counter == -1:
        frontier = deque()

    if counter == -1:
        frontier.append(Node(problem.initial))
        display_frontier(frontier)
    if counter % 3 == 0 and counter >= 0:
        node = frontier.popleft()
        display_current(node)
    if counter % 3 == 1 and counter >= 0:
        if problem.goal_test(node.state):
            return node
        frontier.extend(node.expand(problem))
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def depth_first_tree_search(problem):
    """Search the deepest nodes in the search tree first."""
    global frontier, counter, node
    if counter == -1:
        frontier = []

    if counter == -1:
        frontier.append(Node(problem.initial))
        display_frontier(frontier)
    if counter % 3 == 0 and counter >= 0:
        node = frontier.pop()
        display_current(node)
    if counter % 3 == 1 and counter >= 0:
        if problem.goal_test(node.state):
            return node
        frontier.extend(node.expand(problem))
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def breadth_first_graph_search(problem):
    """Breadth-first graph search."""
    global frontier, node, explored, counter
    if counter == -1:
        node = Node(problem.initial)
        display_current(node)
        if problem.goal_test(node.state):
            return node

        frontier = deque([node])
        display_frontier(frontier)
        explored = set()
    if counter % 3 == 0 and counter >= 0:
        node = frontier.popleft()
        display_current(node)
        explored.add(node.state)
    if counter % 3 == 1 and counter >= 0:
        for child in node.expand(problem):
            if child.state not in explored and child not in frontier:
                if problem.goal_test(child.state):
                    return child
                frontier.append(child)
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def depth_first_graph_search(problem):
    """Search the deepest nodes in the search tree first."""
    global counter, frontier, node, explored
    if counter == -1:
        frontier = []
    if counter == -1:
        frontier.append(Node(problem.initial))
        explored = set()
        display_frontier(frontier)
    if counter % 3 == 0 and counter >= 0:
        node = frontier.pop()
        display_current(node)
    if counter % 3 == 1 and counter >= 0:
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
        frontier.extend(child for child in node.expand(problem)
                        if child.state not in explored and
                        child not in frontier)
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def best_first_graph_search(problem, f):
    """Search the nodes with the lowest f scores first."""
    global frontier, node, explored, counter

    if counter == -1:
        f = memoize(f, 'f')
        node = Node(problem.initial)
        display_current(node)
        if problem.goal_test(node.state):
            return node
        frontier = PriorityQueue('min', f)
        frontier.append(node)
        display_frontier(frontier)
        explored = set()
    if counter % 3 == 0 and counter >= 0:
        node = frontier.pop()
        display_current(node)
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
    if counter % 3 == 1 and counter >= 0:
        for child in node.expand(problem):
            if child.state not in explored and child not in frontier:
                frontier.append(child)
            elif child in frontier:
                if f(child) < f(frontier[child]):
                    del frontier[child]
                    frontier.append(child)
        display_frontier(frontier)
    if counter % 3 == 2 and counter >= 0:
        display_explored(node)
    return None


def uniform_cost_search(problem):
    """Uniform cost search."""
    return best_first_graph_search(problem, lambda node: node.path_cost)


def astar_search(problem, h=None):
    """A* search is best-first graph search with f(n) = g(n)+h(n)."""
    h = memoize(h or problem.h, 'h')
    return best_first_graph_search(problem, lambda n: n.path_cost + h(n))


def memoize(fn, slot=None, maxsize=32):
    """Memoizes a function."""
    if slot:
        def memoized_fn(obj, *args):
            if hasattr(obj, slot):
                return getattr(obj, slot)
            else:
                val = fn(obj, *args)
                setattr(obj, slot, val)
                return val
    else:
        def memoized_fn(*args):
            return fn(*args)
    return memoized_fn


def on_click():
    """This function defines the action of the 'Next' button."""
    global algo, counter, next_button, romania_problem, start, goal
    romania_problem = GraphProblem(start.get(), goal.get(), romania_map)
    if "Breadth-First Tree Search" == algo.get():
        node = breadth_first_tree_search(romania_problem)
        if node is not None:
            final_path = breadth_first_tree_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1
    elif "Depth-First Tree Search" == algo.get():
        node = depth_first_tree_search(romania_problem)
        if node is not None:
            final_path = depth_first_tree_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1
    elif "Breadth-First Graph Search" == algo.get():
        node = breadth_first_graph_search(romania_problem)
        if node is not None:
            final_path = breadth_first_graph_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1
    elif "Depth-First Graph Search" == algo.get():
        node = depth_first_graph_search(romania_problem)
        if node is not None:
            final_path = depth_first_graph_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1
    elif "Uniform Cost Search" == algo.get():
        node = uniform_cost_search(romania_problem)
        if node is not None:
            final_path = uniform_cost_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1
    elif "A* - Search" == algo.get():
        node = astar_search(romania_problem)
        if node is not None:
            final_path = astar_search(romania_problem).solution()
            final_path.append(start.get())
            display_final(final_path)
            next_button.config(state="disabled")
        counter += 1


def reset_map():
    global counter, city_coord, city_map, next_button
    counter = -1
    for city in city_coord.keys():
        city_map.itemconfig(city_coord[city], fill="white")
    next_button.config(state="normal")


if __name__ == "__main__":
    root = Tk()
    root.title("Road Map of Romania")
    root.geometry("950x1150")
    algo = StringVar(root)
    start = StringVar(root)
    goal = StringVar(root)
    algo.set("Breadth-First Tree Search")
    start.set('Arad')
    goal.set('Bucharest')
    cities = sorted(romania_map.locations.keys())
    algorithm_menu = OptionMenu(
        root,
        algo, "Breadth-First Tree Search", "Depth-First Tree Search",
        "Breadth-First Graph Search", "Depth-First Graph Search",
        "Uniform Cost Search", "A* - Search")
    Label(root, text="\n Search Algorithm").pack()
    algorithm_menu.pack()
    Label(root, text="\n Start City").pack()
    start_menu = OptionMenu(root, start, *cities)
    start_menu.pack()
    Label(root, text="\n Goal City").pack()
    goal_menu = OptionMenu(root, goal, *cities)
    goal_menu.pack()
    frame1 = Frame(root)
    next_button = Button(
        frame1,
        width=6,
        height=2,
        text="Next",
        command=on_click,
        padx=2,
        pady=2,
        relief=GROOVE)
    next_button.pack(side=RIGHT)
    reset_button = Button(
        frame1,
        width=6,
        height=2,
        text="Reset",
        command=reset_map,
        padx=2,
        pady=2,
        relief=GROOVE)
    reset_button.pack(side=RIGHT)
    frame1.pack(side=BOTTOM)
    create_map(root)
    root.mainloop()

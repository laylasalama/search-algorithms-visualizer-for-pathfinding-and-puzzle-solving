from tkinter import Toplevel, Canvas, Frame, Button, Scale, HORIZONTAL, Label
import threading
import math
import time

# Minimal Romania graph (weights) and approximate coordinates for heuristics
graph = {
    'Arad': {'Zerind':75,'Sibiu':140,'Timisoara':118},
    'Zerind': {'Arad':75,'Oradea':71},
    'Oradea': {'Zerind':71,'Sibiu':151},
    'Sibiu': {'Arad':140,'Oradea':151,'Fargaras':99,'Rimnicu Vilcea':80},
    'Timisoara': {'Arad':118,'Lugoj':111},
    'Lugoj': {'Timisoara':111,'Mehadia':70},
    'Mehadia': {'Lugoj':70,'Dobreta':75},
    'Dobreta': {'Mehadia':75,'Craiova':120},
    'Craiova': {'Dobreta':120,'Rimnicu Vilcea':146,'Pitesti':138},
    'Rimnicu Vilcea': {'Sibiu':80,'Craiova':146,'Pitesti':97},
    'Fargaras': {'Sibiu':99,'Buchurest':211},
    'Pitesti': {'Rimnicu Vilcea':97,'Craiova':138,'Buchurest':101},
    'Buchurest': {'Fargaras':211,'Pitesti':101,'Giurgiu':90,'Urziceni':85},
    'Giurgiu': {'Buchurest':90},
    'Urziceni': {'Buchurest':85,'Hirsova':98,'Vaslui':142},
    'Hirsova': {'Urziceni':98,'Eforie':86},
    'Eforie': {'Hirsova':86},
    'Vaslui': {'Urziceni':142,'Lasi':92},
    'Lasi': {'Vaslui':92,'Neamt':87},
    'Neamt': {'Lasi':87},
}

# rough coordinates (for heuristic)
coords = {
    'Arad': (91,492), 'Zerind': (108,531), 'Oradea': (171,571), 'Sibiu': (207,500),
    'Timisoara': (92,593), 'Lugoj': (130,600), 'Mehadia': (170,640), 'Dobreta': (190,700),
    'Craiova': (300,700), 'Rimnicu Vilcea': (265,560), 'Fargaras': (310,490), 'Pitesti': (350,650),
    'Buchurest': (420,740), 'Giurgiu': (420,820), 'Urziceni': (520,690), 'Hirsova': (560,720),
    'Eforie': (610,730), 'Vaslui': (640,600), 'Lasi': (700,560), 'Neamt': (720,500)
}

def heuristic(a,b):
    if a not in coords or b not in coords:
        return 0
    (x1,y1),(x2,y2) = coords[a], coords[b]
    return math.hypot(x1-x2,y1-y2)

def bfs_search(start, goal):
    from collections import deque
    q = deque([start])
    visited = set([start])
    parent = {}
    order = [start]
    while q:
        u = q.popleft()
        if u == goal:
            break
        for v in graph.get(u,{}):
            if v not in visited:
                visited.add(v)
                parent[v]=u
                q.append(v)
                order.append(v)
    return order, parent

def dfs_search(start, goal):
    stack=[start]
    visited=set([start])
    parent={}
    order=[start]
    while stack:
        u = stack.pop()
        if u==goal:
            break
        for v in graph.get(u,{}):
            if v not in visited:
                visited.add(v)
                parent[v]=u
                stack.append(v)
                order.append(v)
    return order, parent

import heapq
def ucs_search(start, goal):
    pq=[(0,start,None)]
    dist={start:0}
    parent={}
    visited=set()
    order=[]
    while pq:
        d,u,p = heapq.heappop(pq)
        if u in visited: continue
        visited.add(u)
        if p: parent[u]=p
        order.append(u)
        if u==goal: break
        for v,w in graph.get(u,{}).items():
            nd = d + w
            if nd < dist.get(v, 1e12):
                dist[v]=nd
                heapq.heappush(pq,(nd,v,u))
    return order, parent

def greedy_search(start, goal):
    pq=[(heuristic(start,goal), start, None)]
    visited=set()
    parent={}
    order=[]
    while pq:
        _,u,p = heapq.heappop(pq)
        if u in visited: continue
        visited.add(u)
        if p: parent[u]=p
        order.append(u)
        if u==goal: break
        for v in graph.get(u,{}):
            if v not in visited:
                heapq.heappush(pq,(heuristic(v,goal),v,u))
    return order, parent

def astar_search(start, goal):
    pq=[(heuristic(start,goal),0,start,None)]
    dist={start:0}
    parent={}
    visited=set()
    order=[]
    while pq:
        f,g,u,p = heapq.heappop(pq)
        if u in visited: continue
        visited.add(u)
        if p: parent[u]=p
        order.append(u)
        if u==goal: break
        for v,w in graph.get(u,{}).items():
            ng = g + w
            if ng < dist.get(v, 1e12):
                dist[v]=ng
                heapq.heappush(pq,(ng+heuristic(v,goal),ng,v,u))
    return order, parent

def beam_search(start, goal, k=2):
    frontier=[start]
    visited=set([start])
    parent={}
    order=[start]
    while frontier:
        candidates=[]
        for u in frontier:
            if u==goal: return order,parent
            for v in graph.get(u,{}):
                if v not in visited:
                    visited.add(v)
                    parent[v]=u
                    candidates.append((heuristic(v,goal),v))
                    order.append(v)
        candidates.sort()
        frontier=[v for _,v in candidates[:k]]
    return order,parent

def hill_climb(start, goal):
    current = start
    parent={}
    order=[start]
    visited=set([start])
    while current!=goal:
        neigh = [(heuristic(n,goal),n) for n in graph.get(current,{}) if n not in visited]
        if not neigh: break
        neigh.sort()
        nxt = neigh[0][1]
        parent[nxt]=current
        visited.add(nxt)
        order.append(nxt)
        current = nxt
    return order,parent

ALG_MAP = {
    'BFS': bfs_search,
    'DFS': dfs_search,
    'UCS': ucs_search,
    'Greedy': greedy_search,
    'A*': astar_search,
    'Beam': lambda s,g: beam_search(s,g, k=3),
    'Hill Climbing': hill_climb,
}

class ExecutionWindow:
    def __init__(self, parent, start, goal, algorithm_name):
        self.window = Toplevel(parent)
        self.window.title(f"Execution: {algorithm_name} {start} -> {goal}")
        self.canvas_w = 900
        self.canvas_h = 700
        self.canvas = Canvas(self.window, width=self.canvas_w, height=self.canvas_h, bg='white')
        self.canvas.pack(side='left', fill='both', expand=True)

        ctrl = Frame(self.window)
        ctrl.pack(side='right', fill='y')
        Button(ctrl, text='Play', command=self.play).pack(pady=6)
        Button(ctrl, text='Pause', command=self.pause).pack(pady=6)
        Button(ctrl, text='Step', command=self.step).pack(pady=6)
        Label(ctrl, text='Speed (ms)').pack(pady=6)
        self.speed = Scale(ctrl, from_=50, to=1000, orient=HORIZONTAL)
        self.speed.set(300)
        self.speed.pack(pady=6)

        func = ALG_MAP.get(algorithm_name)
        if func is None:
            self.order, self.parent = [start], {}
        else:
            self.order, self.parent = func(start, goal)

        self.start = start
        self.goal = goal
        self.algorithm_name = algorithm_name

        self.nodes = list({start} | set(self.order) | set(self.parent.keys()))
        self.layers = self.build_layers()
        self.positions = self.compute_positions()

        self.node_items = {}
        self.edge_items = {}

        self.step_index = 0
        self.running = False

        self.draw_static()

    def build_layers(self):
        layers = {}
        for n in self.nodes:
            depth = 0
            cur = n
            while cur in self.parent:
                depth += 1
                cur = self.parent[cur]
                if cur==self.start:
                    break
            layers.setdefault(depth, []).append(n)
        return layers

    def compute_positions(self):
        positions = {}
        cx = self.canvas_w//2
        cy = self.canvas_h//2 - 40
        for depth, nodes in self.layers.items():
            r = 80 + depth*90
            n = len(nodes)
            for i, node in enumerate(nodes):
                ang = 2*math.pi*i / max(1,n)
                x = cx + int(r*math.cos(ang))
                y = cy + int(r*math.sin(ang))
                positions[node] = (x,y)
        return positions

    def draw_static(self):
        # draw edges (parent links)
        for child, parent in self.parent.items():
            x1,y1 = self.positions.get(parent,(0,0))
            x2,y2 = self.positions.get(child,(0,0))
            line = self.canvas.create_line(x1,y1,x2,y2, fill='#999', width=2)
            self.edge_items[(parent,child)] = line
        # draw nodes
        for node,(x,y) in self.positions.items():
            r=22
            oval = self.canvas.create_oval(x-r,y-r,x+r,y+r, fill='#e7f2ff', outline='#2b6cb0', width=2)
            text = self.canvas.create_text(x,y, text=node, fill='#063a6f')
            self.node_items[node] = (oval,text)

    def highlight_node(self, node):
        items = self.node_items.get(node)
        if not items: return
        oval, text = items
        self.canvas.itemconfig(oval, fill='#2f855a')
        self.canvas.itemconfig(text, fill='white')

    def play(self):
        if not self.running:
            self.running = True
            self._run()

    def pause(self):
        self.running = False

    def step(self):
        if self.step_index < len(self.order):
            node = self.order[self.step_index]
            self.highlight_node(node)
            self.step_index += 1

    def _run(self):
        if not self.running: return
        if self.step_index < len(self.order):
            node = self.order[self.step_index]
            self.highlight_node(node)
            self.step_index += 1
            delay = int(self.speed.get())
            self.window.after(delay, self._run)
        else:
            self.running = False

if __name__ == '__main__':
    # quick manual test
    import tkinter as tk
    root = tk.Tk(); root.withdraw()
    ExecutionWindow(root, 'Arad', 'Buchurest', 'BFS')
    root.mainloop()
import tkinter as tk
from tkinter import RIDGE, SUNKEN, messagebox
import threading
import time
import math

# ----------------------- Romania Graph & coords -----------------------
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

def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a_ = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a_), math.sqrt(1-a_))
    return R * c

# ----------------------- Algorithms (instrumented) -----------------------
from collections import deque
import heapq

def BFS_search(start, goal):
    queue = deque([start])
    parent = {start: None}
    visited_order = []
    nodes_expanded = 0

    while queue:
        node = queue.popleft()
        visited_order.append(node)
        nodes_expanded += 1
        if node == goal:
            break
        for nb in graph[node]:
            if nb not in parent:
                parent[nb] = node
                queue.append(nb)

    # reconstruct path
    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
    return visited_order, parent, path, nodes_expanded, cost

def DFS_search(start, goal):
    stack = [start]
    parent = {start: None}
    visited_order = []
    nodes_expanded = 0

    while stack:
        node = stack.pop()
        if node in visited_order:
            continue
        visited_order.append(node)
        nodes_expanded += 1
        if node == goal:
            break
        for nb in reversed(list(graph[node].keys())):
            if nb not in parent:
                parent[nb] = node
                stack.append(nb)

    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
    return visited_order, parent, path, nodes_expanded, cost

def UCS_search(start, goal):
    pq = [(0, start)]
    parent = {start: None}
    cost_so_far = {start: 0}
    visited_order = []
    nodes_expanded = 0

    while pq:
        c, node = heapq.heappop(pq)
        if node in visited_order:
            continue
        visited_order.append(node)
        nodes_expanded += 1
        if node == goal:
            break
        for nb, w in graph[node].items():
            nc = c + w
            if nb not in cost_so_far or nc < cost_so_far[nb]:
                cost_so_far[nb] = nc
                parent[nb] = node
                heapq.heappush(pq, (nc, nb))

    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = cost_so_far.get(goal, 0)
    return visited_order, parent, path, nodes_expanded, cost

def Greedy_search(start, goal):
    pq = [(haversine(coords[start], coords[goal]), start)]
    parent = {start: None}
    visited_order = []
    nodes_expanded = 0
    seen = set()

    while pq:
        _, node = heapq.heappop(pq)
        if node in seen:
            continue
        seen.add(node)
        visited_order.append(node)
        nodes_expanded += 1
        if node == goal:
            break
        for nb in graph[node]:
            if nb not in seen:
                parent.setdefault(nb, node)
                heapq.heappush(pq, (haversine(coords[nb], coords[goal]), nb))

    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
    return visited_order, parent, path, nodes_expanded, cost

def A_star_search(start, goal):
    pq = [(haversine(coords[start], coords[goal]), 0, start)]
    parent = {start: None}
    g_cost = {start: 0}
    visited_order = []
    nodes_expanded = 0

    while pq:
        f, g, node = heapq.heappop(pq)
        if node in visited_order:
            continue
        visited_order.append(node)
        nodes_expanded += 1
        if node == goal:
            break
        for nb, w in graph[node].items():
            ng = g + w
            if nb not in g_cost or ng < g_cost[nb]:
                g_cost[nb] = ng
                parent[nb] = node
                heapq.heappush(pq, (ng + haversine(coords[nb], coords[goal]), ng, nb))

    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = g_cost.get(goal, 0)
    return visited_order, parent, path, nodes_expanded, cost

def Beam_search(start, goal, beam_width=3):
    current = [start]
    parent = {start: None}
    visited_order = [start]
    nodes_expanded = 0

    while current:
        candidates = []
        for node in current:
            nodes_expanded += 1
            if node == goal:
                path = []
                cur = goal
                while cur and cur in parent:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
                return visited_order, parent, path, nodes_expanded, cost
            for nb in graph[node]:
                if nb not in parent:
                    parent[nb] = node
                    candidates.append(nb)
        # sort by heuristic
        candidates.sort(key=lambda n: haversine(coords[n], coords[goal]))
        current = candidates[:beam_width]
        for c in current:
            visited_order.append(c)

    return visited_order, parent, [], nodes_expanded, 0

def HillClimbing_search(start, goal):
    current = start
    parent = {start: None}
    visited_order = [start]
    nodes_expanded = 0

    while current != goal:
        nodes_expanded += 1
        neighbors = list(graph[current].keys())
        if not neighbors:
            break
        best = min(neighbors, key=lambda n: haversine(coords[n], coords[goal]))
        if haversine(coords[best], coords[goal]) >= haversine(coords[current], coords[goal]):
            break
        if best in parent:
            break
        parent[best] = current
        current = best
        visited_order.append(current)

    path = []
    cur = goal
    while cur and cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    cost = sum(graph[path[i]][path[i+1]] for i in range(len(path)-1)) if len(path) > 1 else 0
    return visited_order, parent, path, nodes_expanded, cost

# ----------------------- Helper: layers from parent map -----------------------
def build_layers(parent_map, start):
    depths = {start: 0}
    for node in parent_map:
        if node == start:
            continue
        cur = node
        depth = 0
        while cur is not None and cur in parent_map:
            cur = parent_map[cur]
            depth += 1
            if cur == start:
                break
        depths[node] = depth
    layers = {}
    for n, d in depths.items():
        layers.setdefault(d, []).append(n)
    return layers

# ----------------------- GUI: input window (drag/drop) -----------------------
class InputWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Graph Algorithms - Input")
        self.root.geometry("1100x800")
        self.root.configure(bg="#676060")

        self.start = None
        self.goal = None
        self.algorithm = None
        self.widget_names = {}
        self.original_pos = {}
        self.currently_dragging = None

        # Start / Goal areas
        tk.Label(self.root, text="START", font=("Arial", 30), bg="#676060", fg="white").place(x=60, y=10)
        self.start_frame = tk.Frame(self.root, width=300, height=60, bg="lightgreen", relief=SUNKEN, bd=3)
        self.start_frame.place(x=30, y=60)

        tk.Label(self.root, text="GOAL", font=("Arial", 30), bg="#676060", fg="white").place(x=60, y=140)
        self.goal_frame = tk.Frame(self.root, width=300, height=60, bg="lightgreen", relief=SUNKEN, bd=3)
        self.goal_frame.place(x=30, y=190)

        tk.Label(self.root, text="ALGORITHM:", font=("Arial", 20), bg="#676060", fg="white").place(x=40, y=270)
        self.algo_frame = tk.Frame(self.root, width=300, height=60, bg="lightgreen", relief=SUNKEN, bd=3)
        self.algo_frame.place(x=30, y=310)

        tk.Label(self.root, text="Places to choose from:", font=("Arial", 18), bg="#78290C", fg="white").place(x=360, y=520)

        # Create city labels
        x, y = 360, 560
        for i, city in enumerate(graph.keys()):
            lbl = tk.Label(self.root, text=city, font=("Arial", 12), bg="#78290C", fg="white", relief=RIDGE)
            lbl.place(x=x + (i%6)*180, y=y + (i//6)*50)
            self.widget_names[lbl] = city
            self.original_pos[lbl] = (x + (i%6)*180, y + (i//6)*50)
            lbl.bind("<Button-1>", self.drag_start)
            lbl.bind("<B1-Motion>", self.drag_motion)
            lbl.bind("<ButtonRelease-1>", self.drop)

        # Algorithms to choose from
        algos = ["BFS", "DFS", "UCS", "A*", "Greedy", "Beam", "IDA*", "Hill"]
        for i, a in enumerate(algos):
            lbl = tk.Label(self.root, text=a, font=("Arial", 12), bg="#676060", fg="white", relief=RIDGE)
            lbl.place(x=720 + (i%2)*160, y=560 + (i//2)*50)
            self.widget_names[lbl] = a
            self.original_pos[lbl] = (720 + (i%2)*160, 560 + (i//2)*50)
            lbl.bind("<Button-1>", self.drag_start)
            lbl.bind("<B1-Motion>", self.drag_motion)
            lbl.bind("<ButtonRelease-1>", self.drop)

        # Run button
        tk.Button(self.root, text="Run", command=self.open_execution_window, bg="lightgreen", width=10, height=2).place(x=480, y=720)

    def drag_start(self, event):
        self.currently_dragging = event.widget
        widget = self.currently_dragging
        widget.startX = event.x
        widget.startY = event.y

    def drag_motion(self, event):
        if not self.currently_dragging:
            return
        x = self.currently_dragging.winfo_x() - self.currently_dragging.startX + event.x
        y = self.currently_dragging.winfo_y() - self.currently_dragging.startY + event.y
        self.currently_dragging.place(x=x, y=y)

    def drop(self, event):
        if not self.currently_dragging:
            return
        widget = self.currently_dragging
        name = self.widget_names.get(widget)
        x_mouse = event.x_root - self.root.winfo_rootx()
        y_mouse = event.y_root - self.root.winfo_rooty()

        placed = False
        # START zone
        if 30 <= x_mouse <= 330 and 60 <= y_mouse <= 120:
            if self.start is None:
                self.start = name
                widget.place(x=40, y=70)
                placed = True
            else:
                ox, oy = self.original_pos[widget]; widget.place(x=ox, y=oy)
        # GOAL zone
        elif 30 <= x_mouse <= 330 and 190 <= y_mouse <= 250:
            if self.goal is None:
                self.goal = name
                widget.place(x=40, y=200)
                placed = True
            else:
                ox, oy = self.original_pos[widget]; widget.place(x=ox, y=oy)
        # ALGO zone
        elif 30 <= x_mouse <= 330 and 310 <= y_mouse <= 370:
            if self.algorithm is None:
                self.algorithm = name
                widget.place(x=40, y=320)
                placed = True
            else:
                ox, oy = self.original_pos[widget]; widget.place(x=ox, y=oy)

        if not placed:
            ox, oy = self.original_pos[widget]; widget.place(x=ox, y=oy)
        self.currently_dragging = None

    def open_execution_window(self):
        if self.start is None or self.goal is None or self.algorithm is None:
            messagebox.showwarning("Warning", "Please set start, goal and algorithm before running")
            return
        ExecutionWindow(self.root, self.start, self.goal, self.algorithm)

    def run(self):
        self.root.mainloop()

# ----------------------- Execution / Visualization -----------------------
class ExecutionWindow:
    def __init__(self, parent, start, goal, algorithm):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Execution - {algorithm}")
        self.window.geometry("1000x700")
        self.canvas = tk.Canvas(self.window, bg="white", width=760, height=620)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.info = tk.Text(self.window, width=30)
        self.info.pack(side=tk.RIGHT, fill=tk.Y)

        self.start = start
        self.goal = goal
        self.algorithm = algorithm
        self.node_positions = {}
        self.layers = {}
        self.visited_order = []
        self.parent = {}
        self.path = []
        self.current_step = 0
        self.is_playing = False
        self.speed = 1

        ctrl = tk.Frame(self.window)
        ctrl.pack(fill=tk.X, pady=5)
        tk.Button(ctrl, text="Play", command=self.play, bg="lightgreen").pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="Pause", command=self.pause, bg="lightyellow").pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="Step", command=self.step_forward, bg="lightblue").pack(side=tk.LEFT, padx=3)
        tk.Label(ctrl, text="Speed").pack(side=tk.LEFT, padx=3)
        self.speed_scale = tk.Scale(ctrl, from_=1, to=20, orient=tk.HORIZONTAL, command=self.set_speed)
        self.speed_scale.set(5); self.speed_scale.pack(side=tk.LEFT)

        # Run algorithm in thread
        thread = threading.Thread(target=self.run_algorithm)
        thread.daemon = True
        thread.start()

    def run_algorithm(self):
        start_time = time.time()
        if self.algorithm == 'BFS':
            v, p, path, nodes, cost = BFS_search(self.start, self.goal)
        elif self.algorithm == 'DFS':
            v, p, path, nodes, cost = DFS_search(self.start, self.goal)
        elif self.algorithm == 'UCS':
            v, p, path, nodes, cost = UCS_search(self.start, self.goal)
        elif self.algorithm == 'Greedy':
            v, p, path, nodes, cost = Greedy_search(self.start, self.goal)
        elif self.algorithm == 'A*':
            v, p, path, nodes, cost = A_star_search(self.start, self.goal)
        elif self.algorithm == 'Beam':
            v, p, path, nodes, cost = Beam_search(self.start, self.goal)
        elif self.algorithm == 'Hill':
            v, p, path, nodes, cost = HillClimbing_search(self.start, self.goal)
        else:
            v, p, path, nodes, cost = BFS_search(self.start, self.goal)

        elapsed = time.time() - start_time
        self.visited_order = v
        self.parent = p
        self.path = path
        self.nodes = nodes
        self.cost = cost
        self.time = elapsed

        self.layers = build_layers(self.parent, self.start)
        self.prepare_positions()
        self.draw_step()
        self.update_info()

    def prepare_positions(self):
        # compute positions for layers in concentric circles
        cx, cy = 380, 310
        max_layer = max(self.layers.keys()) if self.layers else 0
        for layer in range(0, max_layer+1):
            nodes = self.layers.get(layer, [])
            r = 40 + layer * 80
            n = max(1, len(nodes))
            for i, node in enumerate(nodes):
                angle = 2*math.pi*i/n
                x = cx + r*math.cos(angle)
                y = cy + r*math.sin(angle)
                self.node_positions[node] = (x, y)

    def draw_step(self):
        self.canvas.delete("all")
        # draw edges (parent-child)
        for node, par in self.parent.items():
            if par is None or node not in self.node_positions or par not in self.node_positions:
                continue
            x1, y1 = self.node_positions[par]
            x2, y2 = self.node_positions[node]
            self.canvas.create_line(x1, y1, x2, y2, fill="#999999")

        # draw nodes up to current_step (visited_order)
        shown = set(self.visited_order[:self.current_step])
        for node, (x, y) in self.node_positions.items():
            r = 22
            color = "white"
            if node == self.start:
                color = "green"
            elif node == self.goal:
                color = "red"
            elif node in self.path:
                color = "yellow"
            elif node in shown:
                color = "lightblue"
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="black")
            self.canvas.create_text(x, y, text=node, font=("Arial", 9))

    def update_info(self):
        self.info.delete("1.0", tk.END)
        lines = [f"Algorithm: {self.algorithm}", f"Start: {self.start}", f"Goal: {self.goal}", f"Time: {self.time:.4f}s", f"Nodes expanded: {self.nodes}", f"Path len: {len(self.path)}", f"Cost: {self.cost}", "\nLayers:"]
        for d in sorted(self.layers.keys()):
            lines.append(f"Layer {d}: {', '.join(self.layers[d])}")
        self.info.insert(tk.END, "\n".join(lines))

    def play(self):
        self.is_playing = True
        self.animate()

    def pause(self):
        self.is_playing = False

    def step_forward(self):
        if self.current_step < len(self.visited_order):
            self.current_step += 1
            self.draw_step()
            self.update_info()

    def set_speed(self, val):
        self.speed = int(val)

    def animate(self):
        if not self.is_playing:
            return
        updated = False
        for _ in range(self.speed):
            if self.current_step < len(self.visited_order):
                self.current_step += 1
                updated = True
        if updated:
            self.draw_step(); self.update_info()
        self.window.after(100, self.animate)

# ----------------------- Run app -----------------------
def main():
    app = InputWindow()
    app.run()

if __name__ == '__main__':
    main()

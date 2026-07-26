import tkinter as tk
from tkinter import messagebox, ttk
import random
import time
import threading
import psutil
from collections import deque
from heapq import heappush, heappop
import importlib.util
import sys
import os

# Try to load algorithm modules from this directory (non-fatal).
ALGO_DIR = os.path.dirname(__file__)

def _load_algo_file(name: str):
    path = os.path.join(ALGO_DIR, f"{name}.py")
    if not os.path.exists(path):
        return None
    try:
        # Read source and do a quick safety check: if the module contains
        # top-level imperative calls (e.g. `input(...)`, `print(...)`) we
        # avoid importing it to prevent blocking or noisy side-effects.
        src = open(path, 'r', encoding='utf-8').read()
        try:
            import ast as _ast
            parsed = _ast.parse(src, filename=path)
            for node in parsed.body:
                # top-level expressions that are calls indicate imperative code
                if isinstance(node, _ast.Expr) and isinstance(node.value, _ast.Call):
                    return None
        except Exception:
            # if AST parsing fails for any reason, be conservative and skip
            return None

        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None

# Known algorithm module base names to attempt to load. It's okay if some are missing.
_EXTERNAL_ALG_CANDIDATES = [
    'BFS', 'DFS', 'UCS', 'Greedy', 'A_Star', 'Astar', 'BeamSearch', 'Beem', 'HillClimbing', 'HillClimping', 'IDAstar'
]
EXTERNAL_ALGOS = {}
for _name in _EXTERNAL_ALG_CANDIDATES:
    m = _load_algo_file(_name)
    if m is not None:
        EXTERNAL_ALGOS[_name] = m

DIRECTIONS = {"North": (0, -1), "South": (0, 1), "East": (1, 0), "West": (-1, 0)}
OPPOSITE = {"North": "South", "South": "North", "East": "West", "West": "East"}
WALL_COLOR, PATH_COLOR, VISITED_COLOR, START_COLOR, GOAL_COLOR, EMPTY_COLOR = "black", "yellow", "lightblue", "green", "red", "white"

class MazeGenerator:
    def __init__(self, w, h):
        self.width, self.height, self.maze = w, h, None
    
    def generate(self, callback=None):
        self.maze = {(x, y): {"North": True, "South": True, "East": True, "West": True} for y in range(self.height) for x in range(self.width)}
        visited, stack = set(), []
        x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
        visited.add((x, y))
        stack.append((x, y))
        
        while stack:
            x, y = stack[-1]
            neighbors = [(d, x + dx, y + dy) for d, (dx, dy) in DIRECTIONS.items() if 0 <= x + dx < self.width and 0 <= y + dy < self.height and (x + dx, y + dy) not in visited]
            
            if neighbors:
                d, nx, ny = random.choice(neighbors)
                self.maze[(x, y)][d] = False
                self.maze[(nx, ny)][OPPOSITE[d]] = False
                visited.add((nx, ny))
                stack.append((nx, ny))
                if callback:
                    callback(list(visited))
            else:
                stack.pop()
        return self.maze

class MazeSearcher:
    def __init__(self, maze, start, goal, width, height, stop_check=None, move_delay=0.0):
        self.maze, self.start, self.goal, self.width, self.height = maze, start, goal, width, height
        # stop_check: callable returning True when search should stop
        self.stop_check = stop_check or (lambda: False)
        self.visited, self.path, self.nodes_expanded = [], [], 0
        # store starting memory in KB
        self.start_mem = psutil.Process().memory_info().rss / 1024.0
        # track peak memory seen during search (KB)
        self.max_mem = self.start_mem
        # per-move delay (seconds) during search
        self.move_delay = float(move_delay or 0.0)

        # expose any externally loaded algorithm modules to this instance
        try:
            self.external_algos = EXTERNAL_ALGOS
        except Exception:
            self.external_algos = {}

    def _try_external(self, alg_key, callback=None):
        """Attempt to call an externally loaded algorithm module.

        Returns:
            - True/False if external algorithm ran and returned success flag
            - None if no external algorithm was available or it failed
        Side effects: may set `self.visited`, `self.path`, and `self.nodes_expanded` if the external
        function returns a tuple like (visited, path, nodes_expanded).
        """
        mod = self.external_algos.get(alg_key)
        if not mod:
            return None
        # candidate function names to try in the external module
        fn_names = ('BFS','bfs','DFS','dfs','UCS','ucs','Greedy','greedy','A_Star','A_Star','Astar','A_Star','A_Star','HillClimbing','Hill','hill_climb','BeamSearch','beam_search','IDAstar','IDA_star','search','run')
        for fname in fn_names:
            fn = getattr(mod, fname, None)
            if callable(fn):
                try:
                    # many external modules accept different signatures; provide common ones
                    res = fn(self.maze, self.start, self.goal, neighbors_fn=self.get_neighbors, heuristic_fn=self.heuristic, callback=callback, stop_check=self.stop_check, move_delay=self.move_delay)
                except TypeError:
                    # try simpler signatures
                    try:
                        res = fn(self.start, self.goal)
                    except Exception:
                        continue
                except Exception:
                    continue
                # Interpret return values
                if isinstance(res, bool):
                    return res
                if isinstance(res, tuple):
                    if len(res) >= 1 and res[0] is not None:
                        try:
                            self.visited = list(res[0])
                        except Exception:
                            pass
                    if len(res) >= 2 and res[1] is not None:
                        try:
                            self.path = list(res[1])
                        except Exception:
                            pass
                    if len(res) >= 3 and res[2] is not None:
                        try:
                            self.nodes_expanded = int(res[2])
                        except Exception:
                            pass
                    return True
                # fallback: truthiness
                return bool(res)
        return None

    def _sleep_with_stop(self, seconds):
        """Sleep up to `seconds` but break early if `stop_check()` becomes True.
        Returns True if slept fully, False if interrupted by stop request.
        """
        if seconds <= 0:
            return True
        end = time.time() + seconds
        # choose a small grain so stop becomes responsive even for longer sleeps
        grain = min(0.01, seconds)
        while time.time() < end:
            if self.stop_check():
                return False
            time.sleep(min(grain, end - time.time()))
        return True

    def _sample_mem(self):
        """Sample current RSS and update peak memory (KB)."""
        try:
            cur = psutil.Process().memory_info().rss / 1024.0
            if cur > self.max_mem:
                self.max_mem = cur
        except Exception:
            pass
    
    def get_neighbors(self, node):
        x, y = node
        return [(x + dx, y + dy) for d, (dx, dy) in DIRECTIONS.items() if (x + dx, y + dy) in self.maze and not self.maze[(x, y)][d]]
    
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def reconstruct_path(self, parent):
        path, current = [], self.goal
        while current:
            path.append(current)
            current = parent.get(current)
        return path[::-1]
    
    def get_memory(self):
        # return memory delta in KB
        try:
            # return peak delta seen during the search (KB)
            return max(0.0, self.max_mem - self.start_mem)
        except Exception:
            try:
                return max(0.0, psutil.Process().memory_info().rss / 1024.0 - self.start_mem)
            except Exception:
                return 0.0
    
    def BFS(self, callback=None):
        # Try external implementation first
        try:
            ext = self._try_external('BFS', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        queue = deque([self.start])
        parent = {self.start: None}
        visited = {self.start}
        while queue:
            if self.stop_check():
                return False
            node = queue.popleft()
            self.visited.append(node)
            self.nodes_expanded += 1
            # sample memory after expanding a node
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            if node == self.goal:
                self.path = self.reconstruct_path(parent)
                return True
            for nb in self.get_neighbors(node):
                if self.stop_check():
                    return False
                if nb not in visited:
                    visited.add(nb)
                    parent[nb] = node
                    queue.append(nb)
        return False
    
    def DFS(self, callback=None):
        try:
            ext = self._try_external('DFS', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        stack = [self.start]
        parent = {self.start: None}
        visited = {self.start}
        while stack:
            if self.stop_check():
                return False
            node = stack.pop()
            self.visited.append(node)
            self.nodes_expanded += 1
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            if node == self.goal:
                self.path = self.reconstruct_path(parent)
                return True
            for nb in self.get_neighbors(node):
                if self.stop_check():
                    return False
                if nb not in visited:
                    visited.add(nb)
                    parent[nb] = node
                    stack.append(nb)
        return False
    
    def UCS(self, callback=None):
        try:
            ext = self._try_external('UCS', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        heap = [(0, self.start)]
        parent = {self.start: None}
        cost = {self.start: 0}
        visited = set()
        while heap:
            if self.stop_check():
                return False
            c, node = heappop(heap)
            if node in visited: continue
            visited.add(node)
            self.visited.append(node)
            self.nodes_expanded += 1
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            if node == self.goal:
                self.path = self.reconstruct_path(parent)
                return True
            for nb in self.get_neighbors(node):
                if self.stop_check():
                    return False
                if nb not in visited:
                    nc = c + 1
                    if nb not in cost or nc < cost[nb]:
                        cost[nb] = nc
                        parent[nb] = node
                        heappush(heap, (nc, nb))
        return False
    
    def Greedy(self, callback=None):
        try:
            ext = self._try_external('Greedy', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        heap = [(self.heuristic(self.start, self.goal), self.start)]
        parent = {self.start: None}
        visited = set()
        while heap:
            if self.stop_check():
                return False
            _, node = heappop(heap)
            if node in visited: continue
            visited.add(node)
            self.visited.append(node)
            self.nodes_expanded += 1
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            if node == self.goal:
                self.path = self.reconstruct_path(parent)
                return True
            for nb in self.get_neighbors(node):
                if self.stop_check():
                    return False
                if nb not in visited:
                    parent[nb] = node
                    heappush(heap, (self.heuristic(nb, self.goal), nb))
        return False
    
    def A_Star(self, callback=None):
        try:
            # try both A_Star and Astar module names
            ext = self._try_external('A_Star', callback=callback)
            if ext is None:
                ext = self._try_external('Astar', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        heap = [(self.heuristic(self.start, self.goal), 0, self.start)]
        parent = {self.start: None}
        g_cost = {self.start: 0}
        visited = set()
        ctr = 0
        while heap:
            if self.stop_check():
                return False
            _, g, node = heappop(heap)
            if node in visited: continue
            visited.add(node)
            self.visited.append(node)
            self.nodes_expanded += 1
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            if node == self.goal:
                self.path = self.reconstruct_path(parent)
                return True
            for nb in self.get_neighbors(node):
                if self.stop_check():
                    return False
                if nb not in visited:
                    ng = g + 1
                    if nb not in g_cost or ng < g_cost[nb]:
                        g_cost[nb] = ng
                        parent[nb] = node
                        ctr += 1
                        heappush(heap, (ng + self.heuristic(nb, self.goal), ng, nb))
        return False
    
    def HillClimbing(self, callback=None):
        try:
            ext = self._try_external('HillClimbing', callback=callback)
            if ext is None:
                ext = self._try_external('HillClimping', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        cur = self.start
        visited = {cur}
        while cur != self.goal:
            if self.stop_check():
                return False
            self.visited.append(cur)
            self.nodes_expanded += 1
            self._sample_mem()
            if self.move_delay:
                if not self._sleep_with_stop(self.move_delay):
                    return False
            if callback: callback(self.visited[:], self.path[:])
            nb = self.get_neighbors(cur)
            if self.stop_check():
                return False
            if not nb: return False
            best = min(nb, key=lambda n: self.heuristic(n, self.goal))
            if self.heuristic(best, self.goal) >= self.heuristic(cur, self.goal) or best in visited: return False
            visited.add(best)
            cur = best
        self.visited.append(cur)
        self.path = [cur]
        return True
    
    def BeamSearch(self, callback=None, bw=5):
        try:
            ext = self._try_external('BeamSearch', callback=callback)
            if ext is None:
                ext = self._try_external('Beem', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass

        lvl = [self.start]
        parent = {self.start: None}
        visited = {self.start}
        while lvl:
            if self.stop_check():
                return False
            nlvl = []
            for node in lvl:
                self.visited.append(node)
                self.nodes_expanded += 1
                self._sample_mem()
                if self.move_delay:
                    if not self._sleep_with_stop(self.move_delay):
                        return False
                if callback: callback(self.visited[:], self.path[:])
                if node == self.goal:
                    self.path = self.reconstruct_path(parent)
                    return True
                for nb in self.get_neighbors(node):
                    if self.stop_check():
                        return False
                    if nb not in visited:
                        visited.add(nb)
                        parent[nb] = node
                        nlvl.append(nb)
            nlvl.sort(key=lambda n: self.heuristic(n, self.goal))
            lvl = nlvl[:bw]
        return False
    
    def IDAstar(self, callback=None):
        try:
            ext = self._try_external('IDAstar', callback=callback)
            if ext is not None:
                return bool(ext)
        except Exception:
            pass
        return self.A_Star(callback=callback)

class MazeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze Solver")
        self.root.geometry("1920x1080")
        self.width, self.height = 50, 50
        self.maze, self.start, self.goal, self.results, self.running = {}, None, None, {}, False
        self.cell_size = 18
        # target seconds for full generation (adjustable)
        # reduced to make generation way faster (smaller delay)
        self.gen_target_seconds = 0.12
        # small per-move delay (seconds) applied during generation and search
        # set to 0.001 (1ms) to make moves slightly visible but keep overall speed
        self.move_delay = 0.001
        # predeclare attributes used by the generator/renderer to satisfy linters
        self.cell_items = {}
        self._visited_drawn = set()
        # store wall line items: keys are (x,y,direction)
        self.wall_items = {}
        # stop event to cancel running algorithms
        self.stop_event = threading.Event()
        self.create_ui()
        self.start_gen()
    
    def create_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Maze canvas
        self.left = ttk.LabelFrame(main, text=f"Maze ({self.width}x{self.height})", padding=10)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Size controls above the canvas
        size_frame = ttk.Frame(self.left)
        size_frame.pack(fill=tk.X, pady=(0,6))
        ttk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
        self.size_w_var = tk.IntVar(value=self.width)
        self.size_h_var = tk.IntVar(value=self.height)
        w_spin = tk.Spinbox(size_frame, from_=5, to=200, textvariable=self.size_w_var, width=6)
        w_spin.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(size_frame, text="Height:").pack(side=tk.LEFT)
        h_spin = tk.Spinbox(size_frame, from_=5, to=200, textvariable=self.size_h_var, width=6)
        h_spin.pack(side=tk.LEFT, padx=(4,8))
        tk.Button(size_frame, text="Apply Size", command=self.apply_size, font=("Arial", 9)).pack(side=tk.LEFT, padx=(6,0))

        canvas_frame = ttk.Frame(self.left)
        canvas_frame.pack(padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=self.width * self.cell_size, height=self.height * self.cell_size, relief=tk.SUNKEN, bd=2)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click_canvas)

        self.status = tk.Label(self.left, text="Generating...", font=("Arial", 10), fg="blue")
        self.status.pack(pady=8)

        # Right panel - Controls & Results
        right = ttk.LabelFrame(main, text="Controls & Results", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Generate button
        gen_btn = tk.Button(right, text="Generate Maze", command=self.start_gen, bg="#224522", fg="white", font=("Arial", 10, "bold"))
        gen_btn.pack(fill=tk.X, pady=(0,10))

        # Algorithm selection
        ttk.Label(right, text="Select Algorithms for Compare:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(5,5))
        self.avars = {}
        algos = ["BFS", "DFS", "UCS", "Greedy", "A*", "IDA*", "Hill", "Beam"]
        for a in algos:
            v = tk.BooleanVar(value=True)
            self.avars[a] = v
            ttk.Checkbutton(right, text=a, variable=v).pack(anchor=tk.W, padx=12)

        # Individual algorithm buttons
        ttk.Label(right, text="Run Individual Algorithm:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10,3))
        algo_btn_frame = ttk.Frame(right)
        algo_btn_frame.pack(fill=tk.X, pady=3)
        for a in algos:
            btn = tk.Button(algo_btn_frame, text=a, command=lambda name=a: threading.Thread(target=self.run_algo, args=(name,), daemon=True).start(),
                           bg="#048989", fg="white", font=("Arial", 9, "bold"), width=10)
            btn.pack(side=tk.LEFT, padx=2, pady=2, expand=True, fill=tk.X)

        # Action buttons
        action_frame = ttk.Frame(right)
        action_frame.pack(fill=tk.X, pady=8)
        ttk.Button(action_frame, text="Solve & Run Selected", command=self.run_sel).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(action_frame, text="Run All", command=self.run_all).pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Stop / Continue buttons
        control_frame = ttk.Frame(right)
        control_frame.pack(fill=tk.X, pady=6)
        tk.Button(control_frame, text="Stop", command=self.request_stop, bg="#FF0000", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        tk.Button(control_frame, text="Continue", command=self.clear_stop, bg="#085403", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Results box
        ttk.Label(right, text="Results:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10,3))
        res_frame = ttk.Frame(right)
        res_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(res_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.res_text = tk.Text(res_frame, height=16, width=40, yscrollcommand=sb.set)
        self.res_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.res_text.yview)

        # Analysis buttons (kept but analysis logic unchanged)
        ana_frame = ttk.Frame(right)
        ana_frame.pack(fill=tk.X, pady=6)
        ttk.Button(ana_frame, text="Show Performance Graph", command=self.draw_hist).pack(side=tk.LEFT, padx=2)
        ttk.Button(ana_frame, text="Show Best", command=self.show_best).pack(side=tk.LEFT, padx=2)
        # keep a reference so we can disable it after the recommended algorithm is already run
        self.recommend_btn = ttk.Button(ana_frame, text="Recommend", command=self.recommend)
        self.recommend_btn.pack(side=tk.LEFT, padx=2)
        # Fast search option (disable visualization to speed up searches)
        self.fast_search_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ana_frame, text="Fast Search (no visualization)", variable=self.fast_search_var).pack(side=tk.LEFT, padx=6)
        # Animate final path option
        self.animate_path_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ana_frame, text="Animate Final Path", variable=self.animate_path_var).pack(side=tk.LEFT, padx=6)

        # Histogram canvas (reuse existing)
        self.hist_c = tk.Canvas(right, height=120, bg="white", relief=tk.SUNKEN, bd=1)
        self.hist_c.pack(fill=tk.BOTH, expand=False, pady=(6,0))
    
    def start_gen(self):
        if self.running: return
        self.running = True
        self.start = self.goal = None
        self.results.clear()
        self.res_text.config(state=tk.NORMAL)
        self.res_text.delete("1.0", tk.END)
        self.res_text.config(state=tk.DISABLED)
        self.status.config(text="Generating... (5s)", fg="blue")
        def gen_t():
            try:
                # prepare canvas grid items once (lightgray background)
                try:
                    self.canvas.delete("all")
                except:
                    pass
                self.cell_items = {}
                for y in range(self.height):
                    for x in range(self.width):
                        x1 = x * self.cell_size
                        y1 = y * self.cell_size
                        x2 = (x + 1) * self.cell_size
                        y2 = (y + 1) * self.cell_size
                        item = self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgray", outline="")
                        self.cell_items[(x, y)] = item
                self.canvas.update_idletasks()

                g = MazeGenerator(self.width, self.height)
                start_time = time.time()
                total_cells = float(self.width * self.height)
                # compute cells_per_sec from desired total seconds
                cells_per_sec = max(1.0, total_cells / max(0.01, self.gen_target_seconds))

                latest = {'queue': deque()}
                lock = threading.Lock()
                gen_done = [False]
                self._visited_drawn = set()
                gen_seen = set()

                def upd(v):
                    # v is full visited list; compute only newly visited cells and enqueue them
                    if not v:
                        return
                    new_added = []
                    with lock:
                        for cell in v:
                            if cell not in gen_seen:
                                gen_seen.add(cell)
                                latest['queue'].append(cell)
                                new_added.append(cell)
                        # keep a live reference to maze so frame renderer can read wall state
                        try:
                            self.maze = g.maze
                        except:
                            pass
                    # tiny per-move delay for generation (outside lock)
                    if new_added and self.move_delay:
                        for _ in new_added:
                            time.sleep(self.move_delay)
                    # pacing: sleep to meet the global target time based on actual cells
                    cells = len(gen_seen)
                    elapsed = time.time() - start_time
                    target_time = float(cells) / cells_per_sec
                    if target_time > elapsed:
                        time.sleep(target_time - elapsed)

                # frame renderer (runs in main thread via after)
                frame_ms = 20  # ~50 FPS for snappier updates
                def frame():
                    # pop a small batch from the queue each frame to avoid instant fill
                    # use a smaller divisor to process larger batches and reduce delay
                    batch_size = max(1, int(cells_per_sec * (frame_ms / 1000.0) / 2))
                    q = []
                    with lock:
                        for _ in range(batch_size):
                            if not latest['queue']:
                                break
                            q.append(latest['queue'].popleft())
                    if q:
                        for cell in q:
                            if cell not in self._visited_drawn:
                                item = self.cell_items.get(cell)
                                if item:
                                    try:
                                        self.canvas.itemconfig(item, fill="white")
                                    except:
                                        pass
                                # after coloring cell, draw/delete its walls according to current maze
                                cx, cy = cell
                                try:
                                    cell_info = self.maze.get((cx, cy)) if self.maze else None
                                except Exception:
                                    cell_info = None
                                if cell_info:
                                    for d, (dx, dy) in DIRECTIONS.items():
                                        key = (cx, cy, d)
                                        has_wall = bool(cell_info.get(d, True))
                                        if has_wall:
                                            if key not in self.wall_items:
                                                x1 = cx * self.cell_size
                                                y1 = cy * self.cell_size
                                                x2 = (cx + 1) * self.cell_size
                                                y2 = (cy + 1) * self.cell_size
                                                try:
                                                    if d == 'North': w = self.canvas.create_line(x1, y1, x2, y1, fill=WALL_COLOR, width=1)
                                                    elif d == 'South': w = self.canvas.create_line(x1, y2, x2, y2, fill=WALL_COLOR, width=1)
                                                    elif d == 'East': w = self.canvas.create_line(x2, y1, x2, y2, fill=WALL_COLOR, width=1)
                                                    else: w = self.canvas.create_line(x1, y1, x1, y2, fill=WALL_COLOR, width=1)
                                                    self.wall_items[key] = w
                                                except:
                                                    pass
                                        else:
                                            if key in self.wall_items:
                                                try:
                                                    self.canvas.delete(self.wall_items.pop(key))
                                                except:
                                                    pass
                                self._visited_drawn.add(cell)
                        self.canvas.update_idletasks()
                    if not gen_done[0] or latest['queue']:
                        self.root.after(frame_ms, frame)

                # start frame loop
                self.root.after(frame_ms, frame)

                g.generate(callback=upd)

                # generation finished
                gen_done[0] = True
                self.maze = g.maze
                # final draw including walls and ready status
                self.root.after(0, self.draw_maze)
                self.root.after(0, lambda: self.status.config(text="Ready! Click to set Start/Goal", fg="green"))
            finally:
                self.running = False

        t = threading.Thread(target=gen_t, daemon=True)
        t.start()
    
    
    def draw_maze_gen(self, visited_cells):
        """Draw maze during generation - shows walls and visited cells"""
        if not self.maze:
            return
        try:
            self.canvas.delete("all")
        except:
            return
        
        vs = set(visited_cells or [])
        for (x, y), cell in self.maze.items():
            x1 = x * self.cell_size
            y1 = y * self.cell_size
            x2 = (x + 1) * self.cell_size
            y2 = (y + 1) * self.cell_size
            
            # Color: white if visited/carved, light gray if not yet visited
            col = "white" if (x, y) in vs else "lightgray"
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=col, outline="")
            
            # Draw walls during generation
            if cell["North"]:
                self.canvas.create_line(x1, y1, x2, y1, fill=WALL_COLOR, width=1)
            if cell["South"]:
                self.canvas.create_line(x1, y2, x2, y2, fill=WALL_COLOR, width=1)
            if cell["East"]:
                self.canvas.create_line(x2, y1, x2, y2, fill=WALL_COLOR, width=1)
            if cell["West"]:
                self.canvas.create_line(x1, y1, x1, y2, fill=WALL_COLOR, width=1)
        
        self.canvas.update_idletasks()
    
    def draw_maze(self, vh=None, ph=None):
        if not self.maze: return
        try:
            self.canvas.delete("all")
        except: return
        vs, ps = set(vh or []), set(ph or [])
        for (x, y), cell in self.maze.items():
            x1, y1, x2, y2 = x * self.cell_size, y * self.cell_size, (x + 1) * self.cell_size, (y + 1) * self.cell_size
            if (x, y) == self.start: col = START_COLOR
            elif (x, y) == self.goal: col = GOAL_COLOR
            elif (x, y) in ps: col = PATH_COLOR
            elif (x, y) in vs: col = VISITED_COLOR
            else: col = EMPTY_COLOR
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=col, outline="")
            if cell["North"]: self.canvas.create_line(x1, y1, x2, y1, fill=WALL_COLOR, width=1)
            if cell["South"]: self.canvas.create_line(x1, y2, x2, y2, fill=WALL_COLOR, width=1)
            if cell["East"]: self.canvas.create_line(x2, y1, x2, y2, fill=WALL_COLOR, width=1)
            if cell["West"]: self.canvas.create_line(x1, y1, x1, y2, fill=WALL_COLOR, width=1)
        # draw path on top to ensure visibility (small inset rectangle)
        if ps:
            inset = max(1, int(self.cell_size * 0.18))
            for (x, y) in ps:
                x1 = x * self.cell_size + inset
                y1 = y * self.cell_size + inset
                x2 = (x + 1) * self.cell_size - inset
                y2 = (y + 1) * self.cell_size - inset
                try:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=PATH_COLOR, outline="")
                except Exception:
                    pass

    def animate_path(self, path, idx=0, delay_ms=40):
        """Animate the final path by drawing one path cell every delay_ms milliseconds.
        Uses the canvas tag 'path_anim' so previous animations are cleared when starting a new one.
        """
        try:
            # clear any prior animation overlays
            try:
                self.canvas.delete('path_anim')
            except Exception:
                pass
            if not path:
                return
            # draw up to idx inclusive
            inset = max(1, int(self.cell_size * 0.18))
            for i in range(0, idx + 1):
                x, y = path[i]
                x1 = x * self.cell_size + inset
                y1 = y * self.cell_size + inset
                x2 = (x + 1) * self.cell_size - inset
                y2 = (y + 1) * self.cell_size - inset
                # tag the item so we can delete them together later
                try:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=PATH_COLOR, outline="", tags=('path_anim',))
                except Exception:
                    pass
            # if not done, schedule next frame
            if idx + 1 < len(path):
                self.root.after(delay_ms, lambda: self.animate_path(path, idx + 1, delay_ms))
        except Exception:
            return
    
    def click_canvas(self, e):
        if not self.maze: return
        x, y = e.x // self.cell_size, e.y // self.cell_size
        if not (0 <= x < self.width and 0 <= y < self.height): return
        if self.start is None:
            self.start = (x, y)
            self.status.config(text=f"Start: {self.start} | Click Goal", fg="blue")
        elif self.goal is None:
            if (x, y) == self.start:
                messagebox.showwarning("Warning", "Goal != Start")
                return
            self.goal = (x, y)
            self.status.config(text=f"Ready! Start: {self.start}, Goal: {self.goal}", fg="green")
        else:
            self.start = (x, y)
            self.goal = None
            self.status.config(text=f"Start reset | Click Goal", fg="blue")
        self.draw_maze()
    
    def run_algo(self, name):
        if not self.start or not self.goal:
            messagebox.showwarning("Warning", "Set start and goal")
            return
        self.status.config(text=f"Running {name}...", fg="orange")
        self.root.update_idletasks()
        try:
            # reset stop event for this run
            self.stop_event.clear()
            t0 = time.time()
            # pass a stop_check callable so searcher cooperatively exits when stop_event set
            s = MazeSearcher(self.maze, self.start, self.goal, self.width, self.height, stop_check=lambda: self.stop_event.is_set(), move_delay=self.move_delay)

            # build a throttled callback for visualization. If fast mode is enabled, don't pass a callback
            if self.fast_search_var.get():
                # use a no-op callback to avoid type warnings while skipping GUI work
                def cb(v, p):
                    return None
            else:
                last = {"t": 0.0}
                # lower interval -> more draws; increase for faster search
                draw_interval = 0.06  # seconds between GUI updates (throttle)
                def cb(v, p):
                    now = time.time()
                    if now - last["t"] >= draw_interval:
                        last["t"] = now
                        # schedule draw on main thread
                        try:
                            self.root.after(0, self.draw_maze, v, p)
                        except Exception:
                            pass

            amap = {"BFS": s.BFS, "DFS": s.DFS, "UCS": s.UCS, "Greedy": s.Greedy, "A*": s.A_Star, "IDA*": s.IDAstar, "Hill": s.HillClimbing, "Beam": s.BeamSearch}

            # start a timer to enforce an 8 second timeout
            timeout_seconds = 8.0
            timer = threading.Timer(timeout_seconds, lambda: self.stop_event.set())
            timer.start()
            ok = amap[name](callback=cb)
            timer.cancel()
            # After search finishes, clear the transient 'visited' (blue) overlay so
            # the path animation can be shown on a clean maze. Then either animate
            # the path step-by-step or draw it instantly depending on setting.
            try:
                # redraw maze without visited/path to remove blue visited cells
                self.root.after(0, self.draw_maze)
            except Exception:
                pass
            try:
                if s.path:
                    # remove any prior animation overlays
                    try:
                        self.canvas.delete('path_anim')
                    except Exception:
                        pass
                    if self.animate_path_var.get():
                        # start animation shortly after clearing visited cells
                        self.root.after(80, lambda: self.animate_path(s.path, 0, delay_ms=30))
                    else:
                        # draw full path (no animation) shortly after clearing visited
                        self.root.after(80, lambda: self.draw_maze([], s.path))
                else:
                    # ensure no lingering animation tags
                    try:
                        self.canvas.delete('path_anim')
                    except Exception:
                        pass
            except Exception:
                pass

            t1 = time.time() - t0
            m = s.get_memory()
            # determine success: ok True and not stopped
            success = bool(ok) and (not self.stop_event.is_set())
            self.results[name] = {"time": t1, "memory": m, "nodes": s.nodes_expanded, "path_length": len(s.path) if s.path else 0, "success": success}
            self.upd_res()
            if success:
                self.status.config(text=f"✓ {name} done", fg="green")
            else:
                self.status.config(text=f"✗ {name} stopped/timeout", fg="red")
        except Exception as e:
            self.status.config(text=f"✗ {name} error", fg="red")
    
    def run_sel(self):
        sel = [a for a, v in self.avars.items() if v.get()]
        if not sel:
            messagebox.showwarning("Warning", "Select algorithm")
            return
        def rt():
            for a in sel:
                self.run_algo(a)
                time.sleep(0.2)
        t = threading.Thread(target=rt, daemon=True)
        t.start()
    
    def run_all(self):
        for v in self.avars.values(): v.set(True)
        self.run_sel()
    
    def upd_res(self):
        self.res_text.config(state=tk.NORMAL)
        self.res_text.delete("1.0", tk.END)
        h = f"{'Algo':<10} {'Time(s)':<10} {'Mem(KB)':<12} {'Nodes':<10} {'Path':<10} {'OK':<5}\n"
        h += "-" * 55 + "\n"
        self.res_text.insert(tk.END, h)
        # tag for unsolved entries
        try:
            self.res_text.tag_config('unsolved', foreground='red')
        except Exception:
            pass
        for a, s in sorted(self.results.items()):
            mem = s.get('memory', 0.0)
            mem_str = f"{mem:.2f}" if mem >= 0.01 else "<0.01"
            l = f"{a:<10} {s['time']:<10.4f} {mem_str:<12} {s['nodes']:<10} {s['path_length']:<10} {'✓' if s['success'] else '✗':<5}\n"
            self.res_text.insert(tk.END, l)
            if not s.get('success'):
                # tag the last inserted line as unsolved (red)
                try:
                    line_no = int(self.res_text.index('end-1c').split('.')[0])
                    self.res_text.tag_add('unsolved', f"{line_no}.0", f"{line_no}.end")
                except Exception:
                    pass
        self.res_text.config(state=tk.DISABLED)

    def request_stop(self):
        """Request cooperative stop for running algorithms."""
        try:
            self.stop_event.set()
        except Exception:
            pass
        try:
            self.status.config(text="Stop requested", fg="red")
        except Exception:
            pass

    def clear_stop(self):
        """Clear stop flag to allow future runs to proceed."""
        try:
            self.stop_event.clear()
        except Exception:
            pass
        # restore a sensible status line
        try:
            if self.start and self.goal:
                self.status.config(text=f"Ready! Start: {self.start}, Goal: {self.goal}", fg="green")
            else:
                self.status.config(text="Ready", fg="green")
        except Exception:
            pass

    def apply_size(self):
        """Apply the width/height from the UI, resize canvas and regenerate maze."""
        try:
            w = int(self.size_w_var.get())
            h = int(self.size_h_var.get())
        except Exception:
            messagebox.showwarning("Size", "Enter valid integer sizes")
            return
        w = max(5, min(200, w))
        h = max(5, min(200, h))
        self.width, self.height = w, h
        try:
            self.left.config(text=f"Maze ({self.width}x{self.height})")
        except Exception:
            pass
        try:
            self.canvas.config(width=self.width * self.cell_size, height=self.height * self.cell_size)
        except Exception:
            pass
        # request stop of any running search/generation and restart generation shortly
        self.request_stop()
        # clear stop and start new generation after a short delay
        self.root.after(180, lambda: (self.clear_stop(), self.start_gen()))
    
    def draw_hist(self):
        # Redirect histogram request to the full performance graph window
        # kept for compatibility with previous UI wiring
        self.show_graph()

    def show_graph(self):
        """Show a simple performance bar graph for timings."""
        if not self.results:
            messagebox.showinfo("Graph", "No results to show")
            return
        # New detailed performance comparison window (text + metric bars)
        items = sorted(self.results.items())
        names = [n for n, _ in items]
        nodes = [float(r.get('nodes', 0) or 0) for _, r in items]
        times = [float(r.get('time', 0) or 0) for _, r in items]
        paths = [int(r.get('path_length', -1) if r.get('path_length', -1) is not None else -1) for _, r in items]
        # memory is stored as KB already in this UI; ensure numeric
        mems = [float(r.get('memory', 0) or 0) for _, r in items]

        win = tk.Toplevel(self.root)
        win.title("Performance Comparison")
        # Larger default size for easier reading
        try:
            win.geometry('1100x700')
        except Exception:
            pass

        # Top: text summary and legend
        top_frame = ttk.Frame(win)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        info = tk.Text(top_frame, height=8, width=120, font=("Courier", 10))
        info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        info.insert(tk.END, "Algorithm\tNodes\tTime(s)\tPath\tMemory(KB)\n")
        info.insert(tk.END, "-------------------------------------------------------------\n")
        for name, r in items:
            info.insert(tk.END, f"{name}\t{r.get('nodes',0)}\t{r.get('time',0):.3f}\t{r.get('path_length',-1)}\t{r.get('memory',0):.2f}\n")
        info.config(state=tk.DISABLED)

        # Canvas chart: each algorithm gets one row with four metric bars (Nodes, Time, Path, Memory)
        # Legend canvas (uses same icons as Maze visualization)
        legend = tk.Canvas(top_frame, width=240, height=80, bg='white', highlightthickness=0)
        legend.pack(side=tk.RIGHT, padx=(6,0))
        # draw legend items: Obstacle (black), Start (green S), Goal (red G), Open (white), Exploring (yellow+orange)
        lx = 8
        ly = 12
        sz = 18
        # obstacle
        legend.create_rectangle(lx, ly, lx+sz, ly+sz, fill='black', outline='gray')
        legend.create_text(lx+sz+6, ly+sz//2, anchor='w', text='Obstacle', font=("Arial", 9))
        # start
        sy = ly + 20
        legend.create_rectangle(lx, sy, lx+sz, sy+sz, fill='lightgreen', outline='gray')
        legend.create_text(lx+sz+6, sy+sz//2, anchor='w', text='Start (S)', font=("Arial", 9))
        # goal
        gy = sy + 20
        legend.create_rectangle(lx+120, ly, lx+120+sz, ly+sz, fill='lightcoral', outline='gray')
        legend.create_text(lx+120+sz+6, ly+sz//2, anchor='w', text='Goal (G)', font=("Arial", 9))
        # exploring (yellow with orange dot)
        legend.create_rectangle(lx+120, sy, lx+120+sz, sy+sz, fill='lightyellow', outline='gray')
        legend.create_oval(lx+120+4, sy+4, lx+120+sz-4, sy+sz-4, fill='orange', outline='orange')

        # Main canvas for metric bars (wider to match window)
        canvas = tk.Canvas(win, height=max(300, 30 * max(1, len(names))), width=1040, bg='white')
        canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # layout
        cwidth = 1000
        name_col = 220
        gap = 8
        metrics = ['Nodes', 'Time(s)', 'Path', 'Memory(KB)']
        metric_colors = ['steelblue', 'coral', 'lightgreen', 'khaki']
        metric_values = [nodes, times, [p if p >= 0 else 0 for p in paths], mems]

        rows = len(names)
        row_h = 28
        padding_top = 10

        # compute max per metric for scaling (avoid zero division)
        max_vals = [max(vals) if vals and max(vals) > 0 else 1 for vals in metric_values]

        # compute bar area width for each metric column
        bar_area = cwidth - name_col - (len(metrics)-1)*gap
        metric_width = bar_area // len(metrics)

        # header
        canvas.create_text(10, padding_top, anchor='w', text='Algorithm', font=("Arial", 10, 'bold'))
        for mi, m in enumerate(metrics):
            x = name_col + mi*(metric_width+gap) + metric_width//2
            canvas.create_text(x, padding_top, text=m, font=("Arial", 10, 'bold'))

        # draw rows
        for i, name in enumerate(names):
            y = padding_top + 18 + i*row_h
            # algorithm name
            canvas.create_text(10, y, anchor='w', text=name, font=("Arial", 10))
            # draw metric bars
            for mi, vals in enumerate(metric_values):
                v = vals[i]
                maxv = max_vals[mi]
                x0 = name_col + mi*(metric_width+gap)
                y0 = y - (row_h//3)
                full_w = metric_width - 4
                w = int((v / maxv) * full_w) if maxv > 0 else 0
                # background box
                canvas.create_rectangle(x0, y0, x0+full_w, y0+ (row_h//1.5), fill='#f0f0f0', outline='#cccccc')
                if w > 0:
                    canvas.create_rectangle(x0+1, y0+1, x0+1+w, y0 + (row_h//1.5) -1, fill=metric_colors[mi], outline='black')
                # value label
                val_text = f"{v:.2f}" if isinstance(v, float) else str(v)
                if mi == 3:
                    # memory show KB with 2 decimals
                    val_text = f"{v:.2f} KB"
                canvas.create_text(x0 + full_w + 6, y, anchor='w', text=val_text, font=("Arial", 9))

        win.transient(self.root)
        win.grab_set()
        win.focus_set()
    
    def show_best(self):
        ok = {a: s for a, s in self.results.items() if s['success']}
        if not ok:
            messagebox.showinfo("Best", "No solution found")
            return
        b = min(ok.items(), key=lambda kv: (kv[1]['time'], kv[1]['nodes']))
        messagebox.showinfo("Best", f"{b[0]}\nTime: {b[1]['time']:.4f}s\nMemory: {b[1]['memory']:.2f} KB\nNodes: {b[1]['nodes']}")
    
    def recommend(self):
        ok = {a: s for a, s in self.results.items() if s['success']}
        if not ok:
            messagebox.showinfo("Recommend", "Run algorithms first\nA* is usually best for mazes")
            return
        def norm(a, v):
            mn, mx = min(a), max(a)
            return 0 if mn == mx else (v - mn) / (mx - mn)
        t = [s['time'] for s in ok.values()]
        m = [s['memory'] for s in ok.values()]
        n = [s['nodes'] for s in ok.values()]
        scores = {a: norm(t, s['time']) + norm(m, s['memory']) + norm(n, s['nodes']) for a, s in ok.items()}
        best = min(scores.items(), key=lambda kv: kv[1])
        messagebox.showinfo("Recommend", f"Best: {best[0]}\nScore: {best[1]:.3f}")
        # If the recommended algorithm has already been run successfully, disable the Recommend button
        try:
            rec_name = best[0]
            if rec_name in self.results and self.results[rec_name].get('success'):
                try:
                    self.recommend_btn.config(state='disabled')
                except Exception:
                    try:
                        self.recommend_btn.state(['disabled'])
                    except Exception:
                        pass
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MazeGUI(root)
    root.mainloop()

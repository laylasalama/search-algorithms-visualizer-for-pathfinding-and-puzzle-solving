import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import sys
import subprocess
import os
import ast
import importlib.util
import tracemalloc

# ================================
#   GRID GUI WITH MOUSE DRAWING
# ================================

class GridDrawerGUI:
    def __init__(self, root):
        self.root = root
        # Responsive scaling so layout fits well on 1920x1080 laptops
        self.root = root
        self.root.title("Grid Pathfinding - Draw Your Grid with Mouse")
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except:
            sw, sh = 1920, 1080
        # scale relative to 1920x1080
        self.ui_scale = min(max(0.6, sw / 1920.0), max(0.6, sh / 1080.0))
        # default geometry: use most of the screen but leave some space
        try:
            geom_w = int(sw * 0.95)
            geom_h = int(sh * 0.9)
            self.root.geometry(f"{geom_w}x{geom_h}")
        except:
            self.root.geometry("1500x800")

        # font scale helper
        self.sf = lambda s: max(8, int(s * self.ui_scale))

        self.grid = None
        self.start = None
        self.goal = None
        self.grid_size = 10
        # base cell size scaled for large screens
        self.cell_size = max(20, int(40 * self.ui_scale))
        self.results = {}
        self.solving = False
        self.current_proc = None
        self.current_procs = []  # track multiple procs when comparing
        self.delay_ms = 50  # visualization delay in milliseconds for single runs
        self.drawing_mode = "opstacle"  
        self.current_solution_path = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI widgets"""
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Canvas for drawing
        left_frame = ttk.LabelFrame(main_frame, text="Draw Your Grid (Mouse Drawing)", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Controls
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        self.size_var = tk.StringVar(value="10")
        size_spin = ttk.Spinbox(control_frame, from_=3, to=50, textvariable=self.size_var, width=5, command=self.update_grid_size)
        size_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Mode:").pack(side=tk.LEFT, padx=20)
        self.mode_var = tk.StringVar(value="opstacle"  )
        mode_combo = ttk.Combobox(control_frame, textvariable=self.mode_var, 
                       values=["opstacle"  , "start", "goal", "erase", "cost"], state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # Allow user to manually override default Start/Goal
        self.override_start_goal_var = tk.BooleanVar(value=False)
        override_cb = ttk.Checkbutton(control_frame, text="Manual Start/Goal", variable=self.override_start_goal_var, 
                                      command=self._on_override_toggle)
        override_cb.pack(side=tk.LEFT, padx=10)

        # Visualization delay for single algorithm runs
        ttk.Label(control_frame, text="Delay (ms):").pack(side=tk.LEFT, padx=10)
        self.delay_var = tk.StringVar(value=str(self.delay_ms))
        delay_spin = ttk.Spinbox(control_frame, from_=0, to=2000, textvariable=self.delay_var, width=6, command=self._on_delay_change)
        delay_spin.pack(side=tk.LEFT, padx=5)
        # Cost painting controls
        ttk.Label(control_frame, text="Cost:").pack(side=tk.LEFT, padx=6)
        self.cost_var = tk.StringVar(value="1")
        cost_spin = ttk.Spinbox(control_frame, from_=1, to=999, textvariable=self.cost_var, width=5)
        cost_spin.pack(side=tk.LEFT, padx=2)
        
        tk.Button(control_frame, text="Clear All", command=self.clear_grid, bg="#FF6B6B", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Reset", command=self.reset_grid, bg="#4ECDC4", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Canvas for grid drawing
        self.canvas = tk.Canvas(left_frame, bg="white", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        # Recompute cell size when canvas resizes so grid fills available area
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        info_label = ttk.Label(left_frame, text="opstacl=Black | Start=Green(S) | Goal=Red(G) | Open=White | Exploring=Yellow", 
                       font=("Arial", self.sf(9)), foreground="gray")
        info_label.pack(fill=tk.X, pady=5)
        
        # Right panel - Controls and Results
        right_frame = ttk.LabelFrame(main_frame, text="Algorithms & Results", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        algo_label = ttk.Label(right_frame, text="Select Algorithms:", font=("Arial", self.sf(11), "bold"))
        algo_label.pack(anchor=tk.W, pady=(10, 10))
        
        self.algo_vars = {}
        algorithms = ["A*", "BFS", "DFS", "Greedy", "UCS", "Hill Climbing", "IDA*", "Beem"]
        
        algo_frame = ttk.Frame(right_frame)
        algo_frame.pack(anchor=tk.W, padx=10, fill=tk.X)
        
        for algo in algorithms:
            var = tk.BooleanVar(value=True)
            self.algo_vars[algo] = var
            ttk.Checkbutton(algo_frame, text=algo, variable=var).pack(anchor=tk.W)

        individual_label = ttk.Label(right_frame, text="Run Individual:", font=("Arial", self.sf(11), "bold"))
        individual_label.pack(anchor=tk.W, pady=(15, 10))
        
        # Algorithm buttons
        algo_btn_frame = ttk.Frame(right_frame)
        algo_btn_frame.pack(fill=tk.X, pady=5, padx=10)
        
        for i, algo in enumerate(algorithms):
            btn = tk.Button(algo_btn_frame, text=algo, command=lambda a=algo: self.run_single_algorithm(a), 
                           bg="#048989", fg="white", font=("Arial", self.sf(9), "bold"), width=12)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        algo_btn_frame.columnconfigure(0, weight=1)
        algo_btn_frame.columnconfigure(1, weight=1)

        action_btn_frame = ttk.Frame(right_frame)
        action_btn_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Button(action_btn_frame, text="Solve & Compare All", command=self.solve_and_compare).pack(fill=tk.X, expand=True, pady=2)
        ttk.Button(action_btn_frame, text="Performance Comparison", command=self.show_performance_comparison).pack(fill=tk.X, expand=True, pady=2)
        ttk.Button(action_btn_frame, text="Show Best", command=self.show_best_algorithm).pack(fill=tk.X, expand=True, pady=2)

        # Option: run algorithms in-process (import & call) instead of subprocess
        self.inprocess_var = tk.BooleanVar(value=False)
        inproc_cb = ttk.Checkbutton(action_btn_frame, text="Run In-Process", variable=self.inprocess_var)
        inproc_cb.pack(fill=tk.X, pady=2)

        #tk.Button(right_frame, text="Stop", command=self.stop_solving, bg="#FF0000", fg="white", 
         #   font=("Arial", self.sf(9), "bold"), width=20).pack(pady=5)
        
        results_label = ttk.Label(right_frame, text="Results:", font=("Arial", self.sf(11), "bold"))
        results_label.pack(anchor=tk.W, pady=(15, 10))
        
        scroll = ttk.Scrollbar(right_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(right_frame, height=22, width=35, yscrollcommand=scroll.set, font=("Courier", self.sf(9)))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.results_text.yview)
        
        self.best_algo_label = ttk.Label(right_frame, text="Best: N/A", 
                        font=("Arial", self.sf(10), "bold"), foreground="green")
        self.best_algo_label.pack(anchor=tk.W, pady=10)
        
        # Initialize
        self.update_grid_size()
    
    def update_grid_size(self):
        """Update grid size"""
        try:
            self.grid_size = int(self.size_var.get())
        except:
            self.grid_size = 10
        # cell_size will be computed based on canvas size in draw_grid/_on_canvas_configure
        self.reset_grid()

    def _on_canvas_configure(self, event):
        """Handle canvas resize: recompute cell size so grid fills canvas."""
        try:
            w = int(event.width)
            h = int(event.height)
        except:
            return

        if self.grid_size <= 0:
            return

        # compute the largest integer cell size that fits both dimensions
        new_cell = max(5, min(60, min(w // self.grid_size, h // self.grid_size)))
        if new_cell != self.cell_size:
            self.cell_size = new_cell
            # redraw grid using new cell size
            self.draw_grid()

    def _on_delay_change(self):
        """Handler for changes to the Delay spinbox: validate and store value."""
        try:
            v = int(self.delay_var.get())
        except:
            v = self.delay_ms

        if v < 0:
            v = 0
        if v > 2000:
            v = 2000

        self.delay_ms = v
        # keep the displayed value normalized
        try:
            self.delay_var.set(str(v))
        except:
            pass

    def _on_override_toggle(self):
        """Toggle between auto-set Start/Goal and manual placement."""
        if not self.override_start_goal_var.get():
            # Auto mode: set defaults
            self.start = (0, 0)
            self.goal = (self.grid_size - 1, self.grid_size - 1)
            self.draw_grid()
        # If override is True, allow manual placement (user changes mode to 'start'/'goal')
    
    def reset_grid(self):
        """Reset grid with all cells open. By default, set Start=(0,0) and Goal=(last, last)."""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        # costs: default cost 1 for open cells; None for obstacles
        self.costs = [[1 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        # Auto-set defaults unless user enabled manual override
        if not self.override_start_goal_var.get():
            self.start = (0, 0)
            self.goal = (self.grid_size - 1, self.grid_size - 1)
        else:
            self.start = None
            self.goal = None
        # ensure canvas has an initial size before drawing
        try:
            self.draw_grid()
        except Exception:
            # if draw fails (no canvas size yet) schedule a redraw shortly
            self.root.after(50, self.draw_grid)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Grid ready ({self.grid_size}x{self.grid_size}).\nStart: {self.start}, Goal: {self.goal}\nDraw opstacls, click algorithm to solve.\n")
    
    def clear_grid(self):
        """Clear everything"""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.costs = [[1 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.start = None
        self.goal = None
        self.results = {}
        self.draw_grid()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Cleared.\n")
    
    def draw_grid(self):
        """Draw the grid on canvas"""
        self.canvas.delete("all")

        # Use current canvas pixel size so grid fills available space
        cwidth = self.canvas.winfo_width() or (self.grid_size * self.cell_size)
        cheight = self.canvas.winfo_height() or (self.grid_size * self.cell_size)

        # ensure cell_size fits (should normally be set in _on_canvas_configure)
        self.cell_size = max(5, min(60, min(cwidth // self.grid_size, cheight // self.grid_size)))

        width = self.grid_size * self.cell_size
        height = self.grid_size * self.cell_size

        # center the grid in the canvas if canvas is larger
        x_offset = max(0, (cwidth - width) // 2)
        y_offset = max(0, (cheight - height) // 2)
        # store offsets for click/highlight translation
        self.grid_x_offset = x_offset
        self.grid_y_offset = y_offset

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x0 = x_offset + j * self.cell_size
                y0 = y_offset + i * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size
                
                # Determine color
                if (i, j) == self.start:
                    color = "lightgreen"
                    text = "S"
                elif (i, j) == self.goal:
                    color = "lightcoral"
                    text = "G"
                elif self.grid[i][j] == 1:
                    color = "black"
                    text = ""
                else:
                    # color open cells by cost (default white for cost==1)
                    text = ""
                    try:
                        cost_val = self.costs[i][j]
                    except Exception:
                        cost_val = 1
                    if cost_val is None:
                        color = "white"
                    elif isinstance(cost_val, (int, float)) and cost_val > 1:
                        # prefer explicit mapping for small integers
                        try:
                            color = self._cost_color_for_value(cost_val)
                        except:
                            color = self._cost_to_color(cost_val)
                    else:
                        color = "white"
                
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="gray")

                if text:
                    self.canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2,
                                            text=text, font=("Arial", max(8, self.cell_size//3), "bold"))
                else:
                    # show cost if present and >1
                    try:
                        cost_val = self.costs[i][j]
                        if cost_val is not None and cost_val > 1:
                            txt_color = self._text_color_for_bg(color)
                            self.canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2,
                                                    text=str(cost_val), font=("Arial", max(8, self.cell_size//4)), fill=txt_color)
                    except Exception:
                        pass

        # draw solution path overlay if present (lines + nodes)
        if getattr(self, 'current_solution_path', None):
            try:
                path = list(self.current_solution_path)
                if path:
                    # compute centers
                    centers = []
                    for (pi, pj) in path:
                        cx = x_offset + pj * self.cell_size + self.cell_size/2
                        cy = y_offset + pi * self.cell_size + self.cell_size/2
                        centers.append((cx, cy))
                    # draw connecting line
                    coords = []
                    for cx, cy in centers:
                        coords.extend([cx, cy])
                    if coords:
                        self.canvas.create_line(*coords, fill='purple', width=max(2, self.cell_size//6), smooth=True)
                    # draw nodes
                    for idx, (cx, cy) in enumerate(centers):
                        r = max(3, self.cell_size//6)
                        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill='purple', outline='white')
                    # redraw start/goal labels on top
                    if self.start:
                        si, sj = self.start
                        sx = x_offset + sj * self.cell_size + self.cell_size/2
                        sy = y_offset + si * self.cell_size + self.cell_size/2
                        self.canvas.create_text(sx, sy, text='S', font=("Arial", max(8, self.cell_size//3), "bold"))
                    if self.goal:
                        gi, gj = self.goal
                        gx = x_offset + gj * self.cell_size + self.cell_size/2
                        gy = y_offset + gi * self.cell_size + self.cell_size/2
                        self.canvas.create_text(gx, gy, text='G', font=("Arial", max(8, self.cell_size//3), "bold"))
            except Exception:
                pass
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.draw_at_position(event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        self.draw_at_position(event.x, event.y)
    
    def draw_at_position(self, x, y):
        """Draw at canvas position"""
        # translate canvas coords to grid cell indices, accounting for centering offsets
        x_rel = x - getattr(self, 'grid_x_offset', 0)
        y_rel = y - getattr(self, 'grid_y_offset', 0)
        if x_rel < 0 or y_rel < 0:
            return
        j = x_rel // self.cell_size
        i = y_rel // self.cell_size
        
        if 0 <= i < self.grid_size and 0 <= j < self.grid_size:
            mode = self.mode_var.get()
            
            if mode == "opstacle"  :
                self.grid[i][j] = 1
                try:
                    self.costs[i][j] = None
                except:
                    pass
            elif mode == "cost":
                # set cost for this cell, ensure it's an open cell
                try:
                    v = int(self.cost_var.get())
                except:
                    v = 1
                if self.grid[i][j] == 1:
                    # turn into open
                    self.grid[i][j] = 0
                try:
                    self.costs[i][j] = max(1, v)
                except:
                    pass
            elif mode == "start":
                if self.start != (i, j):
                    self.start = (i, j)
                    self.grid[i][j] = 0
            elif mode == "goal":
                if self.goal != (i, j):
                    self.goal = (i, j)
                    self.grid[i][j] = 0
            elif mode == "erase":
                self.grid[i][j] = 0
                if self.start == (i, j):
                    self.start = None
                if self.goal == (i, j):
                    self.goal = None
            
            self.draw_grid()

    def draw_solution_path(self, path):
        """Set and display the final solution path on the canvas."""
        try:
            self.current_solution_path = path if path else None
        except:
            self.current_solution_path = None
        try:
            self.draw_grid()
        except:
            # schedule if canvas not ready
            try:
                self.root.after(50, self.draw_grid)
            except:
                pass

    def _cost_to_color(self, cost):
        """Map a positive integer cost to a color between lightblue and darkblue.
        cost: int >=1. Values <=1 return white.
        """
        try:
            c = float(cost)
        except:
            return "white"

        if c <= 1:
            return "white"

        # choose cap for gradient scaling
        cap = 20.0
        t = min(c, cap) / cap  # 0..1

        # light and dark RGB tuples
        lr, lg, lb = (224, 247, 255)  # light blue-ish
        dr, dg, db = (0, 119, 204)    # darker blue

        r = int(lr * (1 - t) + dr * t)
        g = int(lg * (1 - t) + dg * t)
        b = int(lb * (1 - t) + db * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _cost_color_for_value(self, cost):
        """Map discrete small integer costs to distinct readable colors.
        Falls back to gradient for larger values.
        """
        try:
            c = int(cost)
        except:
            return self._cost_to_color(cost)

        # explicit mapping for common small costs
        mapping = {
            2: '#add8ff',  # light blue
            3: '#b6f7b6',  # light green
            4: '#fff59d',  # light yellow
            5: '#ffd89b',  # light orange
            6: '#ffb3a7',  # light red
            7: '#d6b3ff',  # light purple
            8: '#cfe8ff',
            9: '#c8f7e6',
            10: '#ffe6f0'
        }
        if c <= 1:
            return 'white'
        if c in mapping:
            return mapping[c]
        return self._cost_to_color(c)

    def _text_color_for_bg(self, bg_hex):
        """Return 'black' or 'white' depending on perceived brightness of bg_hex."""
        try:
            if not bg_hex:
                return 'black'
            h = bg_hex.lstrip('#')
            if len(h) == 3:
                r = int(h[0]*2, 16)
                g = int(h[1]*2, 16)
                b = int(h[2]*2, 16)
            else:
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return 'white' if lum < 140 else 'black'
        except:
            return 'black'
    
    def run_single_algorithm(self, algo_name):
        """Run a single algorithm"""
        if self.grid is None or self.start is None or self.goal is None:
            messagebox.showwarning("Warning", "Please create grid with Start (S) and Goal (G)!")
            return
        # Stop any running algorithms and clear previous highlights/paths
        self.stop_solving()

        # clear any previous solution path
        self.current_solution_path = None

        # start solving
        self.solving = True
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Running {algo_name}...\n\n")
        # clear canvas overlays (redraw base grid)
        self.draw_grid()

        thread = threading.Thread(target=self._solve_single_thread, args=(algo_name,), daemon=True)
        thread.start()
    
    def _solve_single_thread(self, algo_name):
        """Run single algorithm"""
        algo_file = os.path.join(os.path.dirname(__file__), "grid_runner.py")
        grid_str = str(self.grid)
        start_str = str(self.start)
        goal_str = str(self.goal)
        
        timeout = 20.0
        start_time = time.time()
        
        # If user selected Run In-Process, import grid_runner and call the corresponding function
        if self.inprocess_var.get():
            try:
                # load module from file path so we use the user's local copy
                spec = importlib.util.spec_from_file_location("grid_runner", algo_file)
                gr = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gr)

                # map display name to runner function name
                func_map = {
                    'A*': 'run_astar', 'BFS': 'run_bfs', 'DFS': 'run_dfs', 'Greedy': 'run_greedy',
                    'UCS': 'run_ucs', 'Hill Climbing': 'run_hill_climbing', 'IDA*': 'run_ida_star', 'Beem': 'run_beem'
                }

                func_name = func_map.get(algo_name, None)
                if func_name is None or not hasattr(gr, func_name):
                    raise RuntimeError(f"Algorithm {algo_name} not available in grid_runner (in-process)")

                func = getattr(gr, func_name)

                out_lines = []

                # Stdout capture that forwards to original stdout and also invokes a callback per-line
                orig_stdout = sys.__stdout__
                class StdoutCapture:
                    def __init__(self, line_callback, orig):
                        self._buf = ""
                        self._cb = line_callback
                        self._orig = orig
                    def write(self, s):
                        # accumulate
                        self._buf += s
                        while "\n" in self._buf:
                            line, self._buf = self._buf.split("\n", 1)
                            line = line + "\n"
                            try:
                                self._cb(line)
                            except:
                                pass
                            try:
                                self._orig.write(line)
                            except:
                                pass
                    def flush(self):
                        try:
                            if self._buf:
                                line = self._buf
                                self._buf = ""
                                try:
                                    self._cb(line)
                                except:
                                    pass
                                try:
                                    self._orig.write(line)
                                except:
                                    pass
                            self._orig.flush()
                        except:
                            pass

                def on_line(line):
                    out_lines.append(line)
                    if line.startswith("STATE:"):
                        try:
                            state_str = line[6:].strip()
                            state_data = ast.literal_eval(state_str)
                            if isinstance(state_data, (tuple, list)) and len(state_data) == 2:
                                self.root.after(0, self.highlight_cell, tuple(state_data))
                                # pacing for single runs
                                # Use the thread-safe stored delay value instead of
                                # reading the Tk StringVar from a worker thread.
                                d = getattr(self, 'delay_ms', 0)
                                if d > 0:
                                    time.sleep(d/1000.0)
                        except:
                            pass

                sys.stdout = StdoutCapture(on_line, orig_stdout)
                # start memory tracing in-process
                tracemalloc.start()

                # call algorithm (best-effort timeout: we run directly and measure elapsed)
                t0 = time.time()
                try:
                    # pass the current cost grid to the in-process algorithm
                    cost_grid_copy = [row[:] for row in getattr(self, 'costs', [[1]*len(self.grid[0]) for _ in range(len(self.grid))])]
                    path_nodes = func(self.grid, cost_grid_copy, self.start, self.goal)
                    # func returns (path, nodes) in most implementations
                    if isinstance(path_nodes, tuple) and len(path_nodes) == 2:
                        path, nodes = path_nodes
                    else:
                        path, nodes = None, 0
                finally:
                    # stop tracing and restore stdout
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    try:
                        sys.stdout.flush()
                    except:
                        pass
                    sys.stdout = orig_stdout

                out = ''.join(out_lines)

                # parse metrics
                nodes_val = nodes or 0
                path_len = len(path) if path else -1
                memory_mb = peak / (1024 * 1024)

                solved = path_len >= 0
                final_time = time.time() - start_time

                result_text = f"{algo_name}:\n"
                result_text += f"Nodes: {nodes_val}\n"
                if path_len >= 0:
                    result_text += f"Path: {path_len}\n"
                result_text += f"Time: {final_time:.3f}s\n"
                result_text += f"Memory: {memory_mb * 1024:.2f} KB\n"
                result_text += f"Status: {'✓ SOLVED' if solved else '✗ NOT SOLVED'}\n"
                result_text += f"\n[DEBUG] Raw Output:\n{out[:500]}..."

                # store solution path so draw_grid can render it
                try:
                    self.current_solution_path = path if path else None
                except:
                    self.current_solution_path = None

                def update_results():
                    self.results_text.delete(1.0, tk.END)
                    self.results_text.insert(tk.END, result_text)
                    self.solving = False
                    self.draw_grid()

                self.root.after(0, update_results)

                print(f"[{algo_name}] path_len={path_len}, nodes={nodes_val}, solved={solved}")
                print(f"[{algo_name}] Raw output (first 500 chars):\n{out[:500]}")

            except Exception as e:
                # restore stdout in case of errors
                try:
                    sys.stdout = orig_stdout
                except:
                    pass
                self.results_text.insert(tk.END, f"Error (in-process): {e}\n")
                self.solving = False
            return

        # fallback: existing subprocess-based approach
        try:
            # include optional cost grid string so runner can use non-uniform costs
            cost_str = str(getattr(self, 'costs', [[1 for _ in range(self.grid_size)] for _ in range(self.grid_size)]))
            proc = subprocess.Popen(
                [sys.executable, '-u', algo_file, algo_name, grid_str, start_str, goal_str, cost_str],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(algo_file)
            )
            self.current_proc = proc
            # track multiple procs so Stop can terminate them
            self.current_procs.append(proc)
            
            out_lines = []
            def reader():
                try:
                    for line in proc.stdout:
                        out_lines.append(line)
                        # Highlight cells during exploration (paced by user delay)
                        if line.startswith("STATE:"):
                            try:
                                state_str = line[6:].strip()
                                state_data = ast.literal_eval(state_str)
                                if isinstance(state_data, (tuple, list)) and len(state_data) == 2:
                                    # schedule highlight on main thread
                                    self.root.after(0, self.highlight_cell, tuple(state_data))
                                    # apply user-chosen delay to pacing (only for individual runs)
                                    # Use the thread-safe stored delay value instead of
                                    # reading the Tk StringVar from a worker thread.
                                    d = getattr(self, 'delay_ms', 0)
                                    if d > 0:
                                        time.sleep(d/1000.0)
                            except:
                                pass
                except:
                    pass
            
            reader_thread = threading.Thread(target=reader, daemon=True)
            reader_thread.start()
            
            while proc.poll() is None:
                if time.time() - start_time > timeout:
                    proc.terminate()
                    break
                time.sleep(0.05)
            
            # allow reader slightly more time to flush final output
            reader_thread.join(timeout=2)
            out = ''.join(out_lines)
            
            nodes = 0
            path_len = -1
            memory_mb = 0.0
            solved = False
            try:
                import re
                parsed_path = None
                for line in out.splitlines():
                    # capture PATH: line (original-case or lower)
                    if line.startswith('PATH:') or line.startswith('Path:') or line.lower().startswith('path:'):
                        try:
                            raw = line.split(':', 1)[1].strip()
                            if raw:
                                parsed_path = ast.literal_eval(raw)
                        except:
                            try:
                                parsed_path = eval(line.split(':',1)[1].strip())
                            except:
                                parsed_path = None
                        continue
                    l = line.lower()
                    if 'nodes' in l:
                        m = re.search(r"(\d+)", l)
                        if m:
                            nodes = int(m.group(1))
                    if 'path length' in l:
                        m = re.search(r"(\d+)", l)
                        if m:
                            path_len = int(m.group(1))
                    if 'memory used' in l:
                        m = re.search(r"(\d+\.?\d*)", l)
                        if m:
                            try:
                                memory_mb = float(m.group(1))
                            except:
                                pass
                # if we found a parsed_path, store it for drawing
                if parsed_path is not None:
                    try:
                        # normalize to list of tuples
                        self.current_solution_path = [tuple(p) for p in parsed_path]
                    except:
                        self.current_solution_path = parsed_path
            except:
                pass
            
            if 'timeout' in out.lower() or 'no path' in out.lower() or 'unsolved' in out.lower():
                solved = False
            elif path_len >= 0:
                solved = True
            
            final_time = time.time() - start_time
            result_text = f"{algo_name}:\n"
            result_text += f"Nodes: {nodes}\n"
            if path_len >= 0:
                result_text += f"Path: {path_len}\n"
            result_text += f"Time: {final_time:.3f}s\n"
            result_text += f"Memory: {memory_mb * 1024:.2f} KB\n"
            result_text += f"Status: {'✓ SOLVED' if solved else '✗ NOT SOLVED'}\n"
            # Debug: show raw output for troubleshooting
            result_text += f"\n[DEBUG] Raw Output:\n{out[:500]}..."
            
            def update_results():
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, result_text)
                self.solving = False
                self.draw_grid()
                # done with this proc
                try:
                    self.current_procs.remove(proc)
                except:
                    pass
            self.root.after(0, update_results)
            
            # Print to console for debugging
            print(f"[{algo_name}] path_len={path_len}, nodes={nodes}, solved={solved}")
            print(f"[{algo_name}] Raw output (first 500 chars):\n{out[:500]}")
            
        except Exception as e:
            self.results_text.insert(tk.END, f"Error: {e}\n")
            self.solving = False
    
    def highlight_cell(self, cell):
        """Highlight exploring cell"""
        if not cell or len(cell) != 2:
            return
        
        i, j = cell
        if 0 <= i < self.grid_size and 0 <= j < self.grid_size:
            if (i, j) != self.start and (i, j) != self.goal and self.grid[i][j] != 1:
                # account for grid offset when drawing highlights
                x0 = getattr(self, 'grid_x_offset', 0) + j * self.cell_size
                y0 = getattr(self, 'grid_y_offset', 0) + i * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size
                
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="lightyellow", outline="gray")
                self.canvas.create_oval(x0+8, y0+8, x1-8, y1-8, fill="orange", outline="orange")
            
            # avoid calling root.update() here to prevent nested event recursion
            # the scheduled drawing via `after` will be processed by the mainloop
            pass
    
    def solve_and_compare(self):
        """Compare all selected algorithms"""
        if self.grid is None or self.start is None or self.goal is None:
            messagebox.showwarning("Warning", "Please create grid with Start (S) and Goal (G)!")
            return
        
        selected_algos = [algo for algo, var in self.algo_vars.items() if var.get()]
        if not selected_algos:
            messagebox.showwarning("Warning", "Select at least one algorithm!")
            return
        
        # Clear previous results and highlights
        self.results = {}
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Comparing algorithms...\n\n")
        self.draw_grid()  # clear previous highlights
        self.solving = True

        thread = threading.Thread(target=self._solve_thread, args=(selected_algos,))
        thread.daemon = True
        thread.start()
    
    def _solve_thread(self, selected_algos):
        """Compare algorithms"""
        self.results = {}
        algo_file = os.path.join(os.path.dirname(__file__), "grid_runner.py")
        grid_str = str(self.grid)
        start_str = str(self.start)
        goal_str = str(self.goal)
        # Optionally run in-process: load grid_runner once
        inproc_module = None
        func_map = {
            'A*': 'run_astar', 'BFS': 'run_bfs', 'DFS': 'run_dfs', 'Greedy': 'run_greedy',
            'UCS': 'run_ucs', 'Hill Climbing': 'run_hill_climbing', 'IDA*': 'run_ida_star', 'Beem': 'run_beem'
        }
        if self.inprocess_var.get():
            try:
                spec = importlib.util.spec_from_file_location("grid_runner", algo_file)
                inproc_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(inproc_module)
            except Exception as e:
                inproc_module = None
                # fall back to subprocess if import fails
                self.results_text.insert(tk.END, f"In-process load failed: {e}\nFalling back to subprocess mode.\n")

        # Run each algorithm sequentially but show STATE highlights in real time (no artificial delay)
        for algo_name in selected_algos:
            if not self.solving:
                break

            try:
                if inproc_module is not None and func_map.get(algo_name):
                    # In-process execution: capture stdout and run function
                    out_lines = []
                    orig_stdout = sys.__stdout__

                    class StdoutCapture:
                        def __init__(self, cb, orig):
                            self._buf = ""
                            self._cb = cb
                            self._orig = orig
                        def write(self, s):
                            self._buf += s
                            while "\n" in self._buf:
                                line, self._buf = self._buf.split("\n", 1)
                                line = line + "\n"
                                try:
                                    self._cb(line)
                                except:
                                    pass
                                try:
                                    self._orig.write(line)
                                except:
                                    pass
                        def flush(self):
                            try:
                                if self._buf:
                                    line = self._buf
                                    self._buf = ""
                                    try:
                                        self._cb(line)
                                    except:
                                        pass
                                    try:
                                        self._orig.write(line)
                                    except:
                                        pass
                                self._orig.flush()
                            except:
                                pass

                    def on_line(line):
                        out_lines.append(line)
                        if line.startswith("STATE:"):
                            try:
                                state_str = line[6:].strip()
                                state_data = ast.literal_eval(state_str)
                                if isinstance(state_data, (tuple, list)) and len(state_data) == 2:
                                    self.root.after(0, self.highlight_cell, tuple(state_data))
                            except:
                                pass

                    sys.stdout = StdoutCapture(on_line, orig_stdout)
                    tracemalloc.start()
                    t0 = time.time()
                    func = getattr(inproc_module, func_map[algo_name])
                    try:
                        cost_grid_copy = [row[:] for row in getattr(self, 'costs', [[1]*len(self.grid[0]) for _ in range(len(self.grid))])]
                        path_nodes = func(self.grid, cost_grid_copy, self.start, self.goal)
                        if isinstance(path_nodes, tuple) and len(path_nodes) == 2:
                            path, nodes = path_nodes
                        else:
                            path, nodes = None, 0
                    finally:
                        current, peak = tracemalloc.get_traced_memory()
                        tracemalloc.stop()
                        try:
                            sys.stdout.flush()
                        except:
                            pass
                        sys.stdout = orig_stdout

                    out = ''.join(out_lines)
                    nodes_val = nodes or 0
                    path_len = len(path) if path else -1
                    memory_mb = peak / (1024 * 1024)
                    result_time = time.time() - t0
                    solved = path_len >= 0
                    self.results[algo_name] = {"nodes": nodes_val, "path_length": path_len, "time": result_time, "memory": memory_mb, "solved": solved}
                else:
                    cost_str = str(getattr(self, 'costs', [[1 for _ in range(self.grid_size)] for _ in range(self.grid_size)]))
                    proc = subprocess.Popen(
                        [sys.executable, '-u', algo_file, algo_name, grid_str, start_str, goal_str, cost_str],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        cwd=os.path.dirname(algo_file)
                    )

                    # track proc
                    self.current_procs.append(proc)

                    out_lines = []
                    def reader():
                        try:
                            for line in proc.stdout:
                                out_lines.append(line)
                                # Highlight in real time (no delay)
                                if line.startswith("STATE:"):
                                    try:
                                        state_str = line[6:].strip()
                                        state_data = ast.literal_eval(state_str)
                                        if isinstance(state_data, (tuple, list)) and len(state_data) == 2:
                                            self.root.after(0, self.highlight_cell, tuple(state_data))
                                    except:
                                        pass
                        except:
                            pass

                    reader_thread = threading.Thread(target=reader, daemon=True)
                    reader_thread.start()

                    timeout = 20.0
                    start_time = time.time()

                    while True:
                        if proc.poll() is not None:
                            break
                        if time.time() - start_time > timeout:
                            try:
                                proc.kill()
                            except:
                                pass
                            self.results[algo_name] = {"nodes": 0, "path_length": -1, "time": timeout, "solved": False}
                            break
                        time.sleep(0.02)

                    reader_thread.join(timeout=1)
                    out = ''.join(out_lines)

                    # parse results
                    nodes = 0
                    path_len = -1
                    memory_mb = 0.0
                    solved = False
                    try:
                        for line in out.splitlines():
                            l = line.lower()
                            if 'nodes' in l:
                                import re
                                m = re.search(r"(\d+)", l)
                                if m:
                                    nodes = int(m.group(1))
                            if 'path length' in l:
                                import re
                                m = re.search(r"(\d+)", l)
                                if m:
                                    path_len = int(m.group(1))
                            if 'memory used' in l:
                                import re
                                m = re.search(r"(\d+\.\d+)", l)
                                if m:
                                    memory_mb = float(m.group(1))
                    except:
                        pass

                    if 'timeout' not in out.lower() and path_len >= 0:
                        solved = True

                    result_time = time.time() - start_time
                    self.results[algo_name] = {"nodes": nodes, "path_length": path_len, "time": result_time, "memory": memory_mb, "solved": solved}

                # update partial results UI for the algorithm that just finished
                def partial_update(name=algo_name, r=self.results[algo_name]):
                    self.results_text.insert(tk.END, f"{name}: ")
                    if r.get('solved'):
                        self.results_text.insert(tk.END, f"  ✓ Nodes: {r['nodes']} Path: {r['path_length']} Time: {r['time']:.3f}s Memory: {r.get('memory', 0) * 1024:.2f} KB\n")
                    else:
                        self.results_text.insert(tk.END, f"  ✗ Not Solved\n")
                    self.results_text.see(tk.END)
                    # clear highlights after this algorithm so next starts clean
                    self.draw_grid()

                self.root.after(0, partial_update)

                # done with this proc if subprocess path took it
                try:
                    if 'proc' in locals():
                        self.current_procs.remove(proc)
                except:
                    pass

            except Exception as e:
                self.results[algo_name] = {"nodes": 0, "path_length": -1, "time": 0, "solved": False, "error": str(e)}

        # final grooming of results
        self.root.after(0, self._update_results)
    
    def _update_results(self):
        """Display results"""
        self.results_text.delete(1.0, tk.END)
        
        solved_list = []
        for algo_name, r in self.results.items():
            if r.get('solved'):
                solved_list.append({
                    'name': algo_name,
                    'nodes': float(r.get('nodes', 0) or 0),
                    'time': float(r.get('time')) if r.get('time') else 0,
                    'path': int(r.get('path_length')) if r.get('path_length', -1) >= 0 else None,
                })
        
        for algo_name, result in self.results.items():
            self.results_text.insert(tk.END, f"{algo_name}:\n")
            if result["solved"]:
                self.results_text.insert(tk.END, f"  ✓ Nodes: {result['nodes']} Path: {result['path_length']} Time: {result['time']:.3f}s\n\n")
            else:
                self.results_text.insert(tk.END, f"  ✗ Not Solved\n\n")
        
        if solved_list:
            best = min(solved_list, key=lambda x: x['nodes'])
            self.best_algo_label.config(text=f"Best: {best['name']} ({int(best['nodes'])} nodes)")
            self.results_text.insert(tk.END, f"\nBest: {best['name']}")
        else:
            self.best_algo_label.config(text="Best: None solved")

        self.solving = False
        self.draw_grid()

    def show_performance_comparison(self):
        """Show detailed performance comparison using Tkinter (no matplotlib)."""
        if not self.results:
            messagebox.showwarning("Warning", "No results yet. Run 'Solve & Compare All' first!")
            return

        # Prepare sorted results
        items = sorted(self.results.items())
        names = [n for n, r in items]
        nodes = [r.get('nodes', 0) for _, r in items]
        times = [r.get('time', 0) for _, r in items]
        paths = [r.get('path_length', -1) for _, r in items]
        # convert stored memory (MB) to KB for display
        mems = [r.get('memory', 0) * 1024 for _, r in items]

        # Create popup window (larger)
        win = tk.Toplevel(self.root)
        win.title("Performance Comparison")
        try:
            win.geometry("1400x600")
        except:
            pass

        info = tk.Text(win, height=10, width=100, font=("Courier", self.sf(12)))
        info.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)
        info.insert(tk.END, "Algorithm\tNodes\tTime(s)\tPath\tMemory(KB)\n")
        info.insert(tk.END, "-------------------------------------------------------------\n")
        for name, r in items:
            info.insert(tk.END, f"{name}\t{r.get('nodes',0)}\t{r.get('time',0):.3f}\t{r.get('path_length',-1)}\t{r.get('memory',0) * 1024:.2f}\n")
        info.config(state=tk.DISABLED)

        # Canvas chart: each algorithm gets one row with four metric bars (Nodes, Time, Path, Memory)
        canvas = tk.Canvas(win, height=max(300, 40 * max(1, len(names))), width=1100, bg='white')
        canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # layout (larger for readability)
        cwidth = 1040
        name_col = 240
        gap = 10
        metrics = ['Nodes', 'Time(s)', 'Path', 'Memory(KB)']
        metric_colors = ['steelblue', 'coral', 'lightgreen', 'khaki']
        metric_values = [nodes, times, [p if p >= 0 else 0 for p in paths], mems]

        rows = len(names)
        row_h = 36
        padding_top = 14

        # compute max per metric for scaling
        max_vals = [max(vals) if vals and max(vals) > 0 else 1 for vals in metric_values]

        # compute bar area width for each metric column
        bar_area = cwidth - name_col - (len(metrics)-1)*gap
        metric_width = bar_area // len(metrics)

        # header
        canvas.create_text(12, padding_top, anchor='w', text='Algorithm', font=("Arial", self.sf(12), 'bold'))
        for mi, m in enumerate(metrics):
            x = name_col + mi*(metric_width+gap) + metric_width//2
            canvas.create_text(x, padding_top, text=m, font=("Arial", self.sf(12), 'bold'))

        # draw rows
        for i, name in enumerate(names):
            y = padding_top + 22 + i*row_h
            # algorithm name
            canvas.create_text(12, y, anchor='w', text=name, font=("Arial", self.sf(12)))
            # draw metric bars
            for mi, vals in enumerate(metric_values):
                v = vals[i]
                maxv = max_vals[mi]
                x0 = name_col + mi*(metric_width+gap)
                y0 = y - (row_h//3)
                full_w = metric_width - 6
                w = int((v / maxv) * full_w) if maxv > 0 else 0
                # background box
                canvas.create_rectangle(x0, y0, x0+full_w, y0+ (row_h//1.5), fill='#f0f0f0', outline='#cccccc')
                if w > 0:
                    canvas.create_rectangle(x0+2, y0+2, x0+2+w, y0 + (row_h//1.5) -2, fill=metric_colors[mi], outline='black')
                # value label
                val_text = f"{v:.2f}" if isinstance(v, float) else str(v)
                if mi == 3:
                    # memory show KB with 2 decimals
                    val_text = f"{v:.2f} KB"
                canvas.create_text(x0 + full_w + 10, y, anchor='w', text=val_text, font=("Arial", self.sf(11)))

        win.transient(self.root)
        win.grab_set()
        win.focus_set()

    def show_best_algorithm(self):
        """Show the best solved algorithm based on nodes expanded."""
        if not self.results:
            messagebox.showwarning("Warning", "No results yet. Run 'Solve & Compare All' first!")
            return

        solved = [ (name, r) for name, r in self.results.items() if r.get('solved') ]
        if not solved:
            messagebox.showinfo("Best Algorithm", "No algorithm solved the problem.")
            return

        best = min(solved, key=lambda x: x[1].get('nodes', float('inf')))
        name, r = best
        msg = f"Best: {name}\nNodes: {r.get('nodes',0)}\nPath Length: {r.get('path_length',-1)}\nTime: {r.get('time',0):.3f}s\nMemory: {r.get('memory',0) * 1024:.2f} KB"
        # show in results_text and popup
        self.results_text.insert(tk.END, "\n" + msg + "\n")
        messagebox.showinfo("Best Algorithm", msg)

    def stop_solving(self):
        """Stop solving"""
        self.solving = False
        # kill all tracked processes
        for p in list(self.current_procs):
            try:
                p.kill()
            except:
                pass
        self.current_procs = []

def main():
    root = tk.Tk()
    app = GridDrawerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import ttk, messagebox
import time
import tempfile
import uuid
import random
import threading
import sys
import subprocess
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False

# ================================
#   15-PUZZLE UTILITIES
# ================================

def count_inversions(tiles):
    """Count inversions in puzzle to check solvability"""
    inv_count = 0
    nums = [t for t in tiles if t != 0]
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] > nums[j]:
                inv_count += 1
    return inv_count

def is_solvable(tiles):
    """Check if 15-puzzle is solvable"""
    inversions = count_inversions(tiles)
    blank_index = tiles.index(0)
    blank_row = blank_index // 4  # 0-indexed row
    row_from_bottom = 4 - blank_row  # 1-indexed from bottom (1=bottom, 4=top)
    
    # Correct solvability rule for 15-puzzle:
    # If blank is on even row from bottom: inversions must be ODD
    # If blank is on odd row from bottom: inversions must be EVEN
    if row_from_bottom % 2 == 0:  # Even row from bottom
        return inversions % 2 == 1
    else:  # Odd row from bottom
        return inversions % 2 == 0

def generate_solvable_puzzle():
    """Generate a solvable 15-puzzle"""
    while True:
        tiles = list(range(16))
        random.shuffle(tiles)
        if is_solvable(tiles):
            return tiles

def goal_test(state):
    """Check if puzzle is solved"""
    return state == list(range(1, 16)) + [0]

def get_neighbors(state):
    """Get valid neighbors for state"""
    neighbors = []
    blank = state.index(0)
    r, c = divmod(blank, 4)
    moves = [(1,0),(-1,0),(0,1),(0,-1)]
    
    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            new_state = state[:]
            new_state[blank], new_state[nr*4 + nc] = new_state[nr*4 + nc], new_state[blank]
            neighbors.append((new_state, 1))
    return neighbors

def heuristic_manhattan(state):
    """Manhattan distance heuristic"""
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        r, c = divmod(index, 4)
        gr, gc = divmod(tile - 1, 4)
        distance += abs(r - gr) + abs(c - gc)
    return distance

# ================================
#   MAIN GUI APPLICATION
# ================================

class PuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("15-Puzzle Solver with AI Algorithms")
        self.root.geometry("1400x900")
        
        self.current_puzzle = None
        self.generated_puzzle = None
        self.stop_event = threading.Event()
        self.results = {}
        self.solving = False
        self.current_proc = None
        self.proc_paused = False
        self.proc_lock = threading.Lock()
        
        # Create main frames
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Puzzle display
        left_frame = ttk.LabelFrame(main_frame, text="15-Puzzle Board", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.puzzle_frame = ttk.Frame(left_frame)
        self.puzzle_frame.pack(pady=20)
        
        self.puzzle_buttons = []
        for i in range(16):
            btn = tk.Button(self.puzzle_frame, width=6, height=3, font=("Arial", 14, "bold"),
                        command=lambda idx=i: self.on_tile_click(idx))
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
            self.puzzle_buttons.append(btn)
        
        # Right panel - Controls
        right_frame = ttk.LabelFrame(main_frame, text="Controls & Results", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Generate puzzle button
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="Generate Puzzle", 
            command=self.generate_puzzle, bg="#224522", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        
        # Algorithm selection
        algo_label = ttk.Label(right_frame, text="Select Algorithms for Compare:", font=("Arial", 11, "bold"))
        algo_label.pack(anchor=tk.W, pady=(20, 10))
        
        self.algo_vars = {}
        algorithms = ["A*", "BFS", "DFS", "Greedy", "UCS", "Hill Climbing", "IDA*", "Beem"]
        
        for algo in algorithms:
            var = tk.BooleanVar(value=True)
            self.algo_vars[algo] = var
            ttk.Checkbutton(right_frame, text=algo, variable=var).pack(anchor=tk.W, padx=20)

        individual_label = ttk.Label(right_frame, text="Run Individual Algorithm:", font=("Arial", 11, "bold"))
        individual_label.pack(anchor=tk.W, pady=(15, 10))
        
        # Create a frame for algorithm buttons
        algo_btn_frame = ttk.Frame(right_frame)
        algo_btn_frame.pack(fill=tk.X, pady=5)
        
        for algo in algorithms:
            btn = tk.Button(algo_btn_frame, text=algo, command=lambda a=algo: self.run_single_algorithm(a), 
                           bg="#048989", fg="white", font=("Arial", 9, "bold"), width=10)
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        # Place Solve & Graph buttons side-by-side for visibility
        action_btn_frame = ttk.Frame(right_frame)
        action_btn_frame.pack(fill=tk.X, pady=5)
        solve_btn = ttk.Button(action_btn_frame, text="Solve & Compare Selected",
                            command=self.solve_and_compare)
        solve_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(action_btn_frame, text="Show Performance Graph",
                 command=self.show_graph).pack(side=tk.LEFT)

        # Stop / Continue / Restart buttons
        control_btn_frame = ttk.Frame(right_frame)
        control_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(control_btn_frame, text="Stop", command=self.stop_solving, bg="#FF0000", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        tk.Button(control_btn_frame, text="Continue", command=self.continue_solving, bg="#085403", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        #ttk.Button(control_btn_frame, text="Restart", command=self.restart_puzzle).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Results display
        results_label = ttk.Label(right_frame, text="Results:", font=("Arial", 11, "bold"))
        results_label.pack(anchor=tk.W, pady=(20, 10))
        
        # Results text area
        scroll = ttk.Scrollbar(right_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(right_frame, height=30, width=40, yscrollcommand=scroll.set)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.results_text.yview)
        
        # Trace text area (shows solution steps)
        trace_label = ttk.Label(right_frame, text="Trace (solution steps):", font=("Arial", 11, "bold"))
        trace_label.pack(anchor=tk.W, pady=(10, 0))
        self.trace_text = tk.Text(right_frame, height=8, width=40)
        self.trace_text.pack(fill=tk.BOTH, expand=False, pady=(0,10))
        
        # Graph button
        ttk.Button(right_frame, text="Show Performance Graph", 
                command=self.show_graph).pack(fill=tk.X, pady=5)
        
        # Best algorithm label
        self.best_algo_label = ttk.Label(right_frame, text="Best Algorithm: N/A", 
                                        font=("Arial", 10, "bold"), foreground="green")
        self.best_algo_label.pack(anchor=tk.W, pady=10)
        # Button to explicitly show best algorithm
        ttk.Button(right_frame, text="Show Best Algorithm", command=self.show_best_algorithm).pack(fill=tk.X, pady=5)

    def append_log(self, text):
        """No-op - logging disabled"""
        pass
        
    def generate_puzzle(self):
        """Generate a new solvable puzzle"""
        puzzle = generate_solvable_puzzle()
        self.generated_puzzle = list(puzzle)
        self.current_puzzle = list(puzzle)
        self.display_puzzle(self.current_puzzle)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Puzzle generated! Click 'Solve & Compare' to start.\n")
        messagebox.showinfo("Success", "New puzzle generated!")
        
    def display_puzzle(self, puzzle):
        """Display puzzle on buttons"""
        for i, val in enumerate(puzzle):
            btn = self.puzzle_buttons[i]
            if val == 0:
                btn.config(text="", bg="lightgray", fg="black")
            else:
                btn.config(text=str(val), bg="lightblue", fg="black")

    def run_single_algorithm(self, algo_name):
        """Run a single algorithm and display its tries"""
        if self.current_puzzle is None:
            messagebox.showwarning("Warning", "Please generate a puzzle first!")
            return
        
        self.solving = True
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Running {algo_name}...\n")
        
        thread = threading.Thread(target=self._solve_single_thread, args=(algo_name,), daemon=True)
        thread.start()
    
    def _solve_single_thread(self, algo_name):
        """Thread function to run a single algorithm"""
        algo_map = {
            "A*": "Astar.py",
            "BFS": "BFS.py",
            "DFS": "DFS.py",
            "Greedy": "Greedy.py",
            "UCS": "UCS.py",
            "Hill Climbing": "Hillclimping.py",
            "IDA*": "IDAstar.py",
            "Beem": "Beem.py"
        }
        
        algo_file = algo_map.get(algo_name)
        if not algo_file:
            return
        
        algo_path = os.path.join(os.path.dirname(__file__), algo_file)
        puzzle_str = ",".join(str(x) for x in self.current_puzzle)
        
        timeout = 8
        start_time = time.time()
        active_time = 0
        
        try:
            # Create per-process pause and stop file paths
            pause_path = os.path.join(tempfile.gettempdir(), f"p15_pause_{uuid.uuid4().hex}.pause")
            stop_path = os.path.join(tempfile.gettempdir(), f"p15_stop_{uuid.uuid4().hex}.stop")
            env = os.environ.copy()
            env['PAUSE_FILE'] = pause_path
            env['STOP_FILE'] = stop_path

            # Use unbuffered Python so STATE markers stream immediately
            proc = subprocess.Popen(
                [sys.executable, '-u', algo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(algo_path),
                env=env
            )
            # remember pause and stop file paths so Stop can create them
            self.current_proc_pause = pause_path
            self.current_proc_stop = stop_path
            # Send the puzzle to the algorithm via stdin
            proc.stdin.write(puzzle_str + "\n")
            proc.stdin.flush()
            self.current_proc = proc
            
            out_lines = []
            def reader():
                try:
                    for line in proc.stdout:
                        out_lines.append(line)
                        # Parse STATE markers and display puzzle live
                        if line.startswith("STATE:"):
                            try:
                                state_str = line[6:].strip()  # Remove "STATE:" prefix
                                state_data = eval(state_str)  # Convert string to list or tuple
                                # Accept both list and tuple formats, convert to list
                                if isinstance(state_data, (list, tuple)) and len(state_data) == 16:
                                    state_list = list(state_data) if isinstance(state_data, tuple) else state_data
                                    # Use default argument to capture the value correctly
                                    self.root.after(0, self.display_puzzle, state_list)
                            except Exception:
                                pass
                except Exception:
                    pass
            
            reader_thread = threading.Thread(target=reader, daemon=True)
            reader_thread.start()
            
            while proc.poll() is None:
                active_time = time.time() - start_time
                if active_time > timeout:
                    proc.terminate()
                    break
                time.sleep(0.05)
            
            reader_thread.join(timeout=1)
            out = ''.join(out_lines)
            
            nodes = 0
            path_len = -1
            solved = False
            try:
                for line in out.splitlines():
                    l = line.lower()
                    if 'nodes' in l:
                        import re
                        m = re.search(r"(\d+)", l)
                        if m:
                            nodes = int(m.group(1))
                    if 'path length' in l or 'pathlength' in l or 'path len' in l:
                        import re
                        m = re.search(r"(\d+)", l)
                        if m:
                            path_len = int(m.group(1))
                    if ('solved' in l and ('yes' in l or 'true' in l or '✓' in l)) or ('puzzle solved' in l):
                        solved = True
            except Exception:
                pass
            # Check for explicit unsolved status (Hill Climbing local maximum or timeout)
            if 'unsolved' in out.lower() or 'local' in out.lower() or 'timeout' in out.lower():
                solved = False
            # If a path length was reported and not explicitly unsolved, consider it solved
            elif path_len >= 0:
                solved = True
            
            final_time = time.time() - start_time
            result_text = f"\n{algo_name} Result:\n"
            result_text += f"Nodes Expanded: {nodes}\n"
            if path_len >= 0:
                result_text += f"Path Length: {path_len}\n"
            result_text += f"Time: {final_time:.4f}s\n"
            
            if solved:
                result_text += "Status: ✓ SOLVED\n"
            else:
                result_text += "Status: ✗ Not Solved\n"
            
            def update_results():
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, result_text)
                
                # Extract and display trace (STATE lines showing solution path)
                self.trace_text.delete(1.0, tk.END)
                trace_lines = []
                for line in out.splitlines():
                    if line.startswith("STATE:"):
                        try:
                            state_str = line[6:].strip()
                            state_data = eval(state_str)
                            if isinstance(state_data, (list, tuple)):
                                trace_lines.append(list(state_data))
                        except:
                            pass
                
                if trace_lines:
                    total_moves = len(trace_lines) - 1  # Subtract 1 for starting position
                    self.trace_text.insert(tk.END, f"Solution Path - Total Moves: {total_moves}\n")
                    self.trace_text.insert(tk.END, f"Steps: {len(trace_lines)}\n")
                    self.trace_text.insert(tk.END, "=" * 50 + "\n\n")
                    
                    for i, step in enumerate(trace_lines[:25]):  # Show first 25 steps
                        # Display as 4x4 grid
                        self.trace_text.insert(tk.END, f"Step {i}: \n")
                        for row in range(4):
                            for col in range(4):
                                idx = row * 4 + col
                                val = step[idx]
                                if val == 0:
                                    self.trace_text.insert(tk.END, "  . ")
                                else:
                                    self.trace_text.insert(tk.END, f"{val:3d} ")
                            self.trace_text.insert(tk.END, "\n")
                        self.trace_text.insert(tk.END, "\n")
                    
                    if len(trace_lines) > 25:
                        self.trace_text.insert(tk.END, f"... ({len(trace_lines) - 25} more steps not shown)")
                else:
                    self.trace_text.insert(tk.END, "No solution trace available")
                
                self.solving = False
            
            self.root.after(0, update_results)
            
        except Exception as e:
            self.results_text.insert(tk.END, f"Error: {e}\n")
            self.solving = False

    def on_tile_click(self, idx):
        """Handle manual tile clicks to move tiles into the blank if adjacent."""
        if self.current_puzzle is None:
            return
        try:
            blank = self.current_puzzle.index(0)
        except ValueError:
            return

        # compute row/col
        r1, c1 = divmod(blank, 4)
        r2, c2 = divmod(idx, 4)
        # only allow move if adjacent (Manhattan distance == 1)
        if abs(r1 - r2) + abs(c1 - c2) == 1:
            # swap
            self.current_puzzle[blank], self.current_puzzle[idx] = self.current_puzzle[idx], self.current_puzzle[blank]
            self.display_puzzle(self.current_puzzle)
            # clear previous results because puzzle changed
            self.results_text.delete(1.0, tk.END)
            self.trace_text.delete(1.0, tk.END)
            self.best_algo_label.config(text="Best Algorithm: N/A")
    
    def solve_and_compare(self):
        """Solve puzzle with selected algorithms"""
        if self.current_puzzle is None:
            messagebox.showwarning("Warning", "Please generate a puzzle first!")
            return
        
        selected_algos = [algo for algo, var in self.algo_vars.items() if var.get()]
        if not selected_algos:
            messagebox.showwarning("Warning", "Select at least one algorithm!")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Solving puzzle with selected algorithms...\n\n")
        # Reset stop event and run in thread to avoid freezing
        self.stop_event.clear()
        self.solving = True
        self.trace_text.delete(1.0, tk.END)

        thread = threading.Thread(target=self._solve_thread, args=(selected_algos,))
        thread.daemon = True
        thread.start()
    
    def _solve_thread(self, selected_algos):
        """Thread function to solve puzzle"""
        self.results = {}
        # Map UI names to filenames to run directly (run the .py files)
        algorithms = {
            "A*": "Astar.py",
            "BFS": "BFS.py",
            "DFS": "DFS.py",
            "Greedy": "Greedy.py",
            "UCS": "UCS.py",
            "Hill Climbing": "Hillclimping.py",
            "IDA*": "IDAstar.py",
            "Beem": "Beem.py"
        }
        
        for algo_name in selected_algos:
            # If user pressed Stop before starting this algorithm, wait until they Continue or restart
            while self.stop_event.is_set():
                # If solving was cancelled externally, break out
                if not self.solving:
                    break
                time.sleep(0.1)
            if not self.solving:
                break
            if algo_name not in algorithms:
                continue
            
            filename = algorithms[algo_name]
            # Announce start in CLI log
            self.append_log(f"--- {algo_name} starting ---\n")

            script_path = os.path.join(os.path.dirname(__file__), filename)
            # Run the user's file as a script so its stdout appears unchanged
            # Run with unbuffered output so the GUI receives stdout exactly
            # as when running the script directly from the CLI.
            cmd = [sys.executable, '-u', script_path]

            # Reset current proc info
            with self.proc_lock:
                self.current_proc = None
                self.proc_paused = False

            try:
                # Set cwd to the script's directory so relative file operations
                # inside the script behave the same as running it directly.
                # create per-process pause file and stop file and pass via env
                pause_path = os.path.join(tempfile.gettempdir(), f"p15_pause_{uuid.uuid4().hex}.pause")
                stop_path = os.path.join(tempfile.gettempdir(), f"p15_stop_{uuid.uuid4().hex}.stop")
                env = os.environ.copy()
                env['PAUSE_FILE'] = pause_path
                env['STOP_FILE'] = stop_path

                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        stdin=subprocess.PIPE, text=True,
                                        cwd=os.path.dirname(script_path), env=env)
                # remember pause/stop file paths so Stop can create them
                self.current_proc_pause = pause_path
                self.current_proc_stop = stop_path
                # Send the puzzle to the algorithm to the algorithm via stdin
                puzzle_str = ",".join(str(x) for x in self.current_puzzle)
                proc.stdin.write(puzzle_str + "\n")
                proc.stdin.flush()
                with self.proc_lock:
                    self.current_proc = proc
                    self.proc_paused = False
                # track peak memory (RSS) in bytes for this subprocess
                max_rss = 0
                p_psutil = None
                if PSUTIL_AVAILABLE:
                    try:
                        p_psutil = psutil.Process(proc.pid)
                    except Exception:
                        p_psutil = None

                # Reader thread to fetch stdout lines and append to log
                out_lines = []
                def reader():
                    try:
                        for line in proc.stdout:
                            out_lines.append(line)
                            self.append_log(line)
                            # Parse STATE markers and display puzzle live
                            if line.startswith("STATE:"):
                                try:
                                    state_str = line[6:].strip()  # Remove "STATE:" prefix
                                    state_data = eval(state_str)  # Convert string to list or tuple
                                    # Accept both list and tuple formats, convert to list
                                    if isinstance(state_data, (list, tuple)) and len(state_data) == 16:
                                        state_list = list(state_data) if isinstance(state_data, tuple) else state_data
                                        # Use direct method call instead of lambda to properly capture
                                        self.root.after(0, self.display_puzzle, state_list)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                reader_thread = threading.Thread(target=reader, daemon=True)
                reader_thread.start()

                # Track active running time (exclude suspended time)
                active_time = 0.0
                last_check = time.time()
                timeout = 15.0  # Increased timeout for 15-puzzle

                while True:
                    if proc.poll() is not None:
                        break

                    # If paused via psutil, don't advance active_time
                    paused = False
                    with self.proc_lock:
                        paused = self.proc_paused

                    now = time.time()
                    if not paused:
                        active_time += now - last_check
                        # sample memory usage while process is active
                        if p_psutil is not None:
                            try:
                                rss = p_psutil.memory_info().rss
                                if rss > max_rss:
                                    max_rss = rss
                            except Exception:
                                pass
                    last_check = now

                    if active_time > timeout:
                        # kill process
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        self.append_log(f"{algo_name} ✗ Not suitable (timeout > 15s)\n\n")
                        self.results[algo_name] = {
                            "nodes": 0,
                            "path_length": -1,
                            "time": timeout,
                            "solved": False,
                            "memory": max_rss,
                            "timeout": True
                        }
                        break

                    # check stop event (user asked to stop entirely)
                    if self.stop_event.is_set():
                        # Create pause file immediately so child process stops ASAP
                        try:
                            pause_path = getattr(self, 'current_proc_pause', None)
                            if pause_path and not os.path.exists(pause_path):
                                open(pause_path, 'w').close()
                        except Exception:
                            pass
                        # user wants to pause/freeze; if psutil available suspend
                        if PSUTIL_AVAILABLE:
                            try:
                                p = psutil.Process(proc.pid)
                                p.suspend()
                                with self.proc_lock:
                                    self.proc_paused = True
                                self.append_log(f"{algo_name} ⏸ Paused by user\n")
                            except Exception as e:
                                self.append_log(f"Could not pause process: {e}\n")
                        else:
                            self.append_log("Pause not available (install psutil).\n")
                        # Wait until stop_event cleared or process ends
                        while self.stop_event.is_set() and proc.poll() is None:
                            time.sleep(0.05)
                        # If resumed (stop_event cleared) and we had suspended the proc, resume it
                        if proc.poll() is None:
                            # Remove pause file so child can resume
                            try:
                                pause_path = getattr(self, 'current_proc_pause', None)
                                if pause_path and os.path.exists(pause_path):
                                    os.remove(pause_path)
                            except Exception:
                                pass
                            if PSUTIL_AVAILABLE:
                                try:
                                    p = psutil.Process(proc.pid)
                                    p.resume()
                                    with self.proc_lock:
                                        self.proc_paused = False
                                    self.append_log(f"{algo_name} ▶ Resumed by user\n")
                                except Exception:
                                    pass
                    time.sleep(0.02)

                # ensure reader thread finished
                reader_thread.join(timeout=1)

                out = ''.join(out_lines)

                # Try to extract simple metrics from stdout: look for lines mentioning Nodes or Path Length
                nodes = 0
                path_len = -1
                solved = False
                # simple heuristics: look for 'Nodes' and 'Path Length' occurrences
                try:
                    for line in out.splitlines():
                        l = line.lower()
                        if 'nodes' in l:
                            import re
                            m = re.search(r"(\d+)", l)
                            if m:
                                nodes = int(m.group(1))
                        if 'path length' in l or 'pathlength' in l or 'path len' in l:
                            import re
                            m = re.search(r"(\d+)", l)
                            if m:
                                path_len = int(m.group(1))
                        if ('solved' in l and ('yes' in l or 'true' in l or '✓' in l)) or ('puzzle solved' in l):
                            solved = True
                except Exception:
                    pass
                
                # populate results based on heuristics. Use the active_time measured
                # while the process ran so we have a numeric time value.
                result_time = active_time if 'active_time' in locals() else None

                local_optimum = False
                if 'hill' in  algo_name.lower():
                    hill_terms = ['local optimum', 'stuck', 'no better moves', 'cannot improve','local maxima', 'unsolved']
                    out_lower = out.lower()
                    for term in hill_terms:
                        if term in out_lower:
                            local_optimum = True
                            break
                is_solved = (solved or (path_len >= 0)) and not local_optimum

                if nodes or path_len >= 0 or solved:
                    self.results[algo_name] = {
                        "nodes": nodes,
                        "path_length": path_len,
                        "time": result_time,
                        "solved": is_solved,
                        "local_optimum": local_optimum,
                        "memory": max_rss,
                    }
                else:
                    # if nothing parseable, still store stdout for inspection
                    self.results[algo_name] = {
                        "nodes": 0,
                        "path_length": -1,
                        "time": result_time,
                        "solved": False,
                        "output": out,
                        "memory": max_rss,
                    }

            except Exception as e:
                self.append_log(f"{algo_name} ✗ Error: {e}\n\n")
                self.results[algo_name] = {
                    "nodes": 0,
                    "path_length": -1,
                    "time": 0,
                    "solved": False,
                    "memory": max_rss if 'max_rss' in locals() else 0,
                    "error": str(e)
                }
            finally:
                with self.proc_lock:
                    self.current_proc = None
                    self.proc_paused = False
            # After each algorithm, append its detailed log and (if available) its trace to CLI log
            try:
                r = self.results.get(algo_name, {})
                if r.get('solved'):
                    t = r.get('time')
                    time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                    mem = r.get('memory', 0)
                    mem_str = f"{mem/1024:.1f} KB" if mem else "N/A"
                    self.append_log(f"{algo_name} ✓ Solved | Nodes: {r.get('nodes')} | Time: {time_str} | Memory: {mem_str}\n")
                    path = r.get('path')
                    if path:
                        for step_i, step in enumerate(path):
                            rows = [step[r*4:(r+1)*4] for r in range(4)]
                            s = '\n'.join(' '.join(str(x) if x != 0 else ' ' for x in row) for row in rows)
                            self.append_log(f"Step {step_i}:\n{s}\n\n")
                else:
                    # Not solved or error
                    if 'error' in r:
                        self.append_log(f"{algo_name} ✗ Error: {r.get('error')}\n\n")
                    else:
                        t = r.get('time')
                        time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                        mem = r.get('memory', 0)
                        mem_str = f"{mem/1024:.1f} KB" if mem else "N/A"
                        self.append_log(f"{algo_name} ✗ Not solved | Nodes: {r.get('nodes',0)} | Time: {time_str} | Memory: {mem_str}\n\n")
            except Exception:
                # avoid crashing solver thread if logging fails
                pass
            # small pause to give UI responsiveness and check stop
            if self.stop_event.is_set():
                break
        
        self.root.after(0, self._update_results)
    
    def _update_results(self):
        """Update results display"""
        self.results_text.delete(1.0, tk.END)
        self.trace_text.delete(1.0, tk.END)
        
        # Find best algorithm (least nodes expanded)
        best_algo = None
        best_score = float('inf')

        for algo_name, result in self.results.items():
            solved = result.get('solved', False)
            nodes = result.get('nodes', 0)
            path_length = result.get('path_length', -1)
            t = result.get('time')
            time_str = f"{t:.4f}s" if (t is not None and isinstance(t, (int, float))) else "N/A"
            mem = result.get('memory', 0)
            mem_str = f"{mem/1024:.1f} KB" if mem else "N/A"

            self.results_text.insert(tk.END, f"{algo_name}:\n")
            if solved:
                self.results_text.insert(tk.END, f"  ✓ Solved\n")
                self.results_text.insert(tk.END, f"  Nodes Expanded: {nodes}\n")
                self.results_text.insert(tk.END, f"  Path Length: {path_length}\n")
                self.results_text.insert(tk.END, f"  Time: {time_str}\n")
                self.results_text.insert(tk.END, f"  Memory: {mem_str}\n\n")
                if nodes < best_score:
                    best_score = nodes
                    best_algo = algo_name
            else:
                # give more information if available
                if 'error' in result:
                    self.results_text.insert(tk.END, f"  ✗ Error: {result.get('error')}\n\n")
                else:
                    self.results_text.insert(tk.END, f"  ✗ Not Solved\n\n")

        if best_algo:
            self.best_algo_label.config(text=f"Best Algorithm: {best_algo} ({int(best_score)} nodes)")
            best_result = self.results.get(best_algo, {})
            path = best_result.get('path')
            if path:
                self.trace_text.insert(tk.END, f"Trace for {best_algo}:\n\n")
                for step_i, step in enumerate(path):
                    rows = [step[r*4:(r+1)*4] for r in range(4)]
                    s = '\n'.join(' '.join(str(x) if x != 0 else ' ' for x in row) for row in rows)
                    self.trace_text.insert(tk.END, f"Step {step_i}:\n{s}\n\n")
        else:
            self.best_algo_label.config(text="Best Algorithm: N/A")

        # Print final best algorithm at the bottom of results and CLI log
        if best_algo:
            self.results_text.insert(tk.END, "\n==============================\n")
            self.results_text.insert(tk.END, f"The best algorithm for this problem is: {best_algo}\n")
            self.results_text.insert(tk.END, "==============================\n")

        # mark solving finished
        self.solving = False
        self.stop_event.clear()

    def stop_solving(self):
        """Pause the currently running algorithm"""
        if self.solving:
            with self.proc_lock:
                proc = self.current_proc

            if proc is not None:
                try:
                    # Create PAUSE file for algorithm-side pause
                    pause_path = getattr(self, 'current_proc_pause', None)
                    if pause_path and not os.path.exists(pause_path):
                        open(pause_path, 'w').close()

                    # Suspend process using psutil if available
                    if PSUTIL_AVAILABLE:
                        p = psutil.Process(proc.pid)
                        p.suspend()
                        with self.proc_lock:
                            self.proc_paused = True

                    self.results_text.insert(tk.END, "\n⏸ Solving Paused...\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"\n❌ Pause Failed: {e}\n")
        else:
            self.results_text.insert(tk.END, "\nNo solver is currently running.\n")

    def show_best_algorithm(self):
        """Show the best algorithm from the last comparison (based on least nodes)."""
        if not self.results:
            messagebox.showinfo("Best Algorithm", "No results available. Run comparison first.")
            return

        best_algo = None
        best_nodes = float('inf')
        best_info = None

        for algo_name, r in self.results.items():
            if r.get('solved'):
                nodes = r.get('nodes', float('inf'))
                if nodes < best_nodes:
                    best_nodes = nodes
                    best_algo = algo_name
                    best_info = r

        if best_algo:
            bt = best_info.get('time')
            bt_str = f"{bt:.4f}s" if (bt is not None) else "N/A"
            msg = f"The best algorithm is: {best_algo}\nNodes: {best_nodes}\nTime: {bt_str}\nPath length: {best_info.get('path_length')}"
            messagebox.showinfo("Best Algorithm", msg)
            try:
                self.results_text.insert(tk.END, "\n" + msg + "\n")
                self.append_log(msg + "\n")
                self.best_algo_label.config(text=f"Best Algorithm: {best_algo} ({best_nodes} nodes)")
            except Exception:
                pass
        else:
            messagebox.showinfo("Best Algorithm", "No algorithm solved the puzzle yet.")

    def continue_solving(self):
        """Resume paused solver"""
        with self.proc_lock:
            proc = self.current_proc
            paused = self.proc_paused

        if proc is not None and paused:
            try:
                # Remove pause file so algorithm resumes
                pause_path = getattr(self, 'current_proc_pause', None)
                if pause_path and os.path.exists(pause_path):
                    os.remove(pause_path)

                # Resume using psutil
                if PSUTIL_AVAILABLE:
                    p = psutil.Process(proc.pid)
                    p.resume()
                    with self.proc_lock:
                        self.proc_paused = False

                self.results_text.insert(tk.END, "\n▶ Solving Resumed...\n")
            except Exception as e:
                self.results_text.insert(tk.END, f"\n❌ Resume Failed: {e}\n")
        else:
            self.results_text.insert(tk.END, "\nSolver is not paused.\n")


        
    def show_graph(self):
        """Display performance comparison graph"""
        if not self.results:
            messagebox.showwarning("Warning", "Please solve the puzzle first!")
            return

        # Build data arrays from results (only solved algorithms used for comparison)
        algo_names = []
        nodes_expanded = []
        path_lengths = []
        times = []  # in ms
        memories = []  # in KB

        for algo_name, result in self.results.items():
            if result.get("solved"):
                algo_names.append(algo_name)
                nodes_expanded.append(result.get("nodes", 0) or 0)
                path_lengths.append(result.get("path_length", -1) if result.get("path_length", -1) is not None else -1)
                t = result.get('time')
                times.append((t * 1000) if t is not None else 0)
                mem = result.get('memory', 0) or 0
                memories.append(mem / 1024.0)

        if not algo_names:
            messagebox.showwarning("Warning", "No solved algorithms to compare!")
            return

        # Prepare combined normalized score
        max_nodes = max(nodes_expanded) if nodes_expanded else 1
        max_time = max(times) if times else 1
        max_path = max([p for p in path_lengths if p >= 0]) if any(p >= 0 for p in path_lengths) else 1
        max_mem = max(memories) if memories else 1

        normalized_nodes = [n / max_nodes for n in nodes_expanded]
        normalized_times = [t / max_time for t in times]
        normalized_paths = [(p / max_path) if p >= 0 else 1.0 for p in path_lengths]
        normalized_mem = [m / max_mem for m in memories]
        # Weight nodes expanded 2x more since it's the primary efficiency metric
        combined = [(2.0*n) + t + p + m for n, t, p, m in zip(normalized_nodes, normalized_times, normalized_paths, normalized_mem)]

        # Create graph window and a Canvas for tkinter-only drawing
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Algorithm Performance Comparison")
        graph_window.geometry("1000x700")

        canvas = tk.Canvas(graph_window, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)

        # Colors palette
        palette = ["#4c72b0", "#55a868", "#c44e52", "#8172b2", "#ccb974", "#64b5cd", "#8c8c8c"]

        def draw():
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 200 or h < 200:
                # schedule later when geometry stabilized
                graph_window.after(100, draw)
                return

            left_margin = 120
            right_margin = 40
            top_margin = 20
            bottom_margin = 40
            chart_area_w = w - left_margin - right_margin
            chart_area_h = h - top_margin - bottom_margin

            # We'll draw 5 stacked charts: nodes, path length, time, memory, combined
            rows = 5
            row_h = chart_area_h / rows

            datasets = [
                ("Nodes Expanded", nodes_expanded, max_nodes),
                ("Path Length", [p if p>=0 else 0 for p in path_lengths], max_path),
                ("Time (ms)", times, max_time),
                ("Memory (KB)", memories, max_mem),
                ("Combined (norm)", combined, max(combined) if combined else 1)
            ]

            n = len(algo_names)
            if n == 0:
                return

            bar_slot = chart_area_w / n
            bar_width = min(80, bar_slot * 0.6)

            for ri, (title, data, vmax) in enumerate(datasets):
                y0 = top_margin + ri * row_h
                y1 = y0 + row_h
                # title
                canvas.create_text(left_margin - 10, y0 + 10, anchor='nw', text=title, font=("Arial", 10, "bold"))

                # Draw horizontal baseline
                canvas.create_line(left_margin, y1 - 30, w - right_margin, y1 - 30, fill="#333")

                # y-axis labels (0 and max)
                canvas.create_text(10, y1 - 30, anchor='w', text="0", font=("Arial", 9))
                canvas.create_text(10, y0 + 5, anchor='w', text=str(round(vmax, 2)), font=("Arial", 9))

                for i, val in enumerate(data):
                    # normalize value
                    try:
                        frac = float(val) / float(vmax) if vmax else 0.0
                    except Exception:
                        frac = 0.0
                    bx_center = left_margin + i * bar_slot + bar_slot / 2
                    bx0 = bx_center - bar_width/2
                    bx1 = bx_center + bar_width/2
                    max_bar_height = row_h - 60
                    bh = max(1, frac * max_bar_height)
                    by1 = y1 - 30
                    by0 = by1 - bh
                    color = palette[i % len(palette)]
                    canvas.create_rectangle(bx0, by0, bx1, by1, fill=color, outline='black')
                    # label under bar
                    canvas.create_text(bx_center, by1 + 12, text=algo_names[i], anchor='n', angle=0, font=("Arial", 9))
                    # value label
                    canvas.create_text(bx_center, by0 - 8, text=str(round(val, 2)), anchor='s', font=("Arial", 8))

        # Initial draw after window appears
        graph_window.after(150, draw)


def main():
    root = tk.Tk()
    app = PuzzleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

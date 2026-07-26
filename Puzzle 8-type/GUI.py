import tkinter as tk
from tkinter import ttk, messagebox
import time
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
#   8-PUZZLE UTILITIES
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
    """Check if 8-puzzle is solvable"""
    return count_inversions(tiles) % 2 == 0

def generate_solvable_puzzle():
    """Generate a solvable 8-puzzle"""
    while True:
        tiles = list(range(9))
        random.shuffle(tiles)
        if is_solvable(tiles):
            return tiles

# ================================
#   MAIN GUI APPLICATION
# ================================

class PuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver with AI Algorithms")
        self.root.geometry("1400x900")
        
        self.current_puzzle = None
        self.generated_puzzle = None
        self.stop_event = threading.Event()
        self.results = {}
        self.solving = False
        self.current_proc = None
        self.proc_paused = False
        self.proc_lock = threading.Lock()
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI widgets"""
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Puzzle display
        left_frame = ttk.LabelFrame(main_frame, text="8-Puzzle Board", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.puzzle_frame = ttk.Frame(left_frame)
        self.puzzle_frame.pack(pady=20)
        
        self.puzzle_buttons = []
        for i in range(9):
            btn = tk.Button(self.puzzle_frame, width=8, height=4, font=("Arial", 20, "bold"))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            self.puzzle_buttons.append(btn)
        
        # Right panel - Controls
        right_frame = ttk.LabelFrame(main_frame, text="Controls & Results", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        tk.Button(button_frame, text="Generate Puzzle", command=self.generate_puzzle, bg="#224522", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        
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

        action_btn_frame = ttk.Frame(right_frame)
        action_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_btn_frame, text="Solve & Compare Selected", command=self.solve_and_compare).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(action_btn_frame, text="Show Performance Graph", command=self.show_graph).pack(side=tk.LEFT)

        control_btn_frame = ttk.Frame(right_frame)
        control_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(control_btn_frame, text="Stop", command=self.stop_solving, bg="#FF0000", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        tk.Button(control_btn_frame, text="Continue", command=self.continue_solving, bg="#085403", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        results_label = ttk.Label(right_frame, text="Results:", font=("Arial", 11, "bold"))
        results_label.pack(anchor=tk.W, pady=(20, 10))
        
        scroll = ttk.Scrollbar(right_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(right_frame, height=30, width=40, yscrollcommand=scroll.set)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.results_text.yview)
        
        self.best_algo_label = ttk.Label(right_frame, text="Best Algorithm: N/A", 
                                        font=("Arial", 10, "bold"), foreground="green")
        self.best_algo_label.pack(anchor=tk.W, pady=10)
        tk.Button(right_frame, text="Show Best Algorithm", command=self.show_best_algorithm, bg="#FF0000", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)

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
            # Use the same Python executable with -u for unbuffered output so STATE markers stream live
            proc = subprocess.Popen(
                [sys.executable, '-u', algo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(algo_path)
            )
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
                                if isinstance(state_data, (list, tuple)) and len(state_data) == 9:
                                    state_list = list(state_data) if isinstance(state_data, tuple) else state_data
                                    self.root.after(0, lambda st=state_list: self.display_puzzle(st))
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
                self.solving = False
            
            self.root.after(0, update_results)
            
        except Exception as e:
            self.results_text.insert(tk.END, f"Error: {e}\n")
            self.solving = False
    
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
        self.stop_event.clear()
        self.solving = True

        thread = threading.Thread(target=self._solve_thread, args=(selected_algos,))
        thread.daemon = True
        thread.start()
    
    def _solve_thread(self, selected_algos):
        """Thread function to solve puzzle"""
        self.results = {}
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
            while self.stop_event.is_set():
                if not self.solving:
                    break
                time.sleep(0.1)
            if not self.solving:
                break
            if algo_name not in algorithms:
                continue
            
            filename = algorithms[algo_name]
            self.append_log(f"--- {algo_name} starting ---\n")

            script_path = os.path.join(os.path.dirname(__file__), filename)
            cmd = [sys.executable, '-u', script_path]

            with self.proc_lock:
                self.current_proc = None
                self.proc_paused = False

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                        cwd=os.path.dirname(script_path))
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
                                    if isinstance(state_data, (list, tuple)) and len(state_data) == 9:
                                        state_list = list(state_data) if isinstance(state_data, tuple) else state_data
                                        self.root.after(0, lambda st=state_list: self.display_puzzle(st))
                                except Exception:
                                    pass
                    except Exception:
                        pass

                reader_thread = threading.Thread(target=reader, daemon=True)
                reader_thread.start()

                active_time = 0.0
                last_check = time.time()
                timeout = 8.0

                while True:
                    if proc.poll() is not None:
                        break

                    paused = False
                    with self.proc_lock:
                        paused = self.proc_paused

                    now = time.time()
                    if not paused:
                        active_time += now - last_check
                        # sample memory usage (RSS) while process is running
                        if p_psutil is not None:
                            try:
                                rss = p_psutil.memory_info().rss
                                if rss > max_rss:
                                    max_rss = rss
                            except Exception:
                                pass
                    last_check = now

                    if active_time > timeout:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        self.append_log(f"{algo_name} ✗ Not suitable (timeout > 8s)\n\n")
                        self.results[algo_name] = {
                            "nodes": 0,
                            "path_length": -1,
                            "time": timeout,
                            "solved": False,
                            "memory": max_rss,
                            "timeout": True
                        }
                        break

                    if self.stop_event.is_set():
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
                        while self.stop_event.is_set() and proc.poll() is None:
                            time.sleep(0.1)
                        if proc.poll() is None:
                            if PSUTIL_AVAILABLE:
                                try:
                                    p = psutil.Process(proc.pid)
                                    p.resume()
                                    with self.proc_lock:
                                        self.proc_paused = False
                                    self.append_log(f"{algo_name} ▶ Resumed by user\n")
                                except Exception:
                                    pass
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

                result_time = active_time if 'active_time' in locals() else None

                out_lower = out.lower()
                local_optimum = False
                if 'hill' in algo_name.lower():
                    hill_keywords = [
                        'local optimum', 'local optimum.', 'local maximum', 'local maxima',
                        'stuck', 'no improvement', 'plateau', 'local', 'hill-climb',
                        'hill climbing', 'no better', 'unsolved'
                    ]
                    for kw in hill_keywords:
                        if kw in out_lower:
                            local_optimum = True
                            break

                is_solved = (solved or (path_len >= 0)) and (not local_optimum)

                if nodes or path_len >= 0 or solved:
                    self.results[algo_name] = {
                        "nodes": nodes,
                        "path_length": path_len,
                        "time": result_time,
                        "solved": bool(is_solved),
                        "local_optimum": bool(local_optimum),
                        "memory": max_rss
                    }
                else:
                    self.results[algo_name] = {
                        "nodes": 0,
                        "path_length": -1,
                        "time": result_time,
                        "solved": False,
                        "local_optimum": bool(local_optimum),
                        "memory": max_rss,
                        "output": out
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

            try:
                r = self.results.get(algo_name, {})
                if r.get('solved'):
                    t = r.get('time')
                    time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                    mem = r.get('memory', 0)
                    mem_str = f"{mem/1024:.1f} KB" if mem else "N/A"
                    self.append_log(f"{algo_name} ✓ Solved | Nodes: {r.get('nodes')} | Time: {time_str} | Memory: {mem_str}\n")
                else:
                    if 'error' in r:
                        self.append_log(f"{algo_name} ✗ Error: {r.get('error')}\n\n")
                    else:
                        t = r.get('time')
                        time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                        mem = r.get('memory', 0)
                        mem_str = f"{mem/1024:.1f} KB" if mem else "N/A"
                        self.append_log(f"{algo_name} ✗ Not solved | Nodes: {r.get('nodes',0)} | Time: {time_str} | Memory: {mem_str}\n\n")
            except Exception:
                pass

            if self.stop_event.is_set():
                break
        
        self.root.after(0, self._update_results)
    
    def _update_results(self):
        """Update results display"""
        self.results_text.delete(1.0, tk.END)
        
        solved_list = []
        for algo_name, r in self.results.items():
            if r.get('solved'):
                solved_list.append({
                    'name': algo_name,
                    'nodes': float(r.get('nodes', 0) or 0),
                    'time': float(r.get('time')) if (r.get('time') is not None) else None,
                    'path': int(r.get('path_length')) if (isinstance(r.get('path_length'), int) and r.get('path_length') >= 0) else None,
                    'memory': float(r.get('memory', 0) or 0) / 1024.0
                })

        best_algo = None
        best_score = float('inf')
        if solved_list:
            max_nodes = max(s['nodes'] for s in solved_list) or 1.0
            times_for_norm = [s['time'] for s in solved_list if s['time'] is not None]
            max_time = max(times_for_norm) if times_for_norm else 1.0
            path_for_norm = [s['path'] for s in solved_list if s['path'] is not None]
            max_path = max(path_for_norm) if path_for_norm else 1.0
            mem_for_norm = [s['memory'] for s in solved_list if s.get('memory') is not None]
            max_mem = max(mem_for_norm) if mem_for_norm else 1.0

            for s in solved_list:
                norm_nodes = (s['nodes'] / max_nodes) if max_nodes else 0.0
                norm_time = (s['time'] / max_time) if (s['time'] is not None and max_time) else 1.0
                norm_path = (s['path'] / max_path) if (s['path'] is not None and max_path) else 1.0
                norm_mem = (s['memory'] / max_mem) if (s.get('memory') is not None and max_mem) else 0.0
                # Weight nodes expanded 2x more since it's the primary efficiency metric
                combined = (2.0 * norm_nodes) + norm_time + norm_path + norm_mem
                if combined < best_score:
                    best_score = combined
                    best_algo = s['name']
        
        for algo_name, result in self.results.items():
            if result["solved"]:
                self.results_text.insert(tk.END, f"{algo_name}:\n")
                self.results_text.insert(tk.END, f"  ✓ Solved\n")
                self.results_text.insert(tk.END, f"  Nodes Expanded: {result['nodes']}\n")
                self.results_text.insert(tk.END, f"  Path Length: {result['path_length']}\n")
                t = result.get('time')
                time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                self.results_text.insert(tk.END, f"  Time: {time_str}\n")
                mem = result.get('memory', 0)
                mem_str = f"{mem/1024.0:.2f} KB" if mem else "N/A"
                self.results_text.insert(tk.END, f"  Memory: {mem_str}\n\n")
            else:
                self.results_text.insert(tk.END, f"{algo_name}:\n")
                self.results_text.insert(tk.END, f"  ✗ Not Solved\n\n")
        
        if best_algo:
            best_nodes = next((s['nodes'] for s in solved_list if s['name'] == best_algo), 0)
            self.best_algo_label.config(text=f"Best Algorithm: {best_algo} ({int(best_nodes)} nodes)")
        else:
            self.best_algo_label.config(text="Best Algorithm: N/A")

        if best_algo:
            self.results_text.insert(tk.END, "\n==============================\n")
            self.results_text.insert(tk.END, f"The best algorithm for this problem is: {best_algo}\n")
            self.results_text.insert(tk.END, "==============================\n")
            self.solving = False
            self.stop_event.clear()

    def stop_solving(self):
        """Signal the solver thread to pause."""
        if self.solving:
            self.stop_event.set()
            self.append_log("\nStop requested. Pausing solver...\n")
            with self.proc_lock:
                proc = self.current_proc
                if PSUTIL_AVAILABLE and proc and proc.poll() is None:
                    try:
                        ps_proc = psutil.Process(proc.pid)
                        ps_proc.suspend()
                        self.proc_paused = True
                        self.append_log("Process paused by user (psutil).\n")
                    except Exception as e:
                        self.append_log(f"Could not pause process: {e}\n")
        else:
            self.append_log("\nNo solver is currently running.\n")

    def continue_solving(self):
        """Resume a paused solver process."""
        if not self.solving:
            self.append_log("No solver is currently running to continue.\n")
            return

        # مسح علم التوقف
        self.stop_event.clear()
        
        with self.proc_lock:
            proc = self.current_proc
            was_paused = self.proc_paused

        if proc is None:
            self.append_log("No active algorithm process to resume.\n")
            return

        if PSUTIL_AVAILABLE and was_paused:
            try:
                ps_proc = psutil.Process(proc.pid)
                ps_proc.resume()           # استئناف العملية على مستوى النظام
                with self.proc_lock:
                    self.proc_paused = False
                self.append_log("Process resumed by user (psutil).\n")
            except Exception as e:
                self.append_log(f"Could not resume process: {e}\n")
        else:
            if not PSUTIL_AVAILABLE:
                self.append_log("psutil not installed; cannot resume process programmatically.\n")
            else:
                self.append_log("Process is not marked as paused; resuming via thread flag.\n")

    def show_best_algorithm(self):
        """Show the best algorithm using the same combined metric as the comparison."""
        if not self.results:
            messagebox.showinfo("Best Algorithm", "No results available. Run comparison first.")
            return

        solved_list = []
        for algo_name, r in self.results.items():
            if r.get('solved'):
                solved_list.append({
                    'name': algo_name,
                    'nodes': float(r.get('nodes', 0) or 0),
                    'time': float(r.get('time')) if (r.get('time') is not None) else None,
                    'path': int(r.get('path_length')) if (isinstance(r.get('path_length'), int) and r.get('path_length') >= 0) else None,
                    'memory': float(r.get('memory', 0) or 0) / 1024.0
                })

        if not solved_list:
            messagebox.showinfo("Best Algorithm", "No algorithm solved the puzzle yet.")
            return

        max_nodes = max(s['nodes'] for s in solved_list) or 1.0
        times_for_norm = [s['time'] for s in solved_list if s['time'] is not None]
        max_time = max(times_for_norm) if times_for_norm else 1.0
        path_for_norm = [s['path'] for s in solved_list if s['path'] is not None]
        max_path = max(path_for_norm) if path_for_norm else 1.0
        mem_for_norm = [s['memory'] for s in solved_list if s.get('memory') is not None]
        max_mem = max(mem_for_norm) if mem_for_norm else 1.0

        best_score = float('inf')
        best = None
        for s in solved_list:
            norm_nodes = (s['nodes'] / max_nodes) if max_nodes else 0.0
            norm_time = (s['time'] / max_time) if (s['time'] is not None and max_time) else 1.0
            norm_path = (s['path'] / max_path) if (s['path'] is not None and max_path) else 1.0
            norm_mem = (s['memory'] / max_mem) if (s.get('memory') is not None and max_mem) else 0.0
            combined = norm_nodes + norm_time + norm_path + norm_mem
            if combined < best_score:
                best_score = combined
                best = s

        if best:
            bt = best['time']
            bt_str = f"{bt:.4f}s" if (bt is not None) else "N/A"
            nodes = int(best['nodes'])
            pathlen = best['path'] if best['path'] is not None else 'N/A'
            mem = best.get('memory')
            mem_str = f"{mem:.2f} KB" if (mem is not None) else 'N/A'
            msg = f"The best algorithm is: {best['name']}\nNodes: {nodes}\nTime: {bt_str}\nPath length: {pathlen}\nMemory: {mem_str}"
            messagebox.showinfo("Best Algorithm", msg)

    def continue_solving(self):
        """Resume a paused solver process."""
        if not self.solving:
            self.append_log("No solver is currently running to continue.\n")
            return

        if self.stop_event.is_set():
            self.stop_event.clear()

        with self.proc_lock:
            proc = self.current_proc
            was_paused = self.proc_paused

        if proc is None:
            self.append_log("No active algorithm process to resume.\n")
            return

        if PSUTIL_AVAILABLE and was_paused:
            try:
                p = psutil.Process(proc.pid)
                p.resume()
                with self.proc_lock:
                    self.proc_paused = False
                self.append_log("Process resumed by user.\n")
            except Exception as e:
                self.append_log(f"Could not resume process: {e}\n")
        else:
            if not PSUTIL_AVAILABLE:
                self.append_log("psutil not installed; cannot resume process programmatically.\n")
            else:
                self.append_log("Process is not marked as paused; resume signal sent.\n")

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

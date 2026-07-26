import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sys
import subprocess
import json
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
        self.root.geometry("1400x700")
        
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
        ttk.Button(button_frame, text="Generate Puzzle", command=self.generate_puzzle).pack(fill=tk.X, pady=5)
        
        algo_label = ttk.Label(right_frame, text="Select Algorithms:", font=("Arial", 11, "bold"))
        algo_label.pack(anchor=tk.W, pady=(20, 10))
        
        self.algo_vars = {}
        algorithms = ["A*", "BFS", "DFS", "Greedy", "UCS", "Hill Climbing", "IDA*", "Beem"]
        
        for algo in algorithms:
            var = tk.BooleanVar(value=True)
            self.algo_vars[algo] = var
            ttk.Checkbutton(right_frame, text=algo, variable=var).pack(anchor=tk.W, padx=20)

        action_btn_frame = ttk.Frame(right_frame)
        action_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_btn_frame, text="Solve & Compare", command=self.solve_and_compare).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(action_btn_frame, text="Show Performance Graph", command=self.show_graph).pack(side=tk.LEFT)

        control_btn_frame = ttk.Frame(right_frame)
        control_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(control_btn_frame, text="Stop", command=self.stop_solving).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(control_btn_frame, text="Continue", command=self.continue_solving).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        results_label = ttk.Label(right_frame, text="Results:", font=("Arial", 11, "bold"))
        results_label.pack(anchor=tk.W, pady=(20, 10))
        
        log_label = ttk.Label(right_frame, text="Trying Output:", font=("Arial", 11, "bold"))
        log_label.pack(anchor=tk.W, pady=(10, 0))
        self.log_text = tk.Text(right_frame, height=10, width=40)
        self.log_text.pack(fill=tk.BOTH, expand=False, pady=(0,10))
        
        scroll = ttk.Scrollbar(right_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(right_frame, height=20, width=40, yscrollcommand=scroll.set)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.results_text.yview)
        
        self.best_algo_label = ttk.Label(right_frame, text="Best Algorithm: N/A", 
                                        font=("Arial", 10, "bold"), foreground="green")
        self.best_algo_label.pack(anchor=tk.W, pady=10)
        ttk.Button(right_frame, text="Show Best Algorithm", command=self.show_best_algorithm).pack(fill=tk.X, pady=5)

    def append_log(self, text):
        """Thread-safe append to the CLI log area."""
        def _append():
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
        self.root.after(0, _append)
        
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

                out_lines = []
                def reader():
                    try:
                        for line in proc.stdout:
                            out_lines.append(line)
                            self.append_log(line)
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
                        if 'solved' in l and ('yes' in l or 'true' in l or '✓' in l):
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
                        'hill climbing', 'no better'
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
                        "local_optimum": bool(local_optimum)
                    }
                else:
                    self.results[algo_name] = {
                        "nodes": 0,
                        "path_length": -1,
                        "time": result_time,
                        "solved": False,
                        "local_optimum": bool(local_optimum),
                        "output": out
                    }

            except Exception as e:
                self.append_log(f"{algo_name} ✗ Error: {e}\n\n")
                self.results[algo_name] = {
                    "nodes": 0,
                    "path_length": -1,
                    "time": 0,
                    "solved": False,
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
                    self.append_log(f"{algo_name} ✓ Solved | Nodes: {r.get('nodes')} | Time: {time_str}\n")
                else:
                    if 'error' in r:
                        self.append_log(f"{algo_name} ✗ Error: {r.get('error')}\n\n")
                    else:
                        t = r.get('time')
                        time_str = f"{t:.4f}s" if (t is not None) else "N/A"
                        self.append_log(f"{algo_name} ✗ Not solved | Nodes: {r.get('nodes',0)} | Time: {time_str}\n\n")
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
                    'path': int(r.get('path_length')) if (isinstance(r.get('path_length'), int) and r.get('path_length') >= 0) else None
                })

        best_algo = None
        best_score = float('inf')
        if solved_list:
            max_nodes = max(s['nodes'] for s in solved_list) or 1.0
            times_for_norm = [s['time'] for s in solved_list if s['time'] is not None]
            max_time = max(times_for_norm) if times_for_norm else 1.0
            path_for_norm = [s['path'] for s in solved_list if s['path'] is not None]
            max_path = max(path_for_norm) if path_for_norm else 1.0

            for s in solved_list:
                norm_nodes = (s['nodes'] / max_nodes) if max_nodes else 0.0
                norm_time = (s['time'] / max_time) if (s['time'] is not None and max_time) else 1.0
                norm_path = (s['path'] / max_path) if (s['path'] is not None and max_path) else 1.0
                combined = norm_nodes + norm_time + norm_path
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
                self.results_text.insert(tk.END, f"  Time: {time_str}\n\n")
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
        """Signal the solver thread to stop."""
        if self.solving:
            self.stop_event.set()
            self.append_log("\nStop requested. Pausing solver...\n")
        else:
            self.append_log("\nNo solver is currently running.\n")

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
                    'path': int(r.get('path_length')) if (isinstance(r.get('path_length'), int) and r.get('path_length') >= 0) else None
                })

        if not solved_list:
            messagebox.showinfo("Best Algorithm", "No algorithm solved the puzzle yet.")
            return

        max_nodes = max(s['nodes'] for s in solved_list) or 1.0
        times_for_norm = [s['time'] for s in solved_list if s['time'] is not None]
        max_time = max(times_for_norm) if times_for_norm else 1.0
        path_for_norm = [s['path'] for s in solved_list if s['path'] is not None]
        max_path = max(path_for_norm) if path_for_norm else 1.0

        best_score = float('inf')
        best = None
        for s in solved_list:
            norm_nodes = (s['nodes'] / max_nodes) if max_nodes else 0.0
            norm_time = (s['time'] / max_time) if (s['time'] is not None and max_time) else 1.0
            norm_path = (s['path'] / max_path) if (s['path'] is not None and max_path) else 1.0
            combined = norm_nodes + norm_time + norm_path
            if combined < best_score:
                best_score = combined
                best = s

        if best:
            bt = best['time']
            bt_str = f"{bt:.4f}s" if (bt is not None) else "N/A"
            nodes = int(best['nodes'])
            pathlen = best['path'] if best['path'] is not None else 'N/A'
            msg = f"The best algorithm is: {best['name']}\nNodes: {nodes}\nTime: {bt_str}\nPath length: {pathlen}"
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
        
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Algorithm Performance Comparison")
        graph_window.geometry("900x600")
        
        algo_names = []
        nodes_expanded = []
        path_lengths = []
        times = []
        
        for algo_name, result in self.results.items():
            if result["solved"]:
                algo_names.append(algo_name)
                nodes_expanded.append(result["nodes"])
                path_lengths.append(result["path_length"])
                t = result.get('time')
                times.append(t * 1000 if t is not None else 0)
        
        if not algo_names:
            messagebox.showwarning("Warning", "No solved algorithms to compare!")
            return
        
        fig = Figure(figsize=(12, 8), dpi=75)
        
        ax1 = fig.add_subplot(2, 2, 1)
        if len(algo_names) > 1:
            colors = [plt.cm.viridis(i / (len(algo_names) - 1)) for i in range(len(algo_names))]
        else:
            colors = [plt.cm.viridis(0.5)]
        ax1.bar(algo_names, nodes_expanded, color=colors)
        ax1.set_ylabel("Nodes Expanded")
        ax1.set_title("Nodes Expanded Comparison")
        ax1.tick_params(axis='x', rotation=45)
        
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.bar(algo_names, path_lengths, color=colors)
        ax2.set_ylabel("Path Length")
        ax2.set_title("Path Length Comparison")
        ax2.tick_params(axis='x', rotation=45)
        
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.bar(algo_names, times, color=colors)
        ax3.set_ylabel("Time (ms)")
        ax3.set_title("Execution Time Comparison")
        ax3.tick_params(axis='x', rotation=45)
        
        ax4 = fig.add_subplot(2, 2, 4)
        max_nodes = max(nodes_expanded) if nodes_expanded else 1
        normalized_nodes = [n/max_nodes for n in nodes_expanded]
        max_time = max(times) if times else 1
        normalized_times = [t/max_time for t in times]
        max_path = max(path_lengths) if path_lengths else 1
        normalized_paths = [p/max_path for p in path_lengths]
        
        combined = [n + t + p for n, t, p in zip(normalized_nodes, normalized_times, normalized_paths)]
        ax4.bar(algo_names, combined, color=colors)
        ax4.set_ylabel("Combined Score (Lower is Better)")
        ax4.set_title("Overall Performance (Normalized)")
        ax4.tick_params(axis='x', rotation=45)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = PuzzleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

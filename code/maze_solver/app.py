"""
maze solver gui thing for the assignment.
can make mazes and solve them with stuff like bfs/dfs.
"""

import json
import csv
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import threading

try:
    from .maze_generator import generate_maze, MazeResult
    from .algorithms import ALGORITHMS, calculate_values, calculate_policy
    from .exporter import Exporter
    from .visualizer import Visualizer
    from .generate_all_graphs import generate_graphs
except ImportError:
    from maze_generator import generate_maze, MazeResult
    from algorithms import ALGORITHMS, calculate_values, calculate_policy
    from exporter import Exporter
    from visualizer import Visualizer
    from generate_all_graphs import generate_graphs


HISTORY_FILE = Path(__file__).parent / "execution_history.json"
SCALABILITY_FILE = Path(__file__).parent / "data" / "maze_scalability_results_clean.csv"
MAX_HISTORY = 200


def load_history() -> list:
    """loads past runs from the json file"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_history(history: list) -> None:
    """saves history to file"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)


class MazeApp:
    """the main gui class"""
    
    def __init__(self):
        """Set up the main window and state."""
        self.root = tk.Tk()
        self.root.title("Maze Solver")
        self.root.geometry("1300x850")
        self.root.configure(bg="#f1f5f9")

        self.matrix: List[str] = []
        self.maze_result: MazeResult | None = None
        self.start = (1, 1)
        self.goal = (1, 1)
        self.current_path: List[tuple] = []
        self.current_algorithm = ""
        self.all_results: Dict[str, Dict] = {}
        self.execution_history = load_history()
        self.view_mode = "original"
        self.exploration_step = 0
        self.exploration_order: List[tuple] = []
        self.step_var = tk.IntVar(value=0)
        self.history_text = None # Safety initialization
        self._animating = False
        self._anim_id = None
        
        self.exporter = Exporter()
        self.visualizer = Visualizer()
        self.executed_algorithms = set()

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        """set up looks for the gui"""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        bg, fg = "#ffffff", "#1e293b"
        accent = "#2563eb"
        
        self.root.configure(bg=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg, font=("Inter", 10))
        self.style.configure("Title.TLabel", font=("Inter", 14, "bold"), foreground="#0f172a", padding=(0, 5))
        self.style.configure("Header.TLabel", font=("Inter", 16, "bold"), foreground=accent)
        
        self.style.configure("TButton", font=("Inter", 10, "bold"), padding=8)
        self.style.map("TButton", background=[("active", "#f1f5f9")])
        
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg, font=("Inter", 10, "bold"))
        
        self.style.configure("Treeview", background="white", fieldbackground="white", foreground=fg, rowheight=30, font=("Inter", 9))
        self.style.configure("Treeview.Heading", background="#f8fafc", foreground="#64748b", font=("Inter", 10, "bold"))

    def _build_ui(self):
        """build the main layout"""
        # Master container
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Top Section (Sidebar + Maze View)
        upper_frame = ttk.Frame(self.main_paned, padding=10)
        self.main_paned.add(upper_frame, weight=4)

        # Left Panel (Scrollable Sidebar)
        sidebar_outer = ttk.Frame(upper_frame, width=300)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        sidebar_outer.pack_propagate(False) # Keep width fixed

        canvas = tk.Canvas(sidebar_outer, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(sidebar_outer, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=5)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # FIXED: Local mousewheel binding to avoid buggy global scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_to_mousewheel)
        canvas.bind("<Leave>", _unbind_from_mousewheel)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=280)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Sidebar Content
        left = scrollable_frame

        # 1. Generation
        ttk.Label(left, text="Maze Generation", style="Title.TLabel").pack(anchor=tk.W)
        gen = ttk.Frame(left, padding=2)
        gen.pack(fill=tk.X, pady=(0, 10))

        for lbl, var, default in [("Width:", "width_var", "100"), ("Height:", "height_var", "100"), ("Seed:", "seed_var", "")]:
            f = ttk.Frame(gen)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=lbl, width=10).pack(side=tk.LEFT)
            v = tk.StringVar(value=default)
            setattr(self, var, v)
            ttk.Entry(f, textvariable=v, width=10).pack(side=tk.LEFT, padx=4)

        self.maze_type_var = tk.StringVar(value="Braided")
        type_frame = ttk.Frame(gen)
        type_frame.pack(fill=tk.X, pady=(4, 2))
        ttk.Label(type_frame, text="Type:", width=10).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Perfect", variable=self.maze_type_var, value="Perfect").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(type_frame, text="Braided", variable=self.maze_type_var, value="Braided").pack(side=tk.LEFT)

        f_braid = ttk.Frame(gen)
        f_braid.pack(fill=tk.X, pady=5)
        ttk.Label(f_braid, text="Braid Factor:").pack(side=tk.LEFT)
        self.braid_var_str = tk.StringVar(value="0.3")
        ttk.Entry(f_braid, textvariable=self.braid_var_str, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Button(gen, text="Generate Maze", command=self.make_new_maze).pack(fill=tk.X, pady=(5, 0))

        # 2. Standard Algorithms
        ttk.Label(left, text="Heuristic Solvers", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 0))
        solve_frame = ttk.Frame(left)
        solve_frame.pack(fill=tk.X, pady=5)
        
        for name in [a for a in ALGORITHMS if "Iteration" not in a]:
            ttk.Button(solve_frame, text=name, command=lambda n=name: self.run_solver(n)).pack(fill=tk.X, pady=1)

        # 4. MDP Algorithms (Grouped with params)
        ttk.Label(left, text="MDP Solvers", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 0))
        mdp_box = ttk.Frame(left, padding=5, borderwidth=1, relief="solid") # Visual grouping
        mdp_box.pack(fill=tk.X, pady=5)
        
        self.gamma_var = tk.StringVar(value="0.99")
        self.epsilon_var = tk.StringVar(value="1e-6")
        self.reward_var = tk.StringVar(value="-1.0")
        
        mdp_params = [
            ("Discount Factor:", self.gamma_var),
            ("Convergence Thr:", self.epsilon_var),
            ("Step Cost:", self.reward_var)
        ]

        
        for lbl, var in mdp_params:
            f = ttk.Frame(mdp_box)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=lbl, width=12).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=var, width=10).pack(side=tk.LEFT, padx=4)


        for name in [a for a in ALGORITHMS if "Iteration" in a]:
            ttk.Button(mdp_box, text=name, command=lambda n=name: self.run_solver(n)).pack(fill=tk.X, pady=2)

        ttk.Button(left, text="Run All Algorithms", command=self._on_run_all).pack(fill=tk.X, pady=(8, 0))
        ttk.Button(left, text="Generate Report", command=self.generate_report).pack(fill=tk.X, pady=(4, 0))

        # 5. History
        ttk.Label(left, text="Quick History", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 0))
        self.history_text = tk.Text(left, height=6, width=30, bg="white", fg="#64748b",
                                    font=("Inter", 8), relief="flat", borderwidth=1, padx=5, pady=5)
        self.history_text.pack(fill=tk.X, pady=5)
        
        ttk.Button(left, text="Clear History", command=self._clear_history).pack(fill=tk.X)
        self._refresh_history_display()

        # Right Panel (Maze View)
        right = ttk.Frame(upper_frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.view_title = ttk.Label(right, text="Maze View", style="Header.TLabel")
        self.view_title.pack(anchor=tk.W)

        # Loading Bar
        self.loading_frame = ttk.Frame(right, padding=(0, 5))
        self.loading_frame.pack(fill=tk.X)
        self.progress = ttk.Progressbar(self.loading_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X)
        self.status_label = ttk.Label(self.loading_frame, text="Ready", font=("Inter", 9), foreground="#64748b")
        self.status_label.pack(pady=2)

        # View Controls
        view_ctrl = ttk.Frame(right)
        view_ctrl.pack(fill=tk.X, pady=(0, 5))
        self.view_var = tk.StringVar(value="original")
        for label, val in [("Maze Only", "original"), ("Exploration", "exploration"), ("Solution Path", "path")]:
            ttk.Radiobutton(view_ctrl, text=label, variable=self.view_var, value=val,
                            command=self.view_update).pack(side=tk.LEFT, padx=10)

        # Canvas for Maze
        canvas_box = tk.Frame(right, background="white", borderwidth=1, relief="solid")
        canvas_box.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_box, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda e: self._draw_maze() if self.matrix else None)

        # KPIs
        self.metrics_strip = ttk.Frame(right, padding=(0, 10))
        self.metrics_strip.pack(fill=tk.X)
        self.kpi_labels = {}
        for key, title in [("time", "RUNTIME"), ("nodes", "EXPANSION"), ("path", "PATH COST"), ("converge", "CONVERGENCE")]:
            f = ttk.Frame(self.metrics_strip)
            f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            ttk.Label(f, text=title, font=("Inter", 8, "bold"), foreground="#64748b").pack()
            l = ttk.Label(f, text="--", font=("JetBrains Mono", 11, "bold"))
            l.pack()
            self.kpi_labels[key] = l

        # Bottom Section (Comparison Table)
        bottom_frame = ttk.Frame(self.main_paned, padding=10)
        self.main_paned.add(bottom_frame, weight=1)
        
        ttk.Label(bottom_frame, text="Comparison Dashboard", style="Title.TLabel").pack(anchor=tk.W)
        table_wrap = ttk.Frame(bottom_frame)
        table_wrap.pack(fill=tk.BOTH, expand=True)

        # Expanded columns for all requested metrics (Search + MDP)
        columns = ("algorithm", "solved", "path", "expanded", "frontier", "gap", "iter", "gamma", "eps", "rollout", "time_ms")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=5)
        
        headers = {
            "algorithm": "ALGORITHM",
            "solved": "SUCCESS",
            "path": "PATH LEN",
            "expanded": "EXPANDED",
            "frontier": "PEAK FRONTIER (MEM PROXY)",
            "gap": "GAP",
            "iter": "ITER",
            "gamma": "DISCOUNT",
            "eps": "CONVERGENCE",
            "rollout": "ROLLOUT",
            "time_ms": "TIME (MS)"
        }

        
        for c in columns:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=70, anchor=tk.CENTER)
        
        self.tree.column("algorithm", width=140, anchor=tk.W)
        self.tree.column("expanded", width=90)
        self.tree.column("frontier", width=230)
        self.tree.column("time_ms", width=80)
        self.tree.column("rollout", width=90)
        self.tree.column("gap", width=60)
        
        # Grid layout for treeview + scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        v_scroll = ttk.Scrollbar(table_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_wrap, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)
        
        self.tree.bind("<<TreeviewSelect>>", self.select_algo)

        # Evaluation Summary (Detailed Log Area)
        summary_wrap = ttk.Frame(bottom_frame)
        summary_wrap.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.summary_text = tk.Text(summary_wrap, height=6, bg="#f8fafc", fg="#1e293b",
                                    font=("Inter", 9), relief="flat", borderwidth=1, padx=10, pady=5)
        summary_scroll = ttk.Scrollbar(summary_wrap, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.summary_text.insert(tk.END, "Select an algorithm to view the detailed performance log.")
        self.summary_text.config(state=tk.DISABLED)

    def view_update(self):
        """updates the maze view"""
        self.view_mode = self.view_var.get()
        if self.view_mode == "exploration":
            self.animate_search()
        else:
            self.kill_anim()
        self._draw_maze()

    def _on_slider(self, val: str):
        """Slider for exploration steps (deprecated)."""
        pass # UI control removed

    def animate_search(self):
        """does the animation for exploration"""
        if self._animating:
            return
        if not self.exploration_order:
            return
        
        self._animating = True
        
        def step():
            if not self._animating or self.view_mode != "exploration":
                self._animating = False
                return
            
            n = len(self.exploration_order)
            if n == 0:
                self._animating = False
                return

            # Dynamic speed: process more steps for larger mazes
            steps_to_jump = 1
            if n > 5000: steps_to_jump = 20
            elif n > 2500: steps_to_jump = 10
            elif n > 1000: steps_to_jump = 5
            elif n > 500: steps_to_jump = 2

            self.exploration_step += steps_to_jump
            if self.exploration_step > n:
                self.exploration_step = 0 # Loop back
            
            self.step_var.set(self.exploration_step)
            self._draw_maze()
            
            # Dynamic interval: faster for large mazes
            delay = 10 if n > 1000 else 20
            self._anim_id = self.root.after(delay, step)

        self._anim_id = self.root.after(20, step)

    def kill_anim(self):
        """stops the animation"""
        self._animating = False
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
        self.exploration_step = len(self.exploration_order)
        self.step_var.set(self.exploration_step)

    def reset_anim(self):
        """resets the exploration stuff"""
        n = len(self.exploration_order)
        self.step_var.set(0)
        self.exploration_step = 0
        if self.view_mode == "exploration":
            self.animate_search()

    def get_maze_size(self) -> tuple:
        """gets w and h from the UI"""
        try:
            w = max(2, int(self.width_var.get()))
            h = max(2, int(self.height_var.get()))
            self.width_var.set(str(w))
            self.height_var.set(str(h))
            return w, h
        except ValueError:
            return 15, 15

    def make_new_maze(self):
        """makes a new maze"""
        width, height = self.get_maze_size()
        seed_str = self.seed_var.get().strip()
        seed = int(seed_str) if seed_str and seed_str.lstrip('-').isdigit() else None
        try:
            maze_type = self.maze_type_var.get().lower()
            try:
                braid_factor = float(self.braid_var_str.get())
            except ValueError:
                braid_factor = 0.3
            
            result = generate_maze(width=width, height=height, seed=seed,
                                   maze_type=maze_type, braid_factor=braid_factor)
            self.maze_result = result
            self.matrix = result.matrix
            self.start = result.start
            self.goal = result.goal
            self.current_path = []
            self.exploration_order = []
            self.all_results = {}
            self.executed_algorithms = set()
            self.view_title.configure(text="Maze View")
            self.reset_anim()
            self.view_var.set("original")
            self.view_mode = "original"
            self._draw_maze()
            self._refresh_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def get_mdp_stuff(self) -> tuple:
        """gets mdp params from entries"""
        try:
            gamma = float(self.gamma_var.get())
            epsilon = float(self.epsilon_var.get())
            reward = float(self.reward_var.get())
            return max(0.01, min(0.9999, gamma)), max(1e-12, epsilon), reward
        except ValueError:
            return 0.99, 1e-6, -1.0


    def _show_summary(self, text: str):
        """Show a message in the bottom text area."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, text)
        self.summary_text.config(state=tk.DISABLED)

    def run_solver(self, algorithm: str):
        """runs an algo in the background"""
        if not self.matrix:
            messagebox.showinfo("Info", "Generate a maze first.")
            return
        
        self.status_label.config(text=f"Running {algorithm}...", foreground="#3b82f6")
        self.progress.config(mode='indeterminate')
        self.progress.start()
        self.root.update_idletasks()
        
        def run():
            gamma, epsilon, reward = self.get_mdp_stuff()
            try:
                if algorithm == "Value Iteration":
                    result = calculate_values(self.matrix, self.start, self.goal, gamma=gamma, epsilon=epsilon, step_reward=reward)
                elif algorithm == "Policy Iteration":
                    result = calculate_policy(self.matrix, self.start, self.goal, gamma=gamma, epsilon=epsilon, step_reward=reward)

                else:
                    result = ALGORITHMS[algorithm](self.matrix, self.start, self.goal)
                
                self.root.after(0, lambda: self.show_results(algorithm, result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self._stop_loading)

        threading.Thread(target=run, daemon=True).start()

    def _stop_loading(self):
        """Reset the progress bar once work is done."""
        self.progress.stop()
        self.progress.config(mode='determinate', value=0)
        self.status_label.config(text="Ready", foreground="#64748b")

    def show_results(self, algorithm, result):
        """shows what the algo did"""
        self._store_result(algorithm, result)
        
        # Calculate/Update optimality gaps
        bfs_res = self.all_results.get("BFS")
        if bfs_res and bfs_res.get("solved"):
            # Update current result gap
            if result.get("solved"):
                result["gap"] = result["path_length"] - bfs_res["path_length"]
            
            # If we just ran BFS, update gaps for all OTHER already-run algorithms
            if algorithm == "BFS":
                for name, other_res in self.all_results.items():
                    if name != "BFS" and other_res.get("solved"):
                        other_res["gap"] = other_res["path_length"] - bfs_res["path_length"]
        else:
            # BFS not run yet
            result["gap"] = 0 if algorithm == "BFS" else None

        self.current_algorithm = algorithm
        self.current_path = result.get("path", [])
        self.exploration_order = result.get("exploration_order", [])
        self.reset_anim()
        
        self.view_title.configure(text=f"Maze View - {algorithm}")
        self.view_var.set("path")
        self.view_mode = "path"
        self.exploration_step = len(self.exploration_order)
        self.step_var.set(self.exploration_step)
        if self.view_mode == "exploration":
            self._start_auto_exploration()
        
        self._update_kpi_display(result)
        self._draw_maze()
        self._refresh_table()
        self._add_to_history(result)
        
        # Track executed algorithm
        self.executed_algorithms.add(algorithm)
        
        # Check if all registered algorithms have been run
        if len(self.executed_algorithms) == len(ALGORITHMS):
            self.do_benchmark()

        # Show single-run summary
        msg = f"Results for {algorithm}:\n"
        msg += f"- Solved: {result.get('solved')}\n"
        msg += f"- Path Length: {result.get('path_length')} moves\n"
        msg += f"- Nodes Expanded: {result.get('nodes_expanded')}\n"
        msg += f"- Peak frontier size (proxy for memory): {result.get('max_frontier', 0)}\n"
        gap = result.get("gap")
        msg += f"- Optimality Gap: {gap if gap is not None else 'N/A'}\n"
        msg += f"- Runtime: {result.get('time_ms')} ms"
        
        if "gamma" in result:
            msg += f"\n- MDP Params: Discount={result['gamma']}, Convergence={result['epsilon']}"
            msg += f"\n- Iterations: {result.get('iterations')} steps"
            msg += f"\n- Rollout Eval: {'SUCCESS' if result.get('rollout_success') else 'FAILED'}"

            msg += f" | Steps: {result.get('rollout_steps')}"
            
        self._show_summary(msg)

    def do_benchmark(self):
        """saves results and makes graphs"""
        """Automatically called when all algorithms have been run for the current maze."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_path = self.exporter.save_to_csv(self.all_results, timestamp)
        plot_path = self.visualizer.plot_comparisons(self.all_results, timestamp)
        scale_path = self._save_scalability_snapshot()
        
        conclusion = self.get_final_words()
        
        messagebox.showinfo("Benchmark Saved", "Per-run benchmark saved. Use 'Generate Report' to build multi-size comparison charts.")
        self._show_summary(
            f"Benchmark Complete!\n\n"
            f"Run CSV saved: {csv_path}\n"
            f"Run visualization saved: {plot_path}\n"
            f"Scalability dataset updated: {scale_path}\n\n"
            f"Analysis & Conclusion:\n{conclusion}"
        )

    def _save_scalability_snapshot(self) -> str:
        """Upsert current all-algorithms result into the scalability CSV."""
        if not self.all_results or not self.maze_result:
            return str(SCALABILITY_FILE)

        def canonical_algorithm(name: str) -> str:
            alias = {
                "A* (Manhattan)": "A* Manhattan",
                "A* (Euclidean)": "A* Euclidean",
            }
            return alias.get(name, name)

        headers = [
            "Maze Size",
            "Maze Type",
            "Paradigm",
            "Algorithm",
            "Path Length",
            "Expanded States",
            "Peak frontier size (proxy for memory)",
            "Solution Quality",
            "Iterations",
            "Discount Factor",
            "Convergence Threshold",
            "Runtime (ms)",
        ]

        SCALABILITY_FILE.parent.mkdir(parents=True, exist_ok=True)

        existing_rows = []
        if SCALABILITY_FILE.exists():
            with open(SCALABILITY_FILE, newline="") as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)

        maze_size = f"{self.maze_result.width}x{self.maze_result.height}"
        maze_type = self.maze_result.maze_type.capitalize()
        bfs_result = self.all_results.get("BFS")
        bfs_len = bfs_result.get("path_length") if bfs_result and bfs_result.get("solved") else None

        new_rows = []
        for name, r in self.all_results.items():
            canonical_name = canonical_algorithm(name)
            is_mdp = "gamma" in r
            solved = bool(r.get("solved"))

            if not solved:
                quality = "Failed"
            elif bfs_len is None:
                quality = "N/A"
            elif r.get("path_length") == bfs_len:
                quality = "Optimal"
            else:
                quality = "Suboptimal"

            new_rows.append({
                "Maze Size": maze_size,
                "Maze Type": maze_type,
                "Paradigm": "MDP" if is_mdp else "Search",
                "Algorithm": canonical_name,
                "Path Length": r.get("path_length", ""),
                "Expanded States": r.get("nodes_expanded", ""),
                "Peak frontier size (proxy for memory)": r.get("max_frontier", "") if not is_mdp else "",
                "Solution Quality": quality,
                "Iterations": r.get("iterations", "") if is_mdp else "",
                "Discount Factor": r.get("gamma", "") if is_mdp else "",
                "Convergence Threshold": r.get("epsilon", "") if is_mdp else "",
                "Runtime (ms)": r.get("time_ms", ""),
            })

        replace_keys = {(row["Maze Size"], row["Maze Type"], row["Algorithm"]) for row in new_rows}
        merged_rows = [
            row for row in existing_rows
            if (
                row.get("Maze Size"),
                row.get("Maze Type"),
                canonical_algorithm(row.get("Algorithm", "")),
            ) not in replace_keys
        ]
        merged_rows.extend(new_rows)

        with open(SCALABILITY_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(merged_rows)

        return str(SCALABILITY_FILE)

    def generate_report(self):
        """Build multi-size comparison graphs from merged scalability CSV."""
        if not SCALABILITY_FILE.exists():
            messagebox.showinfo("Generate Report", "No aggregated data found yet. Run all algorithms for at least one maze first.")
            return

        try:
            outputs = generate_graphs(csv_path=SCALABILITY_FILE)
            if outputs:
                self._show_summary("Generated report charts:\n- " + "\n- ".join(outputs))
            else:
                self._show_summary("No report generated. Check whether the CSV has enough data.")
        except Exception as e:
            messagebox.showerror("Generate Report", str(e))

    def get_final_words(self):
        """picks the best algo"""
        """Analyze results and draw a conclusion about which algorithm is best."""
        if not self.all_results:
            return "No data to analyze."
            
        results = list(self.all_results.values())
        solved_results = [r for r in results if r.get("solved")]
        
        if not solved_results:
            return "No algorithm was able to solve this maze."
            
        fastest = min(solved_results, key=lambda x: x['time_ms'])
        most_efficient = min(solved_results, key=lambda x: x['nodes_expanded'])
        shortest_path = min(solved_results, key=lambda x: x['path_length'])
        
        conclusion = f"- Fastest: {fastest['algorithm']} ({fastest['time_ms']:.2f} ms)\n"
        conclusion += f"- Most Memory Efficient: {most_efficient['algorithm']} ({most_efficient['nodes_expanded']} nodes expanded)\n"
        conclusion += f"- Optimal Path: {shortest_path['algorithm']} ({shortest_path['path_length']} steps)\n\n"
        
        # Logic for "Perfect Algorithm Under Condition"
        if len(self.matrix) * len(self.matrix[0]) > 2500: # Large maze
             conclusion += "Recommendation: For large mazes, A* or BFS are generally more efficient than MDP solvers which can take significant time to converge.\n"
        else:
             conclusion += "Recommendation: For smaller mazes, MDP solvers (Value/Policy Iteration) provide optimal policies for the entire state space, while A* is the best for a single path.\n"
             
        if any("Iteration" in r['algorithm'] for r in solved_results):
             conclusion += "Note: MDP algorithms (Iteration) are perfect when you need a resilient policy across the whole maze, not just a single path."
             
        return conclusion

    def _update_kpi_display(self, r: dict):
        """Update the metrics labels at the top of the maze view."""
        self.kpi_labels["time"].configure(text=f"{r.get('time_ms', 0):.2f} ms")
        self.kpi_labels["nodes"].configure(text=str(r.get("nodes_expanded", r.get("nodes_explored", "--"))))
        self.kpi_labels["path"].configure(text=f"{r.get('path_length', 0)} moves")
        conv = f"{r['iterations']} iter" if "iterations" in r else "N/A"
        self.kpi_labels["converge"].configure(text=conv)

    def _on_run_all(self):
        """Run all registered algorithms sequentially."""
        if not self.matrix:
            messagebox.showinfo("Info", "Generate a maze first.")
            return

        to_run = list(ALGORITHMS.keys())
        self.progress.config(mode='determinate', value=0, maximum=len(to_run))
        self.status_label.config(text="Running All...", foreground="#3b82f6")
        self.root.update_idletasks()
        
        def run():
            gamma, epsilon, reward = self.get_mdp_stuff()
            batch_results = []
            for i, alg in enumerate(to_run):
                self.root.after(0, lambda v=i, a=alg: (self.progress.config(value=v), self.status_label.config(text=f"Running {a}...")))
                try:
                    if alg == "Value Iteration":
                        res = calculate_values(self.matrix, self.start, self.goal, gamma=gamma, epsilon=epsilon, step_reward=reward)
                    elif alg == "Policy Iteration":
                        res = calculate_policy(self.matrix, self.start, self.goal, gamma=gamma, epsilon=epsilon, step_reward=reward)

                    else:
                        res = ALGORITHMS[alg](self.matrix, self.start, self.goal)
                    batch_results.append(res)
                    self._store_result(alg, res)
                    self.root.after(0, lambda a=alg, r=res: self.show_results(a, r))
                except Exception as e:
                    self.root.after(0, lambda err=e, a=alg: messagebox.showerror("Error", f"Failed {a}: {err}"))

            self.root.after(0, self._stop_loading)
            self.root.after(0, lambda: self._display_batch_summary(batch_results))

        threading.Thread(target=run, daemon=True).start()

    def _display_batch_summary(self, results):
        """Show a summary message after running 'Run All'."""
        if not results: return
        n = len(results)
        avg_time = sum(r['time_ms'] for r in results) / n
        avg_path = sum(r['path_length'] for r in results if r['solved']) / n
        avg_frontier = sum(r.get('max_frontier', 0) for r in results) / n
        gaps = [r['gap'] for r in results if r.get('gap') is not None]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        summary = f"Evaluation Results (Batch of {n} algorithms):\n"
        summary += f"- Avg Runtime: {avg_time:.2f} ms | Avg Gap: {avg_gap:.1f}\n"
        summary += f"- Avg Path: {avg_path:.1f} cells | Avg Peak frontier size (proxy for memory): {avg_frontier:.1f}\n"
        
        mdp_results = [r for r in results if "gamma" in r]
        if mdp_results:
            g, e = mdp_results[0]["gamma"], mdp_results[0]["epsilon"]
            summary += f"- MDP: Discount={g}, Convergence={e}\n"


        summary += f"- Best Performer (Time): {min(results, key=lambda x: x['time_ms'])['algorithm']}\n"
        summary += f"- Best Performer (Path): {min([r for r in results if r['solved']], key=lambda x: x['path_length'])['algorithm']}"
        
        self._show_summary(summary)

    def _store_result(self, name: str, result: dict):
        """Store a single algorithm's results for the current maze."""
        result["width"] = self.maze_result.width if self.maze_result else 0
        result["height"] = self.maze_result.height if self.maze_result else 0
        self.all_results[name] = result

    def _refresh_table(self):
        """Update the comparison table with all executed results."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        for name, r in self.all_results.items():
            is_mdp = "gamma" in r
            
            # Gap Logic
            gap = r.get("gap")
            gap_val = gap if gap is not None else "Run BFS"
            if gap == 0: gap_val = "Optimal"
            if not r.get("solved"): gap_val = "N/A"
            
            # Rollout Logic
            rollout = "N/A"
            if is_mdp:
                succ = "✓" if r.get("rollout_success") else "✗"
                rollout = f"{succ} ({r.get('rollout_steps', 0)})"

            self.tree.insert("", tk.END, values=(
                r.get("algorithm", name),
                "Yes" if r.get("solved") else "No",
                r.get("path_length", "-"),
                r.get("nodes_expanded", "-"),
                r.get("max_frontier", "N/A") if not is_mdp else "N/A",
                gap_val,
                r.get("iterations", "N/A") if is_mdp else "N/A",
                r.get("gamma", "N/A") if is_mdp else "N/A",
                r.get("epsilon", "N/A") if is_mdp else "N/A",
                rollout,
                f"{r.get('time_ms', 0):.2f}",
            ))

    def select_algo(self, event):
        """when a row is clicked"""
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        if not vals:
            return
        alg_name = vals[0]
        r = self.all_results.get(alg_name) or next(
            (v for v in self.all_results.values() if v.get("algorithm") == alg_name), None
        )
        if r:
            self.current_path = r.get("path", [])
            self.current_algorithm = r.get("algorithm", alg_name)
            self.exploration_order = r.get("exploration_order", [])
            self.view_title.configure(text=f"Maze View - {self.current_algorithm}")
            self.reset_anim()
            n = len(self.exploration_order)
            self.view_var.set("path")
            self.view_mode = "path"
            self.exploration_step = n
            self.step_var.set(n)
            if self.view_mode == "exploration":
                self.animate_search()
            self._update_kpi_display(r)
            self._draw_maze()
            
            # Rebuild detailed summary for history recall
            msg = f"Results for {self.current_algorithm}:\n"
            msg += f"- Solved: {r.get('solved')}\n"
            msg += f"- Path Length: {r.get('path_length')} moves\n"
            msg += f"- Nodes Expanded: {r.get('nodes_expanded')}\n"
            msg += f"- Peak frontier size (proxy for memory): {r.get('max_frontier', 0)}\n"
            gap = r.get("gap")
            msg += f"- Optimality Gap: {gap if gap is not None else 'N/A'}\n"
            msg += f"- Runtime: {r.get('time_ms')} ms"
            
            if "gamma" in r:
                msg += f"\n- MDP Params: Discount={r['gamma']}, Convergence={r['epsilon']}"
                msg += f"\n- Iterations: {r.get('iterations')} steps"
                msg += f"\n- Rollout Eval: {'SUCCESS' if r.get('rollout_success') else 'FAILED'}"

                msg += f" | Steps: {r.get('rollout_steps')}"
                
            self._show_summary(msg)

    def _show_details(self, r: dict):
        """Show full details of an algorithm's run (unused?)."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        lines = [
            f"Algorithm: {r.get('algorithm', '?')}",
            f"Solution found: {r.get('solved', False)}",
            f"Path length: {r.get('path_length', 0)}",
            f"Expanded states: {r.get('nodes_explored', 0)}",
            f"Runtime: {r.get('time_ms', 0):.4f} ms",
        ]
        if "gamma" in r:
            lines.extend([
                f"Discount: {r.get('gamma')}",
                f"Convergence Thr: {r.get('epsilon')}",
                f"Iterations: {r.get('iterations', 0)}",

                f"Rollout success: {r.get('rollout_success', False)}",
                f"Rollout steps: {r.get('rollout_steps', 0)}",
            ])
            if "policy" in r:
                policy = r["policy"]
                n_states = len([s for s in policy if policy[s] >= 0])
                lines.append(f"Policy: {n_states} states with actions")
        self.details_text.insert(tk.END, "\n".join(lines))
        self.details_text.config(state=tk.DISABLED)

    def _add_to_history(self, result: dict):
        """Add a run to the execution history file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "algorithm": result.get("algorithm", "?"),
            "solved": result.get("solved", False),
            "path_length": result.get("path_length", 0),
            "nodes_expanded": result.get("nodes_expanded", 0),
            "max_frontier": result.get("max_frontier", 0),
            "gap": result.get("gap"),
            "time_ms": result.get("time_ms", 0),
            "iterations": result.get("iterations"),
            "gamma": result.get("gamma"),
            "epsilon": result.get("epsilon"),
            "rollout_success": result.get("rollout_success"),
            "rollout_steps": result.get("rollout_steps"),
        }
        self.execution_history.append(entry)
        save_history(self.execution_history)
        self._refresh_history_display()

    def _refresh_history_display(self):
        """Update the history text box in the sidebar."""
        if not hasattr(self, 'history_text'): return
        self.history_text.delete(1.0, tk.END)
        for i, h in enumerate(reversed(self.execution_history[-15:]), 1):
            ts = h.get("timestamp", "")[:16].replace("T", " ")
            alg = h.get("algorithm", "?")
            p = h.get("path_length", "?")
            n = h.get("nodes_expanded", h.get("nodes_explored", "?"))
            g = h.get("gap")
            gap_str = f" g:{g}" if g is not None else ""
            self.history_text.insert(tk.END, f"{i}. {ts} {alg} p:{p} n:{n}{gap_str}\n")
        if not self.execution_history:
            self.history_text.insert(tk.END, "No runs yet.")

    def _clear_history(self):
        """Delete all items from the execution history."""
        self.execution_history = []
        save_history(self.execution_history)
        self._refresh_history_display()

    def _draw_maze(self):
        """Main rendering function that draws walls, cells, and paths on the canvas."""
        self.canvas.delete("all")
        if not self.matrix:
            return
        rows, cols = len(self.matrix), len(self.matrix[0])
        cw = self.canvas.winfo_width() or 400
        ch = self.canvas.winfo_height() or 350
        cell_w = min(cw / cols, ch / rows, 40)
        ox = (cw - cols * cell_w) / 2
        oy = (ch - rows * cell_w) / 2

        mode = self.view_var.get() if hasattr(self, "view_var") else "original"
        res = self.all_results.get(self.current_algorithm, {})
        explored_so_far = set(self.exploration_order[: self.exploration_step]) if self.exploration_order else set()
        current_cell = self.exploration_order[self.exploration_step - 1] if self.exploration_step > 0 and self.exploration_step <= len(self.exploration_order) else None
        path_set = set(self.current_path) if self.current_path else set()

        # Heatmap data preparation
        v_dict = res.get("values", {})
        v_min, v_max = 0, 0
        if v_dict:
            v_vals = [v for k, v in v_dict.items() if k != self.goal]
            if v_vals:
                v_min, v_max = min(v_vals), max(v_vals)

        for y in range(rows):
            for x in range(cols):
                wx, wy = ox + x * cell_w, oy + y * cell_w
                if self.matrix[y][x] == "1":
                    self.canvas.create_rectangle(wx, wy, wx + cell_w, wy + cell_w, fill="#94a3b8", outline="#64748b")
                    continue

                # Default tile style
                fill, out = "#ffffff", "#cbd5e1"
                
                # Apply styles based on mode and algorithm
                if mode == "original":
                    pass
                elif mode == "exploration":
                    if (x, y) == current_cell:
                        fill, out = "#f59e0b", "#d97706"
                    elif (x, y) in explored_so_far:
                        fill, out = "#fed7aa", "#fdba74"
                else: # mode == "path"
                    if self.current_algorithm == "Value Iteration" and (x, y) in v_dict:
                        # Draw Heatmap
                        if (x, y) == self.goal:
                            fill, out = "#ef4444", "#dc2626"
                        else:
                            val = v_dict[(x, y)]
                            fill = self._get_heatmap_color(val, v_min, v_max)
                            out = fill
                    elif self.current_algorithm == "Policy Iteration" and (x, y) in res.get("policy", {}):
                        # Draw Policy
                        if (x, y) == self.goal:
                            fill, out = "#ef4444", "#dc2626"
                        elif (x, y) in path_set:
                            # Show rollout path for illustrative purposes
                            fill, out = "#3b82f6", "#2563eb"
                        else:
                            fill, out = "#ffffff", "#cbd5e1"
                    else:
                        if (x, y) in path_set:
                            fill, out = "#3b82f6", "#2563eb"
                        elif (x, y) in explored_so_far:
                            fill, out = "#e0e7ff", "#c7d2fe"

                # Start state override
                if (x, y) == self.start:
                    fill, out = "#22c55e", "#16a34a"
                
                # Goal state override (if logic above didn't handle it)
                if (x, y) == self.goal:
                     fill, out = "#ef4444", "#dc2626"

                self.canvas.create_rectangle(wx, wy, wx + cell_w, wy + cell_w, fill=fill, outline=out)

                # Draw arrows for Policy Iteration
                if mode == "path" and self.current_algorithm == "Policy Iteration":
                    policy = res.get("policy", {})
                    if (x, y) in policy and policy[(x, y)] != -1:
                        self._draw_arrow(wx, wy, cell_w, policy[(x, y)], "#1e293b" if (x, y) not in path_set else "#ffffff")

    def _get_heatmap_color(self, val, v_min, v_max):
        """Calculate a color for the heatmap based on the state's value."""
        if v_max == v_min:
            return "#eff6ff"
        # Scale value to [0, 1]
        t = (val - v_min) / (v_max - v_min)
        # Use a blue-to-red or light-to-dark gradient
        # Blue gradient: 239, 246, 255 (light) to 30, 64, 175 (dark)
        r = int(239 - t * (239 - 30))
        g = int(246 - t * (246 - 64))
        b = int(255 - t * (255 - 175))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw_arrow(self, x, y, size, action, color):
        """Draw an arrow showing the best move for a state."""
        # action: 0=N, 1=S, 2=W, 3=E
        pad = size * 0.2
        cx, cy = x + size/2, y + size/2
        
        if action == 0: # North
            coords = [cx, y + pad, cx - size/4, cy, cx + size/4, cy]
        elif action == 1: # South
            coords = [cx, y + size - pad, cx - size/4, cy, cx + size/4, cy]
        elif action == 2: # West
            coords = [x + pad, cy, cx, cy - size/4, cx, cy + size/4]
        elif action == 3: # East
            coords = [x + size - pad, cy, cx, cy - size/4, cx, cy + size/4]
        else:
            return
            
        self.canvas.create_line(coords[0], coords[1], cx, cy, fill=color, width=1)
        self.canvas.create_polygon(coords, fill=color)


    def run(self):
        """Starts the application and opens the window."""
        self.root.after(100, self.make_new_maze)
        self.root.mainloop()


if __name__ == "__main__":
    MazeApp().run()

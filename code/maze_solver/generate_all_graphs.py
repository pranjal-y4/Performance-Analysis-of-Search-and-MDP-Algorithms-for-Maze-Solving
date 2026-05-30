import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

"""
Script to create 5 different charts from the maze results.
"""

def load_data(csv_path):
    """Load the maze data from a CSV file."""
    df = pd.read_csv(csv_path)
    # Clean up column names in case they have spaces
    df.columns = [c.strip() for c in df.columns]
    return df

def setup_filters(df, algorithms, maze_sizes):
    """Keep only the algorithms and maze sizes we want, and sort them."""
    df = df[df["Algorithm"].isin(algorithms)]
    df = df[df["Maze Size"].isin(maze_sizes)]
    # Make sure maze sizes stay in order: 10x10, then 50x50, then 100x100
    df["Maze Size"] = pd.Categorical(df["Maze Size"], categories=maze_sizes, ordered=True)
    return df.sort_values(by=["Maze Size", "Algorithm"])


def normalize_algorithm_names(df):
    """Normalize algorithm labels from app/export variants."""
    alias_map = {
        "A* (Manhattan)": "A* Manhattan",
        "A* (Euclidean)": "A* Euclidean",
    }
    df = df.copy()
    df["Algorithm"] = df["Algorithm"].replace(alias_map)
    return df


def sort_maze_sizes(sizes):
    """Sort sizes like 10x10, 50x50, 100x100 numerically."""
    def key_fn(size):
        try:
            w, h = size.lower().split("x")
            return int(w) * int(h), int(w), int(h)
        except Exception:
            return (10**12, 10**6, 10**6)
    return sorted(sizes, key=key_fn)


def aggregate_for_plots(df):
    """Keep latest run per maze size + algorithm for stable plots."""
    df = df.copy()
    df["_row_order"] = range(len(df))

    group_cols = ["Maze Size", "Paradigm", "Algorithm"]
    out = df.sort_values("_row_order").groupby(group_cols, as_index=False).tail(1)
    out = out.drop(columns=["_row_order"])
    return out

def plot_runtime_scalability(df, algorithms, output_path):
    """Line chart showing how runtime grows with maze size."""
    plt.figure(figsize=(10, 7))
    for alg in algorithms:
        alg_data = df[df["Algorithm"] == alg].sort_values("Maze Size")
        if not alg_data.empty:
            plt.plot(alg_data["Maze Size"], alg_data["Runtime (ms)"], marker='o', label=alg, linewidth=2)
    
    plt.yscale('log')
    plt.xlabel("Maze Size")
    plt.ylabel("Runtime (ms) (Log Scale)")
    plt.title("Runtime Scalability Across Maze Sizes")
    plt.legend(title="Algorithm", loc="upper left")
    plt.grid(True, which="both", linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def plot_state_expansion(df, algorithms, maze_sizes, output_path):
    """Bar chart showing how many nodes each algorithm explored."""
    x = np.arange(len(maze_sizes))
    width = 0.12

    fig, ax = plt.subplots(figsize=(12, 8))
    for i, alg in enumerate(algorithms):
        alg_data = df[df["Algorithm"] == alg]
        alg_values = [alg_data[alg_data["Maze Size"] == size]["Expanded States"].iloc[0] 
                      if not alg_data[alg_data["Maze Size"] == size].empty else 0 
                      for size in maze_sizes]
        
        offset = (i - (len(algorithms) - 1) / 2) * width
        ax.bar(x + offset, alg_values, width, label=alg)

    ax.set_ylabel('Expanded States (Log Scale)')
    ax.set_xlabel('Maze Size')
    ax.set_title('State Space Expansion as Maze Size Increases')
    ax.set_xticks(x)
    ax.set_xticklabels(maze_sizes)
    ax.set_yscale('log')
    ax.legend(title="Algorithm")
    ax.grid(True, axis='y', which="both", linestyle='--', alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def plot_path_length(df, algorithms, maze_sizes, output_path):
    """Bar chart comparing the lengths of paths found by each algorithm."""
    x = np.arange(len(algorithms))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 8))
    for i, size in enumerate(maze_sizes):
        size_data = df[df["Maze Size"] == size]
        path_lengths = [size_data[size_data["Algorithm"] == alg]["Path Length"].iloc[0]
                        if not size_data[size_data["Algorithm"] == alg].empty else 0
                        for alg in algorithms]
        
        offset = (i - (len(maze_sizes) - 1) / 2) * width
        ax.bar(x + offset, path_lengths, width, label=size)

    ax.set_ylabel('Path Length')
    ax.set_xlabel('Algorithm')
    ax.set_title('Path Length Comparison Across Algorithms and Maze Sizes')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend(title="Maze Size")
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def plot_mdp_scatter(df, output_path):
    """Scatter plot show iterations vs runtime for MDP algorithms."""
    mdp_df = df[df["Paradigm"] == "MDP"].copy()
    if mdp_df.empty:
        return

    plt.figure(figsize=(10, 7))
    colors = {"Value Iteration": "blue", "Policy Iteration": "orange"}
    markers = {"Value Iteration": "o", "Policy Iteration": "s"}

    for alg in ["Value Iteration", "Policy Iteration"]:
        alg_data = mdp_df[mdp_df["Algorithm"] == alg]
        if not alg_data.empty:
            plt.scatter(alg_data["Iterations"], alg_data["Runtime (ms)"], 
                        c=colors.get(alg), marker=markers.get(alg), label=alg, s=100)
            for _, row in alg_data.iterrows():
                plt.text(row["Iterations"], row["Runtime (ms)"], f' {row["Maze Size"]}', verticalalignment='bottom')

    plt.xlabel("Number of Iterations")
    plt.ylabel("Runtime (ms)")
    plt.title("Iterations vs Runtime for MDP Algorithms")
    plt.legend(title="Algorithm")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def plot_paradigm_comparison(df, maze_sizes, output_path):
    """Chart comparing Search vs MDP runtime for each maze size."""
    fig, axes = plt.subplots(1, len(maze_sizes), figsize=(5 * len(maze_sizes), 6), sharey=True)
    paradigms = ["Search", "MDP"]
    colors = ["skyblue", "salmon"]

    if len(maze_sizes) == 1:
        axes = [axes]

    for i, size in enumerate(maze_sizes):
        size_data = df[df["Maze Size"] == size]
        ax = axes[i]
        
        for p_idx, paradigm in enumerate(paradigms):
            p_data = size_data[size_data["Paradigm"] == paradigm]
            if not p_data.empty:
                algs = p_data["Algorithm"].tolist()
                runtimes = p_data["Runtime (ms)"].tolist()
                x_pos = np.arange(len(algs)) + (p_idx * 5)
                ax.bar(x_pos, runtimes, color=colors[p_idx], label=paradigm if i == 0 else "")
                for x, label in zip(x_pos, algs):
                    ax.text(x, 0.1, label, rotation=90, ha='center', va='bottom', fontsize=8)

        ax.set_title(f"Maze Size: {size}")
        ax.set_yscale('log')
        ax.set_xticks([])
        if i == 0:
            ax.set_ylabel("Runtime (ms) (Log Scale)")
    
    fig.suptitle("Search vs MDP Runtime Comparison Across Maze Sizes", fontsize=16)
    fig.legend(title="Paradigm", loc="upper right")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def generate_graphs(csv_path=None, output_dir=None):
    """Main function to generate every chart."""
    base_dir = Path(__file__).parent
    csv_path = Path(csv_path) if csv_path else base_dir / "data" / "maze_scalability_results_clean.csv"
    output_dir = Path(output_dir) if output_dir else base_dir / "visuals"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return []

    df = load_data(csv_path)
    df = normalize_algorithm_names(df)
    df = aggregate_for_plots(df)

    preferred_algs = ["DFS", "BFS", "A* Manhattan", "A* Euclidean", "Value Iteration", "Policy Iteration"]
    present = list(pd.unique(df["Algorithm"]))
    algs = [a for a in preferred_algs if a in present]
    if not algs:
        algs = present

    sizes = sort_maze_sizes(list(pd.unique(df["Maze Size"])))
    df = setup_filters(df, algs, sizes)

    out_paths = [
        output_dir / "scalability_graph.png",
        output_dir / "state_expansion_graph.png",
        output_dir / "path_length_comparison.png",
        output_dir / "mdp_iterations_vs_runtime.png",
        output_dir / "paradigm_comparison.png",
    ]

    plot_runtime_scalability(df, algs, out_paths[0])
    plot_state_expansion(df, algs, sizes, out_paths[1])
    plot_path_length(df, algs, sizes, out_paths[2])
    plot_mdp_scatter(df, out_paths[3])
    plot_paradigm_comparison(df, sizes, out_paths[4])

    return [str(p) for p in out_paths]

if __name__ == "__main__":
    generate_graphs()

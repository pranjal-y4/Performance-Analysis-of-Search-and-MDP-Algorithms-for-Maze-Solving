import matplotlib.pyplot as plt
import os
from pathlib import Path

class Visualizer:
    """class for making plots and stuff"""

    def __init__(self, out_dir: str | None = None):
        """make sure the folder exists"""
        default_dir = Path(__file__).parent / "visuals"
        self.out_dir = Path(out_dir) if out_dir else default_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def plot_comparisons(self, data: dict, ts: str) -> str:
        """makes some charts to show how algos compare"""
        algos = list(data.keys())
        times = [r.get("time_ms", 0) for r in data.values()]
        nodes = [r.get("nodes_expanded", 0) for r in data.values()]
        paths = [r.get("path_length", 0) for r in data.values()]

        size_label = "Unknown size"
        if data:
            first = next(iter(data.values()))
            w = first.get("width")
            h = first.get("height")
            if w and h:
                size_label = f"{w}x{h}"

        # 3 charts in one row
        fig, ax = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f"Results Comparison | Maze: {size_label} | {ts}", fontsize=16, fontweight="bold")
        fig.text(0.5, 0.965, f"Maze Size: {size_label}", ha="center", va="center", fontsize=11)

        # time bar chart
        ax[0].bar(algos, times, color='skyblue', alpha=0.7)
        ax[0].set_title("run time (ms)")
        ax[0].set_ylabel("ms")
        ax[0].tick_params(axis='x', rotation=45)

        # nodes line chart
        ax[1].plot(algos, nodes, marker='o', color='salmon', linewidth=2)
        ax[1].set_title("states explored")
        ax[1].set_ylabel("count")
        ax[1].tick_params(axis='x', rotation=45)
        ax[1].grid(True, linestyle='--', alpha=0.7)

        # path length line chart
        ax[2].plot(algos, paths, marker='s', color='lightgreen', linewidth=2)
        ax[2].set_title("path length")
        ax[2].set_ylabel("len")
        ax[2].tick_params(axis='x', rotation=45)
        ax[2].grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
        
        # save it
        safe_size = size_label.replace(" ", "_")
        fname = f"Visualization_{safe_size}_{ts}.png"
        fpath = self.out_dir / fname
        plt.savefig(fpath)
        plt.close()
        
        return str(fpath)

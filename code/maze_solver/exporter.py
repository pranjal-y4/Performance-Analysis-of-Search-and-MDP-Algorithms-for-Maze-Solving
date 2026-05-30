import csv
import os
from datetime import datetime
from pathlib import Path

class Exporter:
    """class to save results to files"""
    
    def __init__(self, out_dir: str | None = None):
        """creates output folder if not there"""
        default_dir = Path(__file__).parent / "visuals"
        self.out_dir = Path(out_dir) if out_dir else default_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def save_to_csv(self, results: dict, ts: str) -> str:
        """saves results in a csv file"""
        fname = f"table_results_{ts}.csv"
        fpath = self.out_dir / fname
        
        # get data into a list of dicts
        data_list = []
        for name, r in results.items():
            data_list.append({
                "Algorithm": name,
                "Solved": r.get("solved", False),
                "Path Length": r.get("path_length", 0),
                "Time (ms)": r.get("time_ms", 0),
                "Nodes Expanded": r.get("nodes_expanded", 0),
                "Peak frontier size (proxy for memory)": r.get("max_frontier", 0),
                "Iterations/Steps": r.get("iterations", r.get("rollout_steps", 0))
            })
            
        if not data_list:
            return ""

        # csv headers
        headers = ["Algorithm", "Solved", "Path Length", "Time (ms)", "Nodes Expanded", "Peak frontier size (proxy for memory)", "Iterations/Steps"]
        
        # write file
        with open(fpath, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(data_list)
            
        return str(fpath)

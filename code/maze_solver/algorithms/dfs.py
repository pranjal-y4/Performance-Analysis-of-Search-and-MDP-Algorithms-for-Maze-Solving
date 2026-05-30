import time
from typing import List, Tuple, Dict, Any
from .utils import find_neighbors, format_output

def run_dfs(matrix: List[str], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """simple dfs search"""
    t0 = time.perf_counter()
    path, seen = [], []
    visited, parent = {start}, {start: None}
    stack = [start]
    max_s = 1

    while stack:
        max_s = max(max_s, len(stack))
        x, y = stack.pop()
        seen.append((x, y))
        
        # goal check
        if (x, y) == goal:
            curr = goal
            while curr:
                path.append(curr)
                curr = parent[curr]
            path.reverse()
            break
            
        # neighbors to stack
        for n in find_neighbors(matrix, x, y):
            if n not in visited:
                visited.add(n)
                parent[n] = (x, y)
                stack.append(n)

    return format_output("DFS", path, len(seen), t0, seen, max_s)

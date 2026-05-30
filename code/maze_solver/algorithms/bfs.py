import time
from collections import deque
from typing import List, Tuple, Dict, Any
from .utils import find_neighbors, format_output

def run_bfs(matrix: List[str], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """standard bfs search for the maze"""
    t0 = time.perf_counter()
    path, seen = [], []
    visited, parent = {start}, {start: None}
    q = deque([start])
    max_q = 1

    while q:
        max_q = max(max_q, len(q))
        x, y = q.popleft()
        seen.append((x, y))
        
        # if goal, build path back
        if (x, y) == goal:
            curr = goal
            while curr:
                path.append(curr)
                curr = parent[curr]
            path.reverse()
            break
            
        # check all neighbors
        for n in find_neighbors(matrix, x, y):
            if n not in visited:
                visited.add(n)
                parent[n] = (x, y)
                q.append(n)

    return format_output("BFS", path, len(seen), t0, seen, max_q)

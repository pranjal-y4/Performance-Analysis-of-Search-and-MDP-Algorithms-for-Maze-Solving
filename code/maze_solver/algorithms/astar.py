import time
import heapq
from typing import List, Tuple, Dict, Any, Callable
from .utils import find_neighbors, format_output, dist_manhattan, dist_euclidean

def run_astar(
    matrix: List[str],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    heuristic: Callable[[int, int, int, int], float],
    name: str,
) -> Dict[str, Any]:
    """does the astar search with a heuristic"""
    gx, gy = goal
    t0 = time.perf_counter()
    path, seen = [], []
    
    # pq: (f, neg_g, g, (x, y))
    queue = [(0 + heuristic(start[0], start[1], gx, gy), 0, 0, start)]
    parent, g_values = {start: None}, {start: 0}
    max_q = 1

    while queue:
        max_q = max(max_q, len(queue))
        f, neg_g, g, (x, y) = heapq.heappop(queue)
        
        # skip if we found better path
        if g > g_values.get((x, y), float('inf')):
            continue
            
        seen.append((x, y))
        if (x, y) == goal:
            curr = goal
            while curr:
                path.append(curr)
                curr = parent[curr]
            path.reverse()
            break
            
        for n in find_neighbors(matrix, x, y):
            new_g = g + 1
            if n not in g_values or new_g < g_values[n]:
                g_values[n] = new_g
                parent[n] = (x, y)
                h = heuristic(n[0], n[1], gx, gy)
                # tie break with neg g
                heapq.heappush(queue, (new_g + h, -new_g, new_g, n))

    return format_output(name, path, len(seen), t0, seen, max_q)

def run_astar_man(matrix: List[str], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """astar with manhattan"""
    return run_astar(matrix, start, goal, dist_manhattan, "A* (Manhattan)")

def run_astar_euc(matrix: List[str], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """astar with euclidean"""
    return run_astar(matrix, start, goal, dist_euclidean, "A* (Euclidean)")

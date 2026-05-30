import time
import math
from typing import List, Tuple, Dict, Any, Callable

# directions: N, S, W, E (dx, dy)
ORTHOGONAL = [(0, -1), (0, 1), (-1, 0), (1, 0)]
ACTION_NAMES = ["N", "S", "W", "E"]


def is_walkable(cell: Any) -> bool:
    """returns True when a maze cell should be treated as corridor"""
    if isinstance(cell, bool) or cell is None:
        return False

    if isinstance(cell, (int, float)):
        return cell == 0

    if isinstance(cell, str):
        if cell == " ":
            return True

        token = cell.strip().lower()
        if token in {"0", ".", "s", "g", "start", "goal", "free", "path", "open"}:
            return True
        if token in {"1", "#", "x", "wall", "blocked"}:
            return False

    return False

def find_neighbors(matrix: List[str], x: int, y: int) -> List[Tuple[int, int]]:
    """gets neighbors that we can walk on"""
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    res = []
    
    for dx, dy in ORTHOGONAL:
        nx, ny = x + dx, y + dy
        # check bounds and if wall
        if 0 <= nx < cols and 0 <= ny < rows and is_walkable(matrix[ny][nx]):
            res.append((nx, ny))
    return res

def get_move_res(s: Tuple[int, int], a: int, matrix: List[str], rows: int, cols: int) -> Tuple[int, int]:
    """calc next state for mdp stuff. stays put if hit wall."""
    dx, dy = [(0, -1), (0, 1), (-1, 0), (1, 0)][a] # 0=N, 1=S, 2=W, 3=E
    nx, ny = s[0] + dx, s[1] + dy
    if 0 <= nx < cols and 0 <= ny < rows and is_walkable(matrix[ny][nx]):
        return (nx, ny)
    return s

def dist_manhattan(x1: int, y1: int, x2: int, y2: int) -> float:
    """manhattan dist calculation"""
    return abs(x1 - x2) + abs(y1 - y2)

def dist_euclidean(x1: int, y1: int, x2: int, y2: int) -> float:
    """euclidean dist calculation"""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def format_output(name: str, path: List, nodes_expanded: int, t0: float, exploration: List | None = None, max_frontier: int = 0) -> Dict[str, Any]:
    """helper to format the algo results into a dict"""
    elapsed = (time.perf_counter() - t0) * 1000
    p_len = max(0, len(path) - 1) if path else 0
    out = {
        "algorithm": name,
        "solved": len(path) > 0,
        "path": path,
        "path_length": p_len,
        "time_ms": round(elapsed, 4),
        "nodes_expanded": nodes_expanded,
        "max_frontier": max_frontier,
    }
    if exploration is not None:
        out["exploration_order"] = exploration
    return out

def run_path(policy: Dict, start: Tuple[int, int], goal: Tuple[int, int], next_state_fn, goal_set: set) -> Tuple[List[Tuple[int, int]], int]:
    """follows the policy to find the path"""
    path = [start]
    curr = start
    # limit steps so we don't loop forever
    limit = len(policy) * 5
    for _ in range(limit):
        if curr in goal_set:
            return path, max(0, len(path) - 1)
        a = policy.get(curr, -1)
        if a < 0:
            break
        curr = next_state_fn(curr, a)
        path.append(curr)
    return path, max(0, len(path) - 1)

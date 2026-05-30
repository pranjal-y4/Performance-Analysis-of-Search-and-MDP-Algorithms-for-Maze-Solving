import time
from typing import List, Tuple, Dict, Any
from .utils import run_path, get_move_res, is_walkable

def calculate_values(
    matrix: List[str],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    gamma: float = 0.99,
    epsilon: float = 1e-6,
    step_reward: float = -1.0,
) -> Dict[str, Any]:
    """value iteration for the maze mdp"""
    t0 = time.perf_counter()
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    
    # all walkable spots
    states = [(x, y) for y in range(rows) for x in range(cols) if is_walkable(matrix[y][x])]
    goal_set = {goal}

    assert 0 <= start[0] < cols and 0 <= start[1] < rows, "start must be inside maze bounds"
    assert 0 <= goal[0] < cols and 0 <= goal[1] < rows, "goal must be inside maze bounds"
    assert is_walkable(matrix[start[1]][start[0]]), "start must be walkable"
    assert is_walkable(matrix[goal[1]][goal[0]]), "goal must be walkable"
    assert start in states, "start must be included in walkable states"
    assert goal in states, "goal must be included in walkable states"

    def next_state(s, a):
        return get_move_res(s, a, matrix, rows, cols)

    V = {s: 0.0 for s in states}
    order = []
    seen_upd = set()
    nodes_expanded = 0
    
    it = 0
    max_it = max(1, len(states) * 10)
    converged = False
    
    # loop until values stop changing much
    while it < max_it:
        diff_max = 0
        V_new = {}
        for s in states:
            if s in goal_set:
                V_new[s] = 0.0
                continue
            
            # find best action
            best_val = float('-inf')
            for a in range(4):
                ns = next_state(s, a)
                temp = step_reward + gamma * V[ns]
                best_val = max(best_val, temp)
            V_new[s] = best_val
            nodes_expanded += 1
            
            # track change
            change = abs(V[s] - best_val)
            diff_max = max(diff_max, change)
            
            # for viz
            if change > epsilon and s not in seen_upd:
                seen_upd.add(s)
                order.append(s)
                
        V = V_new
        it += 1
        if diff_max < epsilon:
            converged = True
            break

    # make policy from values
    policy = {}
    for s in states:
        if s in goal_set:
            policy[s] = -1
            continue
        best_a, best_v = -1, float('-inf')
        for a in range(4):
            ns = next_state(s, a)
            v = step_reward + gamma * V[ns]
            if v > best_v:
                best_v = v
                best_a = a
        policy[s] = best_a

    # get path
    path, num_steps = run_path(policy, start, goal, next_state, goal_set)
    took = (time.perf_counter() - t0) * 1000
    
    return {
        "algorithm": "Value Iteration",
        "solved": len(path) > 0 and path[-1] == goal,
        "path": path,
        "path_length": num_steps,
        "time_ms": round(took, 4),
        "nodes_expanded": nodes_expanded,
        "exploration_order": order if order else path,
        "gamma": gamma,
        "epsilon": epsilon,
        "converged": converged,
        "iterations": it,
        "policy": policy,
        "values": V,
        "rollout_success": len(path) > 0 and path[-1] == goal,
        "rollout_steps": num_steps,
    }

import time
from typing import List, Tuple, Dict, Any
from .utils import run_path, get_move_res, is_walkable

def calculate_policy(
    matrix: List[str],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    gamma: float = 0.99,
    epsilon: float = 1e-6,
    step_reward: float = -1.0,
) -> Dict[str, Any]:
    """policy iteration algorithm for the maze"""
    t0 = time.perf_counter()
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    
    # get states that are walkable
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

    # start with some defaults
    policy = {s: 0 for s in states}
    policy[goal] = -1
    V = {s: 0.0 for s in states}
    order = []
    seen_upd = set()
    
    iters = 0
    upd_count = 0
    max_eval = max(1, len(states) * 10)
    max_policy_iters = 500
    converged = False

    while True:
        # loop to evaluate the current policy
        for _ in range(max_eval):
            diff_max = 0
            for s in states:
                if s in goal_set:
                    continue
                a = policy[s]
                ns = next_state(s, a)
                new_v = step_reward + gamma * V[ns]

                d = abs(V[s] - new_v)
                diff_max = max(diff_max, d)
                V[s] = new_v
                upd_count += 1
                
                # tracking for viz
                if d > epsilon and s not in seen_upd:
                    seen_upd.add(s)
                    order.append(s)

            if diff_max < epsilon:
                break

        # improve policy using the new values
        stable = True
        for s in states:
            if s in goal_set:
                continue
            upd_count += 1
            old_a = policy[s]
            best_a, best_val = -1, float('-inf')
            for a in range(4):
                ns = next_state(s, a)
                v = step_reward + gamma * V[ns]

                if v > best_val:
                    best_val = v
                    best_a = a
            
            if best_a != old_a:
                stable = False
            policy[s] = best_a
            
        iters += 1
        # stop if stable or too many loops
        if stable:
            converged = True
            break
        if iters >= max_policy_iters:
            break

    # get the path
    path, num_steps = run_path(policy, start, goal, next_state, goal_set)
    took = (time.perf_counter() - t0) * 1000
    
    return {
        "algorithm": "Policy Iteration",
        "solved": len(path) > 0 and path[-1] == goal,
        "path": path,
        "path_length": num_steps,
        "time_ms": round(took, 4),
        "nodes_expanded": upd_count,
        "exploration_order": order if order else path,
        "gamma": gamma,
        "epsilon": epsilon,
        "converged": converged,
        "iterations": iters,
        "policy": policy,
        "values": V,
        "rollout_success": len(path) > 0 and path[-1] == goal,
        "rollout_steps": num_steps,
    }

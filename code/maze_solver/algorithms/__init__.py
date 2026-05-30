from .dfs import run_dfs
from .bfs import run_bfs
from .astar import run_astar_man, run_astar_euc, run_astar
from .value_iteration import calculate_values
from .policy_iteration import calculate_policy

# export the algos here
ALGORITHMS = {
    "DFS": run_dfs,
    "BFS": run_bfs,
    "A* (Manhattan)": run_astar_man,
    "A* (Euclidean)": run_astar_euc,
    "Value Iteration": lambda m, s, g, **kwargs: calculate_values(m, s, g, **kwargs),
    "Policy Iteration": lambda m, s, g, **kwargs: calculate_policy(m, s, g, **kwargs),
}

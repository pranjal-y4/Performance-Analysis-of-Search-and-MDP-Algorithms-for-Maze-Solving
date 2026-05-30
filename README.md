# Maze Solver Project

This project is a tool to test and compare different ways to solve a maze. You can use it to see how search algorithms and MDP (Markov Decision Process) solvers perform on different maze sizes and types.

Check out this video: https://youtu.be/uF0oV2QS2Rs

## Setup and Run

### 1. Install dependencies
From the repository root:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r maze_solver/requirements.txt
```

### 2. Interactive Tool
To open the main window where you can generate mazes and solve them yourself, run:
```bash
python3 -m maze_solver.app
```
From here you can:
- Change the maze size (like 10x10 or 100x100).
- Choose between "Perfect" mazes or "Braided" mazes with loops.
- Run single solvers or hit "Run All" to compare everything at once.
- See an animation of how the solver expands or the final path found.
- After all algorithms complete for a maze, results are saved to both a per-run CSV and the merged scalability CSV (`data/maze_scalability_results_clean.csv`).
- Use the **Generate Report** button to build multi-size comparison plots from all accumulated runs.

### 3. Generate Analysis Graphs
To create the 5 detailed analysis charts (like scalability and paradigm comparison), run:
```bash
python3 -m maze_solver.generate_all_graphs
```
This will save images into the `visuals/` folder automatically.

### 4. Troubleshooting
- If `tkinter` is missing, install the Python Tk package for your OS/Python distribution.
- Run all commands from the project root (`maze-generator/`) so relative paths resolve correctly.

## Project Structure

### Main Files
- **[app.py](app.py)**: The main GUI app. It handles the window, buttons, and drawing the maze.
- **[generate_all_graphs.py](generate_all_graphs.py)**: A script that takes data from the `data/` folder and makes 5 performance charts.
- **[maze_generator.py](maze_generator.py)**: The logic that builds the actual maze grids.
- **[visualizer.py](visualizer.py)**: Makes simple bar and line charts for individual runs in the app.
- **[exporter.py](exporter.py)**: Saves the results of your solvers into CSV files.

### Algorithms Folder
All the actual solving logic lives in the `algorithms/` folder:
- **[dfs.py](algorithms/dfs.py)**: Depth-First Search (fast but not always optimal).
- **[bfs.py](algorithms/bfs.py)**: Breadth-First Search (finds the shortest path).
- **[astar.py](algorithms/astar.py)**: A* Search using both Manhattan and Euclidean distances.
- **[value_iteration.py](algorithms/value_iteration.py)**: MDP solver that calculates the best move for every single spot in the maze.
- **[policy_iteration.py](algorithms/policy_iteration.py)**: MDP solver that improves a set of moves until they are perfect.
- **[utils.py](algorithms/utils.py)**: Shared helpers for things like distances and moving around the grid.

## Data and Visuals
- **data/**: Stores CSV files with the results of your runs.
- **visuals/**: Where all the generated images and charts are saved (`maze_solver/visuals/`).

## Metrics Note
- `max_frontier` is reported as **Peak frontier size (proxy for memory)** (max queue/stack length), not measured RAM bytes.

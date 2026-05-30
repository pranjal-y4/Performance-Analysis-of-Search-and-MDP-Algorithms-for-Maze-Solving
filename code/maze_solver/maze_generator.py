"""
Orthogonal rectangular maze generator using recursive backtracking (DFS).
- Perfect maze: exactly 1 path between any two cells (no loops)
- Braided maze: multi paths possible (loops added by removing walls)
- 4 neighbors: North, South, East, West (no diagonal)
- Matrix: 1 = wall, 0 = corridor
- Grid size: (2 × width + 1) × (2 × height + 1)
- Start: top-left corridor (1, 1)
- Goal: bottom-right corridor
"""

import random
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MazeResult:
    """Output of maze generation."""
    matrix: List[str]
    width: int
    height: int
    seed: int
    maze_type: str
    start: Tuple[int, int]
    goal: Tuple[int, int]
    solvable: bool


def _nodes_to_matrix(nodes: List[List[int]], width: int, height: int) -> List[str]:
    """Convert internal node representation to matrix format.
    Result: (2*height+1) rows × (2*width+1) cols, 1=wall, 0=corridor.
    """
    matrix = []
    row1, row2 = '', ''

    for i in range(width * height):
        row1 += '1' if not row1 else ''
        row2 += '1' if not row2 else ''

        if nodes[i][1]:  # north wall present
            row1 += '11'
            row2 += '01' if nodes[i][4] else '00'
        else:
            has_above = i >= width
            above = has_above and nodes[i - width][4]
            has_next = (i + 1) % width != 0
            next_node = has_next and nodes[i + 1][1]

            if nodes[i][4]:
                row1 += '01'
                row2 += '01'
            elif next_node or above:
                row1 += '01'
                row2 += '00'
            else:
                row1 += '00'
                row2 += '00'

        if (i + 1) % width == 0:
            matrix.append(row1)
            matrix.append(row2)
            row1, row2 = '', ''

    matrix.append('1' * (width * 2 + 1))
    return matrix


def _generate_perfect(width: int, height: int, rng: random.Random) -> List[List[int]]:
    """
    Recursive backtracking (DFS) maze generation.
    nodes[i] = [visited, north, south, west, east] for cell i.
    """
    maze_size = width * height
    nodes = [[0, 1, 1, 1, 1] for _ in range(maze_size)]
    position_index = {'n': 1, 's': 2, 'w': 3, 'e': 4}
    opposite_index = {'n': 2, 's': 1, 'w': 4, 'e': 3}

    def get_neighbors(pos: int) -> dict:
        row, col = pos // width, pos % width
        return {
            'n': pos - width if row > 0 else -1,
            's': pos + width if row < height - 1 else -1,
            'w': pos - 1 if col > 0 else -1,
            'e': pos + 1 if col < width - 1 else -1,
        }

    position = rng.randint(0, maze_size - 1)
    nodes[position][0] = 1
    visited = 1
    stack = []

    while visited < maze_size:
        neighbors = get_neighbors(position)
        directions = [
            d for d in ['n', 's', 'w', 'e']
            if neighbors[d] != -1 and nodes[neighbors[d]][0] != 1
        ]

        if directions:
            visited += 1
            if len(directions) > 1:
                stack.append(position)
            direction = rng.choice(directions)
            next_pos = neighbors[direction]
            nodes[position][position_index[direction]] = 0
            nodes[next_pos][opposite_index[direction]] = 0
            nodes[next_pos][0] = 1
            position = next_pos
        else:
            if not stack:
                break
            position = stack.pop()

    return nodes


def _remove_walls_for_braiding(
    matrix: List[str], width: int, height: int, braid_factor: float, rng: random.Random
) -> List[str]:
    """
    Remove walls from a perfect maze to create loops (multiple paths).
    braid_factor: 0-1, fraction of removable walls to remove. Higher = more loops.
    """
    matrix = [list(row) for row in matrix]
    rows, cols = len(matrix), len(matrix[0])
    max_walls = int(width * height * 0.4)
    to_remove = int(max_walls * braid_factor)
    removed = 0
    tries = 0
    max_tries = to_remove * 15

    while removed < to_remove and tries < max_tries:
        tries += 1
        y = rng.randint(1, rows - 2)
        x = rng.randint(1, cols - 2)
        if matrix[y][x] != '1':
            continue

        even_row = y % 2 == 0
        even_col = x % 2 == 0

        if not even_row and even_col:
            # Vertical wall (between left/right cells): check x-1, x+1
            if x - 1 >= 0 and x + 1 < cols and matrix[y][x - 1] == '0' and matrix[y][x + 1] == '0':
                matrix[y][x] = '0'
                removed += 1
        elif even_row and not even_col:
            # Horizontal wall (between top/bottom cells): check y-1, y+1
            if y - 1 >= 0 and y + 1 < rows and matrix[y - 1][x] == '0' and matrix[y + 1][x] == '0':
                matrix[y][x] = '0'
                removed += 1

    return [''.join(row) for row in matrix]


def is_solvable(
    matrix: List[str],
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> bool:
    """Validate that a path exists from start to goal (4-neighbor BFS)."""
    from collections import deque
    rows, cols = len(matrix), len(matrix[0])
    visited = {start}
    queue = deque([start])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and matrix[ny][nx] == '0':
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return False


def generate_maze(
    width: int,
    height: int,
    seed: Optional[int] = None,
    maze_type: str = "perfect",
    braid_factor: float = 0.3,
) -> MazeResult:
    """
    Generate a maze.
    Parameters:
      width, height: cell dimensions
      seed: optional for reproducibility
      maze_type: "perfect" (one path) or "braided" (multiple paths via loops)
      braid_factor: 0-1, only for braided. Higher = more loops / alternative paths.
    Output: matrix, start, goal, solvable validation.
    """
    if width < 2 or height < 2:
        raise ValueError("Width and height must be at least 2")

    maze_type = maze_type.lower()
    if maze_type not in ("perfect", "braided"):
        maze_type = "perfect"

    seed = seed if seed is not None else random.randint(0, 2**31 - 1)
    rng = random.Random(seed)

    nodes = _generate_perfect(width, height, rng)
    matrix = _nodes_to_matrix(nodes, width, height)

    if maze_type == "braided":
        braid_factor = max(0, min(1, braid_factor))
        matrix = _remove_walls_for_braiding(matrix, width, height, braid_factor, rng)

    rows = height * 2 + 1
    cols = width * 2 + 1
    start = (1, 1)
    goal = (cols - 2, rows - 2)

    solvable = is_solvable(matrix, start, goal)

    return MazeResult(
        matrix=matrix,
        width=width,
        height=height,
        seed=seed,
        maze_type=maze_type,
        start=start,
        goal=goal,
        solvable=solvable,
    )

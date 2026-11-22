import random


def generate_perfect_maze(rows, cols, seed=None):
    """
    Generates a solvable rows x cols maze using Randomized DFS.

    Returns:
        graph: dict mapping (r, c) -> list of reachable (nr, nc) tuples
        v_walls: 2D boolean list [rows][cols - 1] (True = vertical wall exists)
        h_walls: 2D boolean list [rows - 1][cols] (True = horizontal wall exists)
    """
    if rows < 2 or cols < 2:
        raise ValueError("Maze dimensions must be at least 2x2.")

    rng = random.Random(seed)

    v_walls = [[True for _ in range(cols - 1)] for _ in range(rows)]
    h_walls = [[True for _ in range(cols)] for _ in range(rows - 1)]

    visited = [[False for _ in range(cols)] for _ in range(rows)]
    graph = {(r, c): [] for r in range(rows) for c in range(cols)}

    # Iterative DFS stack to avoid Python recursion depth limits on large mazes (e.g., 50x50)
    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(directions)

        carved = False
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                if dr == 1:       # North
                    h_walls[r][c] = False
                elif dr == -1:    # South
                    h_walls[nr][c] = False
                elif dc == 1:     # East
                    v_walls[r][c] = False
                elif dc == -1:    # West
                    v_walls[r][nc] = False

                graph[(r, c)].append((nr, nc))
                graph[(nr, nc)].append((r, c))
                visited[nr][nc] = True
                stack.append((nr, nc))
                carved = True
                break

        if not carved:
            stack.pop()

    return graph, v_walls, h_walls


def find_dead_ends(graph, exclude=None):
    """Returns a sorted list of cells that have only 1 open neighbor."""
    exclude_set = set(exclude) if exclude else set()
    return sorted(
        [cell for cell, neighbors in graph.items() if len(neighbors) == 1 and cell not in exclude_set]
    )


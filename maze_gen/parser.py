import math
import re


def build_graph_from_wbt(wbt_filepath, cell_size=0.4):
    """
    Parses a Webots .wbt world file containing RectangleArena and Wall nodes
    and reconstructs the corresponding grid adjacency graph.

    Returns:
        graph: dict mapping (r, c) -> list of reachable (nr, nc) tuples
        rows: int
        cols: int
    """
    with open(wbt_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    arena_match = re.search(r"RectangleArena\s*\{[^}]*floorSize\s+([\d.]+)\s+([\d.]+)", content)
    floor_x = float(arena_match.group(1)) if arena_match else 2.0
    floor_y = float(arena_match.group(2)) if arena_match else 2.0

    cols = round(floor_x / cell_size)
    rows = round(floor_y / cell_size)
    half_x = floor_x / 2.0
    half_y = floor_y / 2.0

    graph = {}
    for r in range(rows):
        for c in range(cols):
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    neighbors.append((nr, nc))
            graph[(r, c)] = neighbors

    def remove_edge(cell_a, cell_b):
        if cell_b in graph.get(cell_a, []):
            graph[cell_a].remove(cell_b)
        if cell_a in graph.get(cell_b, []):
            graph[cell_b].remove(cell_a)

    wall_blocks = re.findall(r"Wall\s*\{((?:[^{}]|\{[^{}]*\})*)\}", content)

    for block in wall_blocks:
        t_match = re.search(r"translation\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", block)
        s_match = re.search(r"size\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", block)
        r_match = re.search(r"rotation\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s+([-\d.]+)", block)

        if not (t_match and s_match):
            continue

        wx, wy = float(t_match.group(1)), float(t_match.group(2))
        w_len = float(s_match.group(2))

        is_horizontal = False
        if r_match:
            z_axis = float(r_match.group(1))
            angle = abs(float(r_match.group(2)))
            if abs(z_axis) > 0.9 and abs(angle - math.pi / 2) < 0.2:
                is_horizontal = True

        num_segments = max(1, round(w_len / cell_size))

        if is_horizontal:
            r_above = round((wy + half_y) / cell_size)
            start_x = wx - (w_len / 2.0)
            for i in range(num_segments):
                seg_x = start_x + (i + 0.5) * cell_size
                c = int((seg_x + half_x) / cell_size)
                if 0 < r_above < rows and 0 <= c < cols:
                    remove_edge((r_above - 1, c), (r_above, c))
        else:
            c_right = round((wx + half_x) / cell_size)
            start_y = wy - (w_len / 2.0)
            for i in range(num_segments):
                seg_y = start_y + (i + 0.5) * cell_size
                r = int((seg_y + half_y) / cell_size)
                if 0 <= r < rows and 0 < c_right < cols:
                    remove_edge((r, c_right - 1), (r, c_right))

    return graph, rows, cols
    
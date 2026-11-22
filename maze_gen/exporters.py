import json
import math
import os
from .generator import find_dead_ends
from .visualizer import render_ascii_maze


def cell_to_world(row, col, rows, cols, cell_size=0.4):
    """Converts grid (row, col) indices to Webots [x, y] cell-center coordinates in meters."""
    wx = round(-(cols * cell_size) / 2.0 + (col + 0.5) * cell_size, 4)
    wy = round(-(rows * cell_size) / 2.0 + (row + 0.5) * cell_size, 4)
    return [wx, wy]


def compute_start_yaw(graph, start_cell=(0, 0)):
    """
    Computes the initial yaw angle (in radians, ENU frame: +X=0, +Y=pi/2)
    so the e-puck spawns facing an open corridor out of start_cell.
    """
    if not graph:
        return round(math.pi / 2.0, 6)

    neighbors = graph.get(start_cell, [])
    if not neighbors:
        return round(math.pi / 2.0, 6)

    sr, sc = start_cell
    # Prefer North (+Y) or East (+X) when multiple exits exist from start_cell
    preferred_order = [(sr + 1, sc), (sr, sc + 1), (sr - 1, sc), (sr, sc - 1)]
    target = next((n for n in preferred_order if n in neighbors), neighbors[0])

    dr = target[0] - sr
    dc = target[1] - sc
    return round(math.atan2(dr, dc), 6)


def format_epuck_block(start_x, start_y, start_yaw, controller="maze_solver"):
    """
    Generates the Webots E-puck VRML node placed at (start_x, start_y) with
    Lidar, Compass, and GPS mounted in turretSlot.
    """
    return (
        f"E-puck {{\n"
        f"  translation {round(start_x, 4)} {round(start_y, 4)} 0\n"
        f"  rotation 0 0 1 {start_yaw:.6f}\n"
        f'  controller "{controller}"\n'
        f"  turretSlot [\n"
        f"    Lidar {{\n"
        f'      name "lidar"\n'
        f"      horizontalResolution 360\n"
        f"      fieldOfView 6.283185\n"
        f"      numberOfLayers 1\n"
        f"      minRange 0.03\n"
        f"      maxRange 2.0\n"
        f"    }}\n"
        f"    Compass {{\n"
        f'      name "compass"\n'
        f"    }}\n"
        f"    GPS {{\n"
        f'      name "gps"\n'
        f"    }}\n"
        f"  ]\n"
        f"}}\n"
    )


def export_to_webots_wbt(
    rows,
    cols,
    v_walls,
    h_walls,
    filename="random_maze.wbt",
    cell_size=0.4,
    wall_height=0.12,
    wall_thickness=0.04,
    graph=None,
    start=(0, 0),
    controller="maze_solver",
    include_robot=True,
):
    """
    Writes a Webots R2025a .wbt world file with merged collinear wall segments
    and an optional pre-configured E-puck robot spawned at the start cell.
    """
    floor_x = round(cols * cell_size, 4)
    floor_y = round(rows * cell_size, 4)
    half_x = floor_x / 2.0
    half_y = floor_y / 2.0
    cam_height = round(max(floor_x, floor_y) * 2.6, 2)

    # Required EXTERNPROTO declarations for the arena, walls, e-puck, and Lidar
    proto_lines = [
        "#VRML_SIM R2025a utf8",
        "",
        'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackground.proto"',
        'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackgroundLight.proto"',
        'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/floors/protos/RectangleArena.proto"',
        'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/apartment_structure/protos/Wall.proto"',
        'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/appearances/protos/Roughcast.proto"',
    ]

    if include_robot:
        proto_lines.extend([
            'EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/robots/gctronic/e-puck/protos/E-puck.proto"',
        ])

    header = "\n".join(proto_lines + [
        "",
        "WorldInfo {",
        "}",
        "Viewpoint {",
        "  orientation -0.57735 0.57735 0.57735 2.0944",
        f"  position 0 0 {cam_height}",
        "}",
        "TexturedBackground {",
        "}",
        "TexturedBackgroundLight {",
        "}",
        "RectangleArena {",
        f"  floorSize {floor_x} {floor_y}",
        f"  floorTileSize {round(cell_size * 2, 4)} {round(cell_size * 2, 4)}",
        f"  wallHeight {wall_height}",
        "}",
        "",
    ])

    def make_wall_block(name, x, y, length, is_horizontal):
        rot_line = "  rotation 0 0 1 1.5708\n" if is_horizontal else ""
        return (
            f"Wall {{\n"
            f"  translation {round(x, 4)} {round(y, 4)} 0\n"
            f"{rot_line}"
            f'  name "{name}"\n'
            f"  size {wall_thickness} {round(length, 4)} {wall_height}\n"
            f"  appearance Roughcast {{\n"
            f"    colorOverride 0.141176 0.121569 0.192157\n"
            f"    textureTransform TextureTransform {{ scale 2.4 1 }}\n"
            f"  }}\n"
            f"}}\n"
        )

    wall_blocks = []
    wall_idx = 1

    # Merge vertical walls along columns
    for c in range(cols - 1):
        wx = -half_x + (c + 1) * cell_size
        r = 0
        while r < rows:
            if v_walls[r][c]:
                start_r = r
                while r < rows and v_walls[r][c]:
                    r += 1
                span = r - start_r
                length = span * cell_size
                wy = -half_y + (start_r + span / 2.0) * cell_size
                wall_blocks.append(make_wall_block(f"v_wall_{wall_idx}", wx, wy, length, False))
                wall_idx += 1
            else:
                r += 1

    # Merge horizontal walls along rows
    for r in range(rows - 1):
        wy = -half_y + (r + 1) * cell_size
        c = 0
        while c < cols:
            if h_walls[r][c]:
                start_c = c
                while c < cols and h_walls[r][c]:
                    c += 1
                span = c - start_c
                length = span * cell_size
                wx = -half_x + (start_c + span / 2.0) * cell_size
                wall_blocks.append(make_wall_block(f"h_wall_{wall_idx}", wx, wy, length, True))
                wall_idx += 1
            else:
                c += 1

    # Build optional E-puck robot node oriented toward the open corridor at start
    robot_block = ""
    if include_robot:
        start_x, start_y = cell_to_world(start[0], start[1], rows, cols, cell_size)
        start_yaw = compute_start_yaw(graph, start)
        robot_block = "\n" + format_epuck_block(
            start_x, start_y, start_yaw, controller=controller
        )

    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(header + "\n" + "".join(wall_blocks) + robot_block)

    return wall_idx - 1


def export_graph_json(
    graph,
    rows,
    cols,
    wbt_filename,
    json_filename="maze_graph.json",
    cell_size=0.4,
    seed=None,
    start=(0, 0),
    goal=None,
):
    """Exports the maze adjacency graph and metadata (including initial robot yaw) as JSON."""
    if goal is None:
        goal = (rows - 1, cols - 1)

    dead_ends = find_dead_ends(graph, exclude=[start, goal])
    start_yaw = compute_start_yaw(graph, start)

    payload = {
        "metadata": {
            "world_file": os.path.basename(wbt_filename),
            "generator": "randomized_dfs",
            "seed": seed,
            "rows": rows,
            "cols": cols,
            "cell_size_m": cell_size,
            "arena_size_m": [round(cols * cell_size, 4), round(rows * cell_size, 4)],
            "start": {
                "cell": list(start),
                "world_xy": cell_to_world(start[0], start[1], rows, cols, cell_size),
                "yaw_rad": start_yaw,
            },
            "goal": {
                "cell": list(goal),
                "world_xy": cell_to_world(goal[0], goal[1], rows, cols, cell_size),
            },
            "dead_ends": [list(cell) for cell in dead_ends],
            "notes": "Grid indices are [row, col] starting bottom-left (0,0). world_xy are [x, y] cell centers in meters.",
        },
        "adjacency": {
            f"{r},{c}": [list(n) for n in sorted(neighbors)]
            for (r, c), neighbors in sorted(graph.items())
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(json_filename)), exist_ok=True)
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def export_maze_txt(
    graph,
    rows,
    cols,
    wbt_filename,
    json_filename,
    txt_filename="maze_info.txt",
    wall_count=0,
    cell_size=0.4,
    seed=None,
    start=(0, 0),
    goal=None,
):
    """Exports a human-readable ASCII map and summary info to a .txt file."""
    if goal is None:
        goal = (rows - 1, cols - 1)

    start_xy = cell_to_world(start[0], start[1], rows, cols, cell_size)
    start_yaw = compute_start_yaw(graph, start)
    goal_xy = cell_to_world(goal[0], goal[1], rows, cols, cell_size)
    arena_x = round(cols * cell_size, 4)
    arena_y = round(rows * cell_size, 4)
    ascii_map = render_ascii_maze(graph, rows, cols, start=start, goal=goal)

    report = [
        f"Maze Summary: {rows}x{cols} Grid",
        "=" * 40,
        f"World File : {os.path.basename(wbt_filename)}",
        f"Graph File : {os.path.basename(json_filename)}",
        f"Seed       : {seed if seed is not None else 'Random'}",
        f"Cell Size  : {cell_size} m",
        f"Arena Size : {arena_x} m x {arena_y} m",
        f"Wall Nodes : {wall_count} merged walls",
        f"Start (S)  : cell {list(start)} -> world {start_xy} m (yaw: {start_yaw} rad / {round(math.degrees(start_yaw), 1)} deg)",
        f"Goal  (G)  : cell {list(goal)} -> world {goal_xy} m",
        "",
        "Top-Down Layout:",
        ascii_map,
        "",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(txt_filename)), exist_ok=True)
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

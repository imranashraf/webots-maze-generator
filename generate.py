import argparse
import os
from maze_gen import (
    generate_perfect_maze,
    export_to_webots_wbt,
    export_graph_json,
    export_maze_txt,
    render_ascii_maze,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synchronized Webots (.wbt) mazes, JSON adjacency graphs, and TXT summaries."
    )
    parser.add_argument("--rows", type=int, default=8, help="Number of grid rows (default: 8)")
    parser.add_argument("--cols", type=int, default=8, help="Number of grid columns (default: 8)")
    parser.add_argument("--cell-size", type=float, default=0.4, help="Cell size in meters (default: 0.4)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--out-dir", type=str, default="examples", help="Output directory (default: examples)")
    parser.add_argument("--name", type=str, default=None, help="Base filename without extension (default: maze_RxC)")
    parser.add_argument("--quiet", action="store_true", help="Suppress terminal ASCII preview")
    args = parser.parse_args()

    base_name = args.name or f"maze_{args.rows}x{args.cols}"
    wbt_path = os.path.join(args.out_dir, f"{base_name}.wbt")
    json_path = os.path.join(args.out_dir, f"{base_name}_graph.json")
    txt_path = os.path.join(args.out_dir, f"{base_name}_info.txt")

    graph, v_walls, h_walls = generate_perfect_maze(args.rows, args.cols, seed=args.seed)
    
    wall_count = export_to_webots_wbt(
        args.rows,
        args.cols,
        v_walls,
        h_walls,
        filename=wbt_path,
        cell_size=args.cell_size,
        graph=graph,
        controller=getattr(args, "controller", "maze_solver"),
    )
    export_graph_json(
        graph,
        args.rows,
        args.cols,
        wbt_filename=wbt_path,
        json_filename=json_path,
        cell_size=args.cell_size,
        seed=args.seed,
    )
    export_maze_txt(
        graph,
        args.rows,
        args.cols,
        wbt_filename=wbt_path,
        json_filename=json_path,
        txt_filename=txt_path,
        wall_count=wall_count,
        cell_size=args.cell_size,
        seed=args.seed,
    )

    if not args.quiet:
        print(render_ascii_maze(graph, args.rows, args.cols))
        print(f"\nGenerated {args.rows}x{args.cols} maze ({wall_count} merged walls):")
        print(f"  World: {wbt_path}")
        print(f"  Graph: {json_path}")
        print(f"  Info : {txt_path}")


if __name__ == "__main__":
    main()
    
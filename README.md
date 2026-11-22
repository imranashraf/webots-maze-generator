# Webots Maze Generator

Procedural $N \times M$ maze generator and parser for **Webots (R2025a)**. Generates synchronized `.wbt` simulation worlds (with collinear walls merged for fast rendering) and metadata-rich `.json` adjacency graphs ready for classical pathfinding benchmarks (**BFS, DFS, Dijkstra, A***).


## Quick Start

Generate an $8 \times 8$ maze (`0.4m` cells aligned to `0.8m` chequered tiles):

```bash
python generate.py --rows 8 --cols 8 --seed 42 --out-dir examples
import os
import tempfile
import unittest
from collections import deque
from maze_gen import (
    generate_perfect_maze,
    export_to_webots_wbt,
    build_graph_from_wbt,
)


class TestMazeGenerator(unittest.TestCase):
    def test_solvability_and_roundtrip_parsing(self):
        rows, cols = 8, 8
        graph, v_walls, h_walls = generate_perfect_maze(rows, cols, seed=42)

        # 1. Verify BFS reaches every single cell from (0, 0)
        visited = {(0, 0)}
        queue = deque([(0, 0)])
        while queue:
            curr = queue.popleft()
            for nxt in graph[curr]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        self.assertEqual(len(visited), rows * cols)

        # 2. Export to .wbt and parse back to ensure zero wall mismatch
        with tempfile.TemporaryDirectory() as tmpdir:
            wbt_file = os.path.join(tmpdir, "test_maze.wbt")
            export_to_webots_wbt(rows, cols, v_walls, h_walls, filename=wbt_file, cell_size=0.4)
            parsed_graph, p_rows, p_cols = build_graph_from_wbt(wbt_file, cell_size=0.4)

            self.assertEqual((p_rows, p_cols), (rows, cols))
            for cell in graph:
                self.assertEqual(set(graph[cell]), set(parsed_graph[cell]))


if __name__ == "__main__":
    unittest.main()
    
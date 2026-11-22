def render_ascii_maze(graph, rows, cols, start=(0, 0), goal=None, path=None):
    """Returns a formatted ASCII string representation of the maze."""
    if goal is None:
        goal = (rows - 1, cols - 1)
    path_set = set(path) if path else set()

    lines = ["+" + "---+" * cols]
    for r in range(rows - 1, -1, -1):
        row_str = "|"
        bot_str = "+"
        for c in range(cols):
            cell = (r, c)
            if cell == start:
                mark = " S "
            elif cell == goal:
                mark = " G "
            elif cell in path_set:
                mark = " * "
            else:
                mark = "   "

            east = " " if (r, c + 1) in graph.get(cell, []) else "|"
            south = "   +" if (r - 1, c) in graph.get(cell, []) else "---+"
            row_str += mark + east
            bot_str += south
        lines.append(row_str)
        lines.append(bot_str)

    return "\n".join(lines)

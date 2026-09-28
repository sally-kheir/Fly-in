from __future__ import annotations

from flyin.models.graph import Graph


def render_simulation(
    graph: Graph,
    output_lines: list[str],
) -> None:
    """Display the simulation turn by turn in the terminal."""

    total = len(output_lines)

    for index, line in enumerate(output_lines, start=1):
        print(f"Turn {index:>3}/{total}  {line}")

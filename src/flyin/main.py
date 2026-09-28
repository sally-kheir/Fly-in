from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flyin.parsing import MapParser, MapParsingError
from flyin.pathfinding import Dijkstra
from flyin.simulation import Simulator
from flyin.rendering.gui_renderer import render_gui_simulation
from flyin.rendering.terminal_renderer import render_simulation


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flyin",
        description=(
            "Simulate multi-drone routing across a zone network, "
            "minimizing the number of simulation turns."
        ),
    )

    parser.add_argument(
        "map_file",
        type=str,
        help="Path to the map file describing the zone network.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help=(
            "Path to write the simulation output to. If omitted, "
            "the result is printed to stdout."
        ),
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=1000,
        help="Safety limit on the number of turns (default: 1000).",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical interface.",
    )

    return parser


def run(
    map_file: str,
    output: str | None,
    max_turns: int,
    gui: bool,
) -> int:
    try:
        parser = MapParser()
        graph, nb_drones = parser.parse(map_file)
    except MapParsingError as exc:
        print(
            f"Error: invalid map file '{map_file}': {exc}",
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print(
            f"Error: could not read '{map_file}': {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        simulator = Simulator(
            Dijkstra(),
            max_turns=max_turns,
        )

        lines = simulator.run(
            graph,
            nb_drones,
        )

    except ValueError as exc:
        print(
            f"Error: simulation failed: {exc}",
            file=sys.stderr,
        )
        return 1

    render_simulation(
        graph,
        lines,
    )

    if gui:
        render_gui_simulation(
            graph,
            lines,
        )

    if output is not None:
        _write_output(
            lines,
            output,
        )

    print(
        f"Simulation complete: {nb_drones} drones, "
        f"{len(lines)} turns.",
        file=sys.stderr,
    )

    return 0


def _write_output(
    lines: list[str],
    output: str | None,
) -> None:
    text = "\n".join(lines)

    if output is None:
        print(text)
    else:
        Path(output).write_text(
            text + "\n",
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    return run(
        args.map_file,
        args.output,
        args.max_turns,
        args.gui,
    )


if __name__ == "__main__":
    sys.exit(main())

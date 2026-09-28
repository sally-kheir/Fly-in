"""Main simulation loop, tying pathfinding and scheduling together.

Creates every drone at the start zone, computes an initial path for
each with the given pathfinding algorithm, then repeatedly runs
turns through the Scheduler until every drone has reached the end
zone (or a safety turn limit is hit, to avoid an infinite loop in
case of an unsolvable map).
"""

from __future__ import annotations

from flyin.models.drone import Drone
from flyin.models.graph import Graph
from flyin.pathfinding.base import PathfindingAlgorithm
from flyin.simulation.scheduler import Scheduler
from flyin.simulation.state import SimulationState

DEFAULT_MAX_TURNS = 1000


class Simulator:
    """Runs a full multi-drone simulation on a given map."""

    def __init__(
        self,
        algorithm: PathfindingAlgorithm,
        max_turns: int = DEFAULT_MAX_TURNS,
    ) -> None:
        """Initialize the simulator.

        Args:
            algorithm: The pathfinding algorithm used to compute each
                drone's initial route from start to end.
            max_turns: Safety limit on the number of turns to
                simulate before giving up.
        """
        self.algorithm = algorithm
        self.max_turns = max_turns
        self.scheduler = Scheduler()

    def run(self, graph: Graph, nb_drones: int) -> list[str]:
        """Run the simulation to completion.

        Args:
            graph: The parsed network to simulate on.
            nb_drones: Number of drones to create at the start zone.

        Returns:
            The list of output lines, one per turn, in the exact
            format required ("D1-roof1 D2-corridorA", ...). Turns
            where every drone stayed in place are omitted.

        Raises:
            ValueError: If no path exists between the start and end
                zones, or if the simulation does not finish within
                max_turns.
        """
        drones = self._create_drones(graph, nb_drones)
        state = SimulationState(drones)
        output_lines: list[str] = []

        while not state.all_arrived():
            if state.turn_number >= self.max_turns:
                raise ValueError(
                    f"Simulation did not complete within "
                    f"{self.max_turns} turns (possible deadlock)."
                )

            self.scheduler.process_turn(graph, state)
            line = state.format_turn_output()
            if line:
                output_lines.append(line)

        return output_lines

    def _create_drones(self, graph: Graph, nb_drones: int) -> list[Drone]:
        """Create every drone at the start zone with a computed path.

        Args:
            graph: The network to compute paths on.
            nb_drones: Number of drones to create.

        Returns:
            The list of drones, named D1 through D<nb_drones>, each
            with its path already assigned.

        Raises:
            ValueError: If no path exists between start and end.
        """
        start = graph.get_start_zone()
        end = graph.get_end_zone()
        full_path = self.algorithm.find_path(graph, start.name, end.name)

        drones: list[Drone] = []
        for index in range(1, nb_drones + 1):
            drone = Drone(f"D{index}", start.name)
            drone.path = list(full_path[1:])
            drones.append(drone)
        return drones

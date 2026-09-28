"""Turn-by-turn scheduler resolving drone movement conflicts.

Decides, for each turn, which active drones may move into their next
zone/connection and which must wait, based on zone and connection
capacity. Drones are processed in declaration order (D1, D2, ...),
which acts as the tie-breaking priority when several drones compete
for the same limited resource.
"""

from __future__ import annotations

from flyin.models.connection import Connection
from flyin.models.drone import Drone
from flyin.models.graph import Graph
from flyin.simulation.state import SimulationState


class Scheduler:
    """Resolves one simulation turn for every active drone."""

    def __init__(self) -> None:
        self.connections_used_this_turn: dict[str, int] = {}

    def process_turn(self, graph: Graph, state: SimulationState) -> None:
        """Advance the simulation by exactly one turn.

        Args:
            graph: The network drones are moving through.
            state: The simulation state to update in place.
        """
        state.start_new_turn()
        self.connections_used_this_turn = {}

        for drone in state.active_drones():
            if drone.is_in_flight():
                self._advance_flight(drone, graph, state)
            else:
                self._try_start_move(drone, graph, state)

    def _advance_flight(
        self, drone: Drone, graph: Graph, state: SimulationState
    ) -> None:
        """Progress a drone already in flight toward a restricted zone.

        Args:
            drone: The in-flight drone to advance.
            graph: The network, used to resolve the landing zone.
            state: The simulation state, updated with the move.
        """
        connection_name = drone.current_position

        drone.advance_flight()

        if drone.is_waiting():
            landing_zone_name = self._resolve_landing_zone(
                graph,
                connection_name,
                drone,
            )

            landing_zone = graph.get_zone(
                landing_zone_name
            )

            if not landing_zone.has_capacity_for(1):
                return

            connection = self._find_connection_by_name(
                graph,
                connection_name,
            )

            if connection is not None:
                connection.remove_drone(
                    drone.drone_id
                )

            landing_zone.add_drone(
                drone.drone_id
            )

            drone.current_position = landing_zone_name

            if drone.path and drone.path[0] == landing_zone_name:
                drone.path.pop(0)

            state.record_move(
                drone.drone_id,
                landing_zone_name,
            )

            if landing_zone_name == graph.end_zone_name:
                drone.mark_arrived()

        else:
            state.record_move(
                drone.drone_id,
                connection_name,
            )

    def _try_start_move(
        self, drone: Drone, graph: Graph, state: SimulationState
    ) -> None:
        """Attempt to move a waiting drone toward its next zone.

        If the destination zone or the connection leading to it has
        no available capacity this turn, the drone simply stays in
        place.

        Args:
            drone: The waiting drone to try to move.
            graph: The network drones are moving through.
            state: The simulation state, updated if the move happens.
        """
        destination_name = drone.next_zone()

        if destination_name is None:
            return

        destination_zone = graph.get_zone(
            destination_name
        )

        connection = graph.get_connection_between(
            drone.current_position,
            destination_name,
        )

        cost = destination_zone.movement_cost

        if not destination_zone.has_capacity_for(1):
            return

        if connection is not None:
            used = self.connections_used_this_turn.get(
                connection.name,
                0,
            )

            if used >= connection.max_link_capacity:
                return

            if not connection.has_capacity_for(1):
                return

        current_zone = graph.zones.get(
            drone.current_position
        )

        if current_zone is not None:
            current_zone.remove_drone(
                drone.drone_id
            )

        if connection is not None:
            self.connections_used_this_turn[
                connection.name
            ] = used + 1

        if cost > 1 and connection is not None:
            connection.add_drone(
                drone.drone_id
            )

            drone.start_move(
                connection.name,
                cost,
            )

            state.record_move(
                drone.drone_id,
                connection.name,
            )

        else:
            destination_zone.add_drone(
                drone.drone_id
            )

            drone.start_move(
                destination_name,
                cost,
            )

            state.record_move(
                drone.drone_id,
                destination_name,
            )

            if destination_name == graph.end_zone_name:
                drone.mark_arrived()

    def _find_connection_by_name(
        self, graph: Graph, name: str
    ) -> Connection | None:
        """Find a connection in the graph by its canonical name.

        Args:
            graph: The network to search.
            name: The connection's "zoneA-zoneB" name.

        Returns:
            The matching Connection, or None if not found.
        """
        for connection in graph.connections:
            if connection.name == name:
                return connection

        return None

    def _resolve_landing_zone(
        self, graph: Graph, connection_name: str, drone: Drone
    ) -> str:
        """Determine which zone a drone lands in after a flight.

        Args:
            graph: The network, used to inspect the connection.
            connection_name: The connection the drone was traversing.
            drone: The drone that just finished its flight.

        Returns:
            The name of the zone the drone has landed in.

        Raises:
            ValueError: If the connection cannot be found.
        """
        connection = self._find_connection_by_name(
            graph,
            connection_name,
        )

        if connection is None:
            raise ValueError(
                f"Unknown connection '{connection_name}' for drone "
                f"'{drone.drone_id}'."
            )

        if drone.path and drone.path[0] in (
            connection.zone_a,
            connection.zone_b,
        ):
            return drone.path[0]

        return connection.zone_b

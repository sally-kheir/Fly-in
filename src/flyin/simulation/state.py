"""Snapshot of the simulation at a given turn.

SimulationState holds everything that describes "where things stand
right now": the current turn number, every drone and its position,
and the moves recorded during the current turn (used to build the
output line for that turn).
"""

from __future__ import annotations

from flyin.models.drone import Drone


class SimulationState:
    """Mutable snapshot of the simulation, updated turn by turn.

    Attributes:
        turn_number: The current turn (starts at 0, before any
            movement has happened).
        drones: Every drone participating in the simulation.
        moves_this_turn: Maps a drone_id to the zone/connection name
            it moved into during the current turn. Drones that stayed
            in place are not recorded here (per the output format).
    """

    def __init__(self, drones: list[Drone]) -> None:
        """Initialize the simulation state.

        Args:
            drones: The full list of drones taking part in the
                simulation, already created at the start zone.
        """
        self.turn_number = 0
        self.drones: list[Drone] = drones
        self.moves_this_turn: dict[str, str] = {}

    def start_new_turn(self) -> None:
        """Advance to the next turn and clear last turn's moves."""
        self.turn_number += 1
        self.moves_this_turn = {}

    def record_move(self, drone_id: str, destination: str) -> None:
        """Record that a drone moved during the current turn.

        Args:
            drone_id: Identifier of the drone that moved.
            destination: Name of the zone or connection it moved
                into.
        """
        self.moves_this_turn[drone_id] = destination

    def all_arrived(self) -> bool:
        """Return True if every drone has reached the end zone."""
        return all(drone.is_arrived() for drone in self.drones)

    def active_drones(self) -> list[Drone]:
        """Return the drones that have not yet arrived."""
        return [drone for drone in self.drones if not drone.is_arrived()]

    def format_turn_output(self) -> str:
        """Build the output line for the current turn.

        Returns:
            A string like "D1-roof1 D2-corridorA", following the
            order drones were declared. Drones that did not move
            this turn are omitted, as required by the output format.
        """
        parts = [
            f"{drone.drone_id}-{self.moves_this_turn[drone.drone_id]}"
            for drone in self.drones
            if drone.drone_id in self.moves_this_turn
        ]
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"SimulationState(turn={self.turn_number}, "
            f"drones={len(self.drones)}, "
            f"moved_this_turn={len(self.moves_this_turn)})"
        )

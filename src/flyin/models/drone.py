"""Drone model representing a mobile agent moving through the network.

Unlike Zone and Connection, which are fixed elements of the map, a
Drone is a stateful object whose position and status change at every
simulation turn as it travels from the start zone to the end zone.
"""

from __future__ import annotations

from enum import Enum


class DroneStatus(str, Enum):
    """Possible states of a drone during the simulation."""

    WAITING = "waiting"
    IN_FLIGHT = "in_flight"
    ARRIVED = "arrived"


class Drone:
    """A single drone traveling through the zone network.

    Attributes:
        drone_id: Unique identifier of the drone (e.g. "D1").
        current_position: Name of the zone the drone currently
            occupies, or the name of the connection it is currently
            traversing while IN_FLIGHT.
        status: Current status of the drone.
        path: Ordered list of zone names the drone intends to follow,
            from its current position to the end zone.
        turns_remaining: Number of turns left before the drone
            completes a multi-turn move (e.g. entering a restricted
            zone). Zero when not in flight.
    """

    def __init__(
        self,
        drone_id: str,
        start_position: str,
        path: list[str] | None = None,
    ) -> None:
        """Initialize a Drone at the start zone.

        Args:
            drone_id: Unique identifier of the drone (e.g. "D1").
            start_position: Name of the zone the drone starts in
                (should be the start hub).
            path: Optional precomputed path (list of zone names) the
                drone should follow. Can be assigned later once the
                pathfinding algorithm has run.
        """
        self.drone_id = drone_id
        self.current_position = start_position
        self.status = DroneStatus.WAITING
        self.path: list[str] = path if path is not None else []
        self.turns_remaining = 0

    def is_waiting(self) -> bool:
        """Return True if the drone is on the ground, ready to move."""
        return self.status is DroneStatus.WAITING

    def is_in_flight(self) -> bool:
        """Return True if the drone is mid-transit toward a
        restricted zone."""
        return self.status is DroneStatus.IN_FLIGHT

    def is_arrived(self) -> bool:
        """Return True if the drone has reached the end zone."""
        return self.status is DroneStatus.ARRIVED

    def next_zone(self) -> str | None:
        """Return the next zone the drone should move to, if any.

        Returns:
            The name of the next zone in the path, or None if the
            drone has no remaining path (e.g. already arrived).
        """
        if not self.path:
            return None
        return self.path[0]

    def start_move(self, destination: str, cost: int) -> None:
        """Begin a move toward a destination zone.

        Args:
            destination: Name of the connection or zone being
                entered.
            cost: Number of turns required to complete this move
                (1 for normal/priority zones, 2 for restricted
                zones).

        Raises:
            ValueError: If the drone is not in a state where it can
                start a new move (e.g. already in flight).
        """
        if self.is_in_flight():
            raise ValueError(
                f"Drone '{self.drone_id}' is already in flight and "
                f"cannot start a new move."
            )
        self.current_position = destination
        if cost > 1:
            self.status = DroneStatus.IN_FLIGHT
            self.turns_remaining = cost - 1
        else:
            self.turns_remaining = 0
            if self.path and self.path[0] == destination:
                self.path.pop(0)

    def advance_flight(self) -> None:
        """Progress an in-flight drone by one turn.

        Decrements the remaining turn count. When it reaches zero,
        the drone is considered to have landed and returns to the
        WAITING status.
        """
        if not self.is_in_flight():
            raise ValueError(
                f"Drone '{self.drone_id}' is not currently in flight."
            )
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.status = DroneStatus.WAITING
            if self.path and self.path[0] == self.current_position:
                self.path.pop(0)

    def mark_arrived(self) -> None:
        """Mark the drone as having reached the end zone."""
        self.status = DroneStatus.ARRIVED
        self.turns_remaining = 0

    def __repr__(self) -> str:
        return (
            f"Drone(drone_id={self.drone_id!r}, "
            f"position={self.current_position!r}, "
            f"status={self.status.value}, "
            f"turns_remaining={self.turns_remaining})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Drone):
            return NotImplemented
        return self.drone_id == other.drone_id

    def __hash__(self) -> int:
        return hash(self.drone_id)

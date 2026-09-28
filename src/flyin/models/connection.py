"""Connection model representing an edge between two zones.

A connection is a bidirectional link between two zones (like a road
or a rail segment between two bus stops). Each connection has its own
capacity limit, independent from the capacity of the zones it links.
"""

from __future__ import annotations


class Connection:
    """A bidirectional link between two zones.

    Attributes:
        zone_a: Name of the first zone linked by this connection.
        zone_b: Name of the second zone linked by this connection.
        max_link_capacity: Maximum number of drones allowed to
            traverse this connection at the same time.
        occupants: Set of drone IDs currently traversing this
            connection (used for multi-turn movements toward
            restricted zones).
    """

    def __init__(
        self,
        zone_a: str,
        zone_b: str,
        max_link_capacity: int = 1,
    ) -> None:
        """Initialize a Connection.

        Args:
            zone_a: Name of one of the two zones linked.
            zone_b: Name of the other zone linked.
            max_link_capacity: Max simultaneous drones on this link.
                Defaults to 1.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        self.occupants: set[str] = set()

    @property
    def name(self) -> str:
        """Return the canonical identifier of this connection.

        Used for the simulation output format (e.g. drones "in
        flight" toward a restricted zone are reported using the
        connection name).
        """
        return f"{self.zone_a}-{self.zone_b}"

    def involves(self, zone_name: str) -> bool:
        """Check whether this connection touches a given zone.

        Args:
            zone_name: Name of the zone to check.

        Returns:
            True if the zone is one of the two endpoints.
        """
        return zone_name in (self.zone_a, self.zone_b)

    def other_end(self, zone_name: str) -> str:
        """Return the zone on the other side of this connection.

        Args:
            zone_name: Name of the zone on one side of the link.

        Returns:
            The name of the zone on the opposite side.

        Raises:
            ValueError: If zone_name is not an endpoint of this
                connection.
        """
        if zone_name == self.zone_a:
            return self.zone_b
        if zone_name == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"Zone '{zone_name}' is not part of connection "
            f"'{self.name}'."
        )

    def is_full(self) -> bool:
        """Return True if the connection has reached max capacity."""
        return len(self.occupants) >= self.max_link_capacity

    def has_capacity_for(self, incoming: int = 1) -> bool:
        """Check if the connection can accept extra drones.

        Args:
            incoming: Number of drones that would like to traverse
                this connection right now.

        Returns:
            True if adding `incoming` drones would not exceed
            max_link_capacity.
        """
        return len(self.occupants) + incoming <= self.max_link_capacity

    def add_drone(self, drone_id: str) -> None:
        """Register a drone as currently traversing this connection.

        Args:
            drone_id: Identifier of the drone entering the link.

        Raises:
            ValueError: If the connection has no available capacity.
        """
        if not self.has_capacity_for(1) and drone_id not in self.occupants:
            raise ValueError(
                f"Connection '{self.name}' is full "
                f"(max_link_capacity={self.max_link_capacity})."
            )
        self.occupants.add(drone_id)

    def remove_drone(self, drone_id: str) -> None:
        """Remove a drone from this connection, freeing up capacity.

        Args:
            drone_id: Identifier of the drone leaving the link.
        """
        self.occupants.discard(drone_id)

    def __repr__(self) -> str:
        return (
            f"Connection(zone_a={self.zone_a!r}, zone_b={self.zone_b!r}, "
            f"max_link_capacity={self.max_link_capacity}, "
            f"occupants={len(self.occupants)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return NotImplemented
        return {self.zone_a, self.zone_b} == {other.zone_a, other.zone_b}

    def __hash__(self) -> int:
        return hash(frozenset((self.zone_a, self.zone_b)))

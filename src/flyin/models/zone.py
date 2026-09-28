"""Zone model representing a node in the drone routing graph.

A zone is a fixed location on the map (like a bus stop or a metro
station). Drones move between zones through connections. Each zone
has a type that determines how many turns it costs to enter it, and
a capacity that limits how many drones can occupy it at the same
time.
"""

from __future__ import annotations

from enum import Enum


class ZoneType(str, Enum):
    """Possible types for a zone, as defined in the map file format."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


ZONE_MOVEMENT_COST = {
    ZoneType.NORMAL: 1,
    ZoneType.RESTRICTED: 2,
    ZoneType.PRIORITY: 1,
    ZoneType.BLOCKED: 0,
}


class Zone:
    """A single zone (node) in the drone routing network.

    Attributes:
        name: Unique identifier of the zone (e.g. "roof1").
        x: X coordinate, used for visual representation.
        y: Y coordinate, used for visual representation.
        zone_type: The type of the zone (normal, blocked, restricted,
            priority), which determines its movement cost.
        color: Optional color used for terminal/graphical rendering.
        max_drones: Maximum number of drones allowed in this zone at
            the same time.
        is_start: Whether this zone is the unique start hub.
        is_end: Whether this zone is the unique end hub.
        occupants: Set of drone IDs currently present in this zone.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        """Initialize a Zone.

        Args:
            name: Unique identifier of the zone.
            x: X coordinate of the zone.
            y: Y coordinate of the zone.
            zone_type: Type of the zone. Defaults to NORMAL.
            color: Optional display color.
            max_drones: Max simultaneous occupants. Defaults to 1.
            is_start: True if this is the start hub.
            is_end: True if this is the end hub.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.is_start = is_start
        self.is_end = is_end
        self.occupants: set[str] = set()

    @property
    def movement_cost(self) -> int:
        """Return the number of turns required to enter this zone."""
        return ZONE_MOVEMENT_COST[self.zone_type]

    def is_blocked(self) -> bool:
        """Return True if drones are forbidden from entering this zone."""
        return self.zone_type is ZoneType.BLOCKED

    def is_full(self) -> bool:
        """Return True if the zone has reached its maximum capacity.

        The start and end zones are never considered full: all drones
        may share the start initially, and delivered drones simply
        stop being tracked once they reach the end.
        """
        if self.is_start or self.is_end:
            return False
        return len(self.occupants) >= self.max_drones

    def has_capacity_for(self, incoming: int = 1) -> bool:
        """Check if the zone can accept a given number of extra drones.

        Args:
            incoming: Number of drones that would like to enter.

        Returns:
            True if the zone can accept them without exceeding
            max_drones (ignored for start/end zones).
        """
        if self.is_blocked():
            return False
        if self.is_start or self.is_end:
            return True
        return len(self.occupants) + incoming <= self.max_drones

    def add_drone(self, drone_id: str) -> None:
        """Register a drone as currently occupying this zone.

        Args:
            drone_id: Identifier of the drone entering the zone.

        Raises:
            ValueError: If the zone has no available capacity.
        """
        if not self.has_capacity_for(1) and drone_id not in self.occupants:
            raise ValueError(
                f"Zone '{self.name}' is full "
                f"(max_drones={self.max_drones})."
            )
        self.occupants.add(drone_id)

    def remove_drone(self, drone_id: str) -> None:
        """Remove a drone from this zone, freeing up capacity.

        Args:
            drone_id: Identifier of the drone leaving the zone.
        """
        self.occupants.discard(drone_id)

    def __repr__(self) -> str:
        return (
            f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
            f"type={self.zone_type.value}, max_drones={self.max_drones}, "
            f"occupants={len(self.occupants)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

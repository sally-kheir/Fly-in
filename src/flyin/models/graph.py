"""Graph model assembling zones and connections into a network.

The Graph is the object that ties Zone and Connection together. It
stores every zone by name, every connection between zones, and
provides navigation helpers (neighbors, lookups) used by the parser,
the pathfinding algorithm, and the simulator.

No external graph library is used here (networkx, graphlib, etc. are
forbidden by the subject): this is a hand-written adjacency
structure built on top of our own Zone and Connection classes.
"""

from __future__ import annotations

from flyin.models.connection import Connection
from flyin.models.zone import Zone


class Graph:
    """The full network of zones and connections.

    Attributes:
        zones: Mapping from zone name to its Zone object.
        connections: List of every Connection in the network.
        start_zone_name: Name of the unique start hub, once known.
        end_zone_name: Name of the unique end hub, once known.
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_zone_name: str | None = None
        self.end_zone_name: str | None = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph.

        Args:
            zone: The Zone instance to register.

        Raises:
            ValueError: If a zone with the same name already exists,
                or if a second start/end hub is added.
        """
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: '{zone.name}'.")

        if zone.is_start:
            if self.start_zone_name is not None:
                raise ValueError(
                    "A start hub is already defined: "
                    f"'{self.start_zone_name}'. "
                    "Only one start_hub is allowed."
                )
            self.start_zone_name = zone.name

        if zone.is_end:
            if self.end_zone_name is not None:
                raise ValueError(
                    "An end hub is already defined: "
                    f"'{self.end_zone_name}'. "
                    "Only one end_hub is allowed."
                )
            self.end_zone_name = zone.name

        self.zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the graph.

        Args:
            connection: The Connection instance to register.

        Raises:
            ValueError: If either endpoint zone does not exist yet,
                or if this connection (in either direction) has
                already been added.
        """
        for endpoint in (connection.zone_a, connection.zone_b):
            if endpoint not in self.zones:
                raise ValueError(
                    f"Connection '{connection.name}' refers to "
                    f"unknown zone '{endpoint}'."
                )

        if connection in self.connections:
            raise ValueError(
                f"Duplicate connection: '{connection.name}' "
                "(a-b and b-a are considered duplicates)."
            )

        self.connections.append(connection)

    def get_zone(self, name: str) -> Zone:
        """Retrieve a zone by name.

        Args:
            name: Name of the zone to fetch.

        Returns:
            The Zone instance registered under that name.

        Raises:
            KeyError: If no zone with that name exists.
        """
        if name not in self.zones:
            raise KeyError(f"No such zone: '{name}'.")
        return self.zones[name]

    def get_start_zone(self) -> Zone:
        """Return the unique start zone.

        Raises:
            ValueError: If no start hub has been defined yet.
        """
        if self.start_zone_name is None:
            raise ValueError("No start_hub has been defined.")
        return self.zones[self.start_zone_name]

    def get_end_zone(self) -> Zone:
        """Return the unique end zone.

        Raises:
            ValueError: If no end hub has been defined yet.
        """
        if self.end_zone_name is None:
            raise ValueError("No end_hub has been defined.")
        return self.zones[self.end_zone_name]

    def get_connections_for(self, zone_name: str) -> list[Connection]:
        """Return all connections touching a given zone.

        Args:
            zone_name: Name of the zone whose links are requested.

        Returns:
            A list of Connection objects that involve this zone.
        """
        return [
            connection
            for connection in self.connections
            if connection.involves(zone_name)
        ]

    def get_neighbors(self, zone_name: str) -> list[str]:
        """Return the names of zones directly reachable from a zone.

        Args:
            zone_name: Name of the zone to explore from.

        Returns:
            A list of neighboring zone names (order follows the
            order connections were added).
        """
        return [
            connection.other_end(zone_name)
            for connection in self.get_connections_for(zone_name)
        ]

    def get_connection_between(
        self, zone_a: str, zone_b: str
    ) -> Connection | None:
        """Find the connection linking two specific zones, if any.

        Args:
            zone_a: Name of one zone.
            zone_b: Name of the other zone.

        Returns:
            The Connection between them, or None if they are not
            directly connected.
        """
        for connection in self.connections:
            if connection.involves(zone_a) and connection.involves(zone_b):
                return connection
        return None

    def is_ready(self) -> bool:
        """Return True if the graph has both a start and an end hub."""
        return self.start_zone_name is not None and (
            self.end_zone_name is not None
        )

    def __repr__(self) -> str:
        return (
            f"Graph(zones={len(self.zones)}, "
            f"connections={len(self.connections)}, "
            f"start={self.start_zone_name!r}, "
            f"end={self.end_zone_name!r})"
        )

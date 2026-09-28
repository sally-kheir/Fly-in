"""Parser that turns a map file into a fully built Graph.

Reads the file line by line, uses the tokenizer to understand the
syntax of each line, converts raw metadata into proper types, and
assembles Zone/Connection objects into a Graph. All validation
errors are reported with a clear reason and line number.
"""

from __future__ import annotations

from flyin.models.connection import Connection
from flyin.models.graph import Graph
from flyin.models.zone import Zone, ZoneType
from flyin.parsing.exceptions import (
    DuplicateConnectionError,
    DuplicateHubError,
    DuplicateZoneError,
    InvalidMetadataError,
    InvalidSyntaxError,
    InvalidZoneTypeError,
    MissingHubError,
    UnknownZoneReferenceError,
)
from flyin.parsing.tokenizer import (
    CONNECTION_KEYWORD,
    DRONE_COUNT_KEYWORD,
    ConnectionLine,
    HubLine,
    identify_keyword,
    strip_comment_and_blank,
    tokenize_connection_line,
    tokenize_drone_count,
    tokenize_hub_line,
)

_VALID_ZONE_TYPES = {zt.value for zt in ZoneType}


class MapParser:
    """Parses a map file into a Graph and a drone count."""

    def parse(self, file_path: str) -> tuple[Graph, int]:
        """Parse a map file from disk.

        Args:
            file_path: Path to the map file.

        Returns:
            A tuple containing the graph and number of drones.
        """
        with open(file_path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()

        return self.parse_lines(lines)

    def parse_lines(self, lines: list[str]) -> tuple[Graph, int]:
        """Parse map content already split into lines.

        Connections are added immediately. This is required because
        the subject specifies that a connection may only refer to
        zones that were already defined.
        """
        graph = Graph()
        nb_drones = 0

        first_content_line = True
        nb_drones_defined = False

        for line_number, raw_line in enumerate(lines, start=1):
            content = strip_comment_and_blank(raw_line)

            if content is None:
                continue

            keyword, rest = identify_keyword(
                content,
                line_number,
            )

            if first_content_line:
                if keyword != DRONE_COUNT_KEYWORD:
                    raise InvalidSyntaxError(
                        "'nb_drones' must be the first line "
                        "of the map",
                        line_number=line_number,
                    )

                first_content_line = False

            if keyword == DRONE_COUNT_KEYWORD:
                if nb_drones_defined:
                    raise InvalidSyntaxError(
                        "'nb_drones' can only be defined once",
                        line_number=line_number,
                    )

                nb_drones = tokenize_drone_count(
                    rest,
                    line_number,
                )
                nb_drones_defined = True

            elif keyword == CONNECTION_KEYWORD:
                connection_line = tokenize_connection_line(
                    rest,
                    line_number,
                )

                connection = self._build_connection(
                    connection_line,
                    line_number,
                )
                self._add_connection(
                    graph,
                    connection,
                    connection_line,
                    line_number,
                )

            else:
                hub_line = tokenize_hub_line(
                    keyword,
                    rest,
                    line_number,
                )

                zone = self._build_zone(
                    hub_line,
                    line_number,
                )

                self._add_zone(
                    graph,
                    zone,
                    line_number,
                )

        if graph.start_zone_name is None:
            raise MissingHubError(
                "no 'start_hub' declared in the map"
            )

        if graph.end_zone_name is None:
            raise MissingHubError(
                "no 'end_hub' declared in the map"
            )

        return graph, nb_drones

    def _build_zone(
        self,
        hub_line: HubLine,
        line_number: int,
    ) -> Zone:
        """Convert a tokenized HubLine into a Zone object.

        Args:
            hub_line: Parsed zone information.
            line_number: Original map line number.

        Returns:
            A configured Zone instance.
        """
        metadata = dict(hub_line.metadata)

        zone_type_str = metadata.pop(
            "zone",
            ZoneType.NORMAL.value,
        )

        if zone_type_str not in _VALID_ZONE_TYPES:
            raise InvalidZoneTypeError(
                f"unknown zone type '{zone_type_str}'",
                line_number=line_number,
            )

        max_drones_str = metadata.pop(
            "max_drones",
            "1",
        )

        if (
            not max_drones_str.isdigit()
            or int(max_drones_str) <= 0
        ):
            raise InvalidMetadataError(
                f"'max_drones' must be a positive integer, "
                f"got '{max_drones_str}'",
                line_number=line_number,
            )

        color = metadata.pop("color", None)

        return Zone(
            name=hub_line.name,
            x=hub_line.x,
            y=hub_line.y,
            zone_type=ZoneType(zone_type_str),
            color=color,
            max_drones=int(max_drones_str),
            is_start=(hub_line.keyword == "start_hub"),
            is_end=(hub_line.keyword == "end_hub"),
        )

    def _build_connection(
        self,
        connection_line: ConnectionLine,
        line_number: int,
    ) -> Connection:
        """Convert a tokenized ConnectionLine into a Connection.

        Args:
            connection_line: Parsed connection information.
            line_number: Original map line number.

        Returns:
            A configured Connection instance.
        """
        if connection_line.zone_a == connection_line.zone_b:
            raise InvalidSyntaxError(
                f"cannot connect zone "
                f"'{connection_line.zone_a}' to itself",
                line_number=line_number,
            )

        metadata: dict[str, str] = dict(
            connection_line.metadata
        )

        capacity_str = metadata.pop(
            "max_link_capacity",
            "1",
        )

        if (
            not capacity_str.isdigit()
            or int(capacity_str) <= 0
        ):
            raise InvalidMetadataError(
                f"'max_link_capacity' must be a positive integer, "
                f"got '{capacity_str}'",
                line_number=line_number,
            )

        return Connection(
            zone_a=connection_line.zone_a,
            zone_b=connection_line.zone_b,
            max_link_capacity=int(capacity_str),
        )

    def _add_zone(
        self,
        graph: Graph,
        zone: Zone,
        line_number: int,
    ) -> None:
        """Add a zone and validate its name and coordinates."""

        for existing_zone in graph.zones.values():
            if (
                existing_zone.x == zone.x
                and existing_zone.y == zone.y
            ):
                raise DuplicateZoneError(
                    f"zone '{zone.name}' has the same coordinates "
                    f"as zone '{existing_zone.name}'",
                    line_number=line_number,
                )

        try:
            graph.add_zone(zone)

        except ValueError as exc:
            if zone.is_start or zone.is_end:
                raise DuplicateHubError(
                    str(exc),
                    line_number=line_number,
                )

            raise DuplicateZoneError(
                str(exc),
                line_number=line_number,
            )

    def _add_connection(
        self,
        graph: Graph,
        connection: Connection,
        connection_line: ConnectionLine,
        line_number: int,
    ) -> None:
        """Add a connection and validate its endpoints.

        The subject requires connections to reference only zones
        that have already been declared.
        """
        for endpoint in (
            connection_line.zone_a,
            connection_line.zone_b,
        ):
            if endpoint not in graph.zones:
                raise UnknownZoneReferenceError(
                    f"connection refers to unknown zone "
                    f"'{endpoint}'",
                    line_number=line_number,
                )

        try:
            graph.add_connection(connection)

        except ValueError as exc:
            raise DuplicateConnectionError(
                str(exc),
                line_number=line_number,
            )

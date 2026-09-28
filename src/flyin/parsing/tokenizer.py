
"""Tokenizer for a single line of a map file.

Splits one raw text line into structured pieces (keyword, name,
coordinates, metadata) that the parser can turn into Zone/Connection
objects. Knows nothing about Zone, Connection or Graph: its only job
is to understand the syntax of a line.
"""

from __future__ import annotations

import re

from flyin.parsing.exceptions import InvalidMetadataError, InvalidSyntaxError

HUB_KEYWORDS = ("hub", "start_hub", "end_hub")
CONNECTION_KEYWORD = "connection"
DRONE_COUNT_KEYWORD = "nb_drones"

_METADATA_PATTERN = re.compile(r"(\w+)=([^\s\]]+)")


class HubLine:
    """Structured result of tokenizing a hub/start_hub/end_hub line."""

    def __init__(
        self,
        keyword: str,
        name: str,
        x: int,
        y: int,
        metadata: dict[str, str],
    ) -> None:
        self.keyword = keyword
        self.name = name
        self.x = x
        self.y = y
        self.metadata = metadata


class ConnectionLine:
    """Structured result of tokenizing a connection line."""

    def __init__(
        self,
        zone_a: str,
        zone_b: str,
        metadata: dict[str, str],
    ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.metadata = metadata


def strip_comment_and_blank(line: str) -> str | None:
    """Remove comments and skip empty lines."""

    without_comment = line.split("#", 1)[0]
    stripped = without_comment.strip()

    return stripped if stripped else None


def _parse_metadata(
    raw_metadata: str,
    line_number: int,
) -> dict[str, str]:
    """Parse the content inside a metadata block."""

    metadata: dict[str, str] = {}
    remainder = raw_metadata.strip()
    consumed = 0

    for match in _METADATA_PATTERN.finditer(remainder):
        gap = remainder[consumed:match.start()]

        if gap.strip() != "":
            raise InvalidMetadataError(
                f"malformed metadata near '{gap}'",
                line_number=line_number,
            )

        metadata[match.group(1)] = match.group(2)
        consumed = match.end()

    if remainder[consumed:].strip() != "":
        raise InvalidMetadataError(
            f"malformed metadata near '{remainder[consumed:]}'",
            line_number=line_number,
        )

    return metadata


def tokenize_drone_count(
    content: str,
    line_number: int,
) -> int:
    """Tokenize a nb_drones line."""

    value = content.strip()

    if not value.isdigit() or int(value) <= 0:
        raise InvalidSyntaxError(
            f"'nb_drones' must be a positive integer, "
            f"got '{value}'",
            line_number=line_number,
        )

    return int(value)


def tokenize_hub_line(
    keyword: str,
    content: str,
    line_number: int,
) -> HubLine:
    """Tokenize a hub/start_hub/end_hub line."""

    metadata: dict[str, str] = {}
    body = content.strip()

    bracket_start = body.find("[")

    if bracket_start != -1:
        if not body.endswith("]"):
            raise InvalidSyntaxError(
                "metadata block must end with ']'",
                line_number=line_number,
            )

        raw_metadata = body[bracket_start + 1:-1]
        metadata = _parse_metadata(
            raw_metadata,
            line_number,
        )
        body = body[:bracket_start].strip()

    parts = body.split()

    if len(parts) != 3:
        raise InvalidSyntaxError(
            f"expected '<name> <x> <y>' after "
            f"'{keyword}:', got '{body}'",
            line_number=line_number,
        )

    name, x_str, y_str = parts

    if not _is_int(x_str) or not _is_int(y_str):
        raise InvalidSyntaxError(
            f"coordinates must be integers, "
            f"got '{x_str} {y_str}'",
            line_number=line_number,
        )

    return HubLine(
        keyword=keyword,
        name=name,
        x=int(x_str),
        y=int(y_str),
        metadata=metadata,
    )


def tokenize_connection_line(
    content: str,
    line_number: int,
) -> ConnectionLine:
    """Tokenize a connection line."""

    metadata: dict[str, str] = {}
    body = content.strip()

    bracket_start = body.find("[")

    if bracket_start != -1:
        if not body.endswith("]"):
            raise InvalidSyntaxError(
                "metadata block must end with ']'",
                line_number=line_number,
            )

        raw_metadata = body[bracket_start + 1:-1]
        metadata = _parse_metadata(
            raw_metadata,
            line_number,
        )
        body = body[:bracket_start].strip()

    if "-" not in body:
        raise InvalidSyntaxError(
            f"expected '<zone_a>-<zone_b>', got '{body}'",
            line_number=line_number,
        )

    zone_a, _, zone_b = body.partition("-")
    zone_a = zone_a.strip()
    zone_b = zone_b.strip()

    if not zone_a or not zone_b:
        raise InvalidSyntaxError(
            f"expected '<zone_a>-<zone_b>', got '{body}'",
            line_number=line_number,
        )

    return ConnectionLine(
        zone_a=zone_a,
        zone_b=zone_b,
        metadata=metadata,
    )


def identify_keyword(
    line: str,
    line_number: int,
) -> tuple[str, str]:
    """Identify which instruction a line represents."""

    if ":" not in line:
        raise InvalidSyntaxError(
            f"missing ':' in line '{line}'",
            line_number=line_number,
        )

    keyword, _, content = line.partition(":")
    keyword = keyword.strip()

    known_keywords = (
        HUB_KEYWORDS
        + (CONNECTION_KEYWORD, DRONE_COUNT_KEYWORD)
    )

    if keyword not in known_keywords:
        raise InvalidSyntaxError(
            f"unknown keyword '{keyword}'",
            line_number=line_number,
        )

    return keyword, content


def _is_int(value: str) -> bool:
    """Return True if value is a valid integer."""

    if value.startswith("-"):
        return value[1:].isdigit()

    return value.isdigit()

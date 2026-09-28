"""Custom exceptions for the map file parser.

Every exception here carries the line number and a clear reason, as
required by the subject: parsing errors must always tell the user
exactly where and why the map file is invalid.
"""

from __future__ import annotations


class MapParsingError(Exception):
    """Base class for every error raised while parsing a map file.

    Attributes:
        line_number: 1-based line number where the error occurred,
            or None if not tied to a specific line.
        reason: Human-readable explanation of what went wrong.
    """

    def __init__(self, reason: str, line_number: int | None = None) -> None:
        """Initialize a MapParsingError.

        Args:
            reason: Explanation of what went wrong.
            line_number: 1-based line number of the offending line,
                if known.
        """
        self.reason = reason
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {reason}"
        else:
            message = reason
        super().__init__(message)


class InvalidSyntaxError(MapParsingError):
    """Raised when a line does not match any known map instruction."""


class InvalidZoneTypeError(MapParsingError):
    """Raised when a zone declares an unrecognized `zone=` value."""


class DuplicateZoneError(MapParsingError):
    """Raised when the same zone name is declared more than once."""


class DuplicateConnectionError(MapParsingError):
    """Raised when the same connection (a-b or b-a) appears twice."""


class UnknownZoneReferenceError(MapParsingError):
    """Raised when a connection refers to a zone that was never declared."""


class InvalidMetadataError(MapParsingError):
    """Raised when a metadata value (e.g. max_drones) is not valid."""


class MissingHubError(MapParsingError):
    """Raised when the map has no start_hub or no end_hub."""


class DuplicateHubError(MapParsingError):
    """Raised when more than one start_hub or end_hub is declared."""

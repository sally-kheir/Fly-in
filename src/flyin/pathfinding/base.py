"""Abstract interface for pathfinding algorithms.

Defines the common contract every pathfinding algorithm must follow,
so the simulator can use any of them interchangeably (e.g. Dijkstra,
A*) without knowing their internal details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from flyin.models.graph import Graph


class PathfindingAlgorithm(ABC):
    """Common interface for all pathfinding algorithms.

    Any algorithm used to compute a route between two zones must
    implement `find_path` with this exact signature.
    """

    @abstractmethod
    def find_path(
        self, graph: Graph, start: str, end: str
    ) -> list[str]:
        """Compute the least-cost path between two zones.

        Args:
            graph: The network to search through.
            start: Name of the zone to start from.
            end: Name of the destination zone.

        Returns:
            An ordered list of zone names from start to end
            (inclusive), representing the least-cost path. Blocked
            zones must never appear in the result.

        Raises:
            ValueError: If no valid path exists between start and
                end (e.g. end is unreachable, or blocked zones cut
                off every route).
        """
        raise NotImplementedError

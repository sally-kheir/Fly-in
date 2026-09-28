"""Hand-written Dijkstra pathfinding algorithm with Dead-End Pruning.

No external graph library is used: this is a from-scratch
implementation of Dijkstra's algorithm.
"""

from __future__ import annotations

from flyin.models.graph import Graph
from flyin.models.zone import ZoneType
from flyin.pathfinding.base import PathfindingAlgorithm


ZONE_COLORS: dict[str, str] = {
    "START": "#a6e3a1",
    "GOAL": "#f9e2af",
    "NORMAL": "#89b4fa",
    "PRIORITY": "#cba6f7",
    "RESTRICTED": "#f9e2af",
    "BLOCKED": "#313244",
}


class Dijkstra(PathfindingAlgorithm):
    """Least-cost pathfinding with dead-end pruning."""

    def _get_valid_nodes(
        self,
        graph: Graph,
        end: str,
    ) -> set[str]:
        """Remove zones that cannot reach the goal using DFS."""

        can_reach_end: set[str] = set()
        visited: set[str] = set()

        def dfs_reach(node: str) -> bool:
            if node == end:
                return True

            if node in visited:
                return False

            visited.add(node)

            zone = graph.get_zone(node)

            if zone.is_blocked():
                return False

            for neighbor in graph.get_neighbors(node):
                if dfs_reach(neighbor):
                    can_reach_end.add(node)
                    return True

            return False

        for zone_name in graph.zones:
            visited.clear()
            dfs_reach(zone_name)

        can_reach_end.add(end)

        valid_nodes: set[str] = set(can_reach_end)

        for node in list(valid_nodes):
            if node == end:
                continue

            forward_neighbors = [
                neighbor
                for neighbor in graph.get_neighbors(node)
                if (
                    neighbor in valid_nodes
                    and not graph.get_zone(neighbor).is_blocked()
                )
            ]

            if not forward_neighbors:
                valid_nodes.discard(node)

        return valid_nodes

    def find_path(
        self,
        graph: Graph,
        start: str,
        end: str,
    ) -> list[str]:
        """Find the least-cost path from start to end."""

        if start not in graph.zones:
            raise ValueError(
                f"Unknown start zone: '{start}'."
            )

        if end not in graph.zones:
            raise ValueError(
                f"Unknown end zone: '{end}'."
            )

        valid_nodes = self._get_valid_nodes(
            graph,
            end,
        )

        if start not in valid_nodes:
            raise ValueError(
                f"Start zone '{start}' cannot reach "
                f"end zone '{end}'."
            )

        distances: dict[str, int] = {
            start: 0
        }

        previous: dict[str, str] = {}

        unvisited: set[str] = {
            start
        }

        visited: set[str] = set()

        while unvisited:
            current = self._closest_unvisited(
                unvisited,
                distances,
                graph,
            )

            unvisited.remove(current)
            visited.add(current)

            if current == end:
                break

            current_zone = graph.get_zone(current)

            if current_zone.is_blocked():
                continue

            for neighbor_name in graph.get_neighbors(current):
                if neighbor_name in visited:
                    continue

                if neighbor_name not in valid_nodes:
                    continue

                neighbor_zone = graph.get_zone(
                    neighbor_name
                )

                if neighbor_zone.is_blocked():
                    continue

                movement_cost = neighbor_zone.movement_cost

                new_distance = (
                    distances[current]
                    + movement_cost
                )

                known_distance = distances.get(
                    neighbor_name
                )

                if (
                    known_distance is None
                    or new_distance < known_distance
                ):
                    distances[neighbor_name] = (
                        new_distance
                    )

                    previous[neighbor_name] = (
                        current
                    )

                    unvisited.add(
                        neighbor_name
                    )

        if end not in distances:
            raise ValueError(
                f"No valid path found between "
                f"'{start}' and '{end}'."
            )

        return self._rebuild_path(
            previous,
            start,
            end,
        )

    def _closest_unvisited(
        self,
        unvisited: set[str],
        distances: dict[str, int],
        graph: Graph,
    ) -> str:
        """Return the closest zone.

        Priority zones are preferred when distances are equal.
        """

        def sorting_key(
            name: str,
        ) -> tuple[int, int]:

            distance = distances[name]

            zone = graph.get_zone(name)

            if zone.zone_type == ZoneType.PRIORITY:
                priority = 0
            else:
                priority = 1

            return (
                distance,
                priority,
            )

        return min(
            unvisited,
            key=sorting_key,
        )

    def _rebuild_path(
        self,
        previous: dict[str, str],
        start: str,
        end: str,
    ) -> list[str]:
        """Rebuild the path from end back to start."""

        path: list[str] = [end]
        current = end

        while current != start:
            previous_node = previous.get(current)

            if previous_node is None:
                break

            current = previous_node
            path.append(current)

        path.reverse()

        return path

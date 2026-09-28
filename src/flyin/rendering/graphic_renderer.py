"""Graphical (arcade-based) visualization of the drone simulation.

Renders zones and connections at their declared (x, y) coordinates,
and animates drones moving between them, automatically advancing one
turn every few seconds. This satisfies the subject's mandatory
visual-representation requirement as a graphical interface.
"""

from __future__ import annotations

import arcade

from flyin.models.graph import Graph

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_MARGIN = 90
ZONE_RADIUS = 18
DRONE_RADIUS = 6
DEFAULT_SECONDS_PER_TURN = 1.0


_EXTRA_COLOR_NAMES: dict[str, tuple[int, int, int]] = {
    "rainbow": (200, 60, 200),
    "darkred": (139, 0, 0),
    "lime": (50, 205, 50),
}
_DEFAULT_ZONE_COLOR = (150, 150, 150)


def resolve_color(name: str | None) -> tuple[int, int, int]:
    """Translate a map color name into an RGB tuple arcade can use.

    Args:
        name: Color name from the map file (e.g. "red"), or None.

    Returns:
        An (r, g, b) tuple. Falls back to a neutral gray if the name
        is unknown.
    """
    if name is None:
        return _DEFAULT_ZONE_COLOR

    key = name.strip().lower()
    if key in _EXTRA_COLOR_NAMES:
        return _EXTRA_COLOR_NAMES[key]

    attr = getattr(arcade.color, key.upper().replace(" ", "_"), None)
    if attr is None:
        return _DEFAULT_ZONE_COLOR
    return (attr[0], attr[1], attr[2])


def build_turn_snapshots(
    graph: Graph, nb_drones: int, output_lines: list[str]
) -> list[dict[str, str]]:
    """Replay the simulation output into a position snapshot per turn.

    Args:
        graph: The simulated network, used to find the start zone.
        nb_drones: Number of drones in the simulation.
        output_lines: The turn-by-turn output produced by Simulator.

    Returns:
        A list of snapshots (index 0 = initial state, before any
        turn). Each snapshot maps a drone_id to the zone or
        connection name it currently occupies.
    """
    positions: dict[str, str] = {
        f"D{i}": graph.start_zone_name or ""
        for i in range(1, nb_drones + 1)
    }
    snapshots: list[dict[str, str]] = [dict(positions)]

    for line in output_lines:
        for token in line.split():
            drone_id, destination = token.split("-", 1)
            positions[drone_id] = destination
        snapshots.append(dict(positions))

    return snapshots


def compute_screen_coordinates(
    graph: Graph,
    width: int = WINDOW_WIDTH,
    height: int = WINDOW_HEIGHT,
    margin: int = WINDOW_MARGIN,
) -> dict[str, tuple[float, float]]:
    """Map each zone's (x, y) map coordinates to screen pixels.

    Args:
        graph: The network whose zones need screen positions.
        width: Window width in pixels.
        height: Window height in pixels.
        margin: Empty border kept around the drawing area.

    Returns:
        A dict mapping each zone name to its (screen_x, screen_y).
    """
    xs = [zone.x for zone in graph.zones.values()]
    ys = [zone.y for zone in graph.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def scale(x: int, y: int) -> tuple[float, float]:
        if max_x == min_x:
            screen_x = width / 2
        else:
            screen_x = margin + (x - min_x) / (max_x - min_x) * (
                width - 2 * margin
            )
        if max_y == min_y:
            screen_y = height / 2
        else:
            screen_y = margin + (y - min_y) / (max_y - min_y) * (
                height - 2 * margin
            )
        return screen_x, screen_y

    return {
        name: scale(zone.x, zone.y) for name, zone in graph.zones.items()
    }


def compute_connection_midpoints(
    graph: Graph, coords: dict[str, tuple[float, float]]
) -> dict[str, tuple[float, float]]:
    """Compute the screen midpoint of each connection.

    Used to place drones that are mid-flight on a connection (not
    yet inside a zone).

    Args:
        graph: The network whose connections need midpoints.
        coords: Screen coordinates of every zone, from
            compute_screen_coordinates.

    Returns:
        A dict mapping each connection's canonical name to its
        (screen_x, screen_y) midpoint.
    """
    midpoints: dict[str, tuple[float, float]] = {}
    for connection in graph.connections:
        x1, y1 = coords[connection.zone_a]
        x2, y2 = coords[connection.zone_b]
        midpoints[connection.name] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return midpoints


class SimulationView(arcade.Window):
    """Arcade window animating the drone simulation turn by turn."""

    def __init__(
        self,
        graph: Graph,
        snapshots: list[dict[str, str]],
        seconds_per_turn: float = DEFAULT_SECONDS_PER_TURN,
    ) -> None:
        """Initialize the simulation window.

        Args:
            graph: The network to draw.
            snapshots: Per-turn drone positions, from
                build_turn_snapshots.
            seconds_per_turn: How long each turn is shown before
                automatically advancing to the next one.
        """
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Fly-in Simulation")
        arcade.set_background_color(arcade.color.WHITE)

        self.graph = graph
        self.snapshots = snapshots
        self.seconds_per_turn = seconds_per_turn
        self.current_turn = 0
        self.time_accumulator = 0.0
        self.finished = False

        self.zone_coords = compute_screen_coordinates(graph)
        self.connection_midpoints = compute_connection_midpoints(
            graph, self.zone_coords
        )

    def on_draw(self) -> None:
        """Render the current turn's state."""
        self.clear()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()
        self._draw_hud()

    def on_update(self, delta_time: float) -> None:
        """Advance the animation timer, moving to the next turn.

        Args:
            delta_time: Seconds elapsed since the last update call.
        """
        if self.finished:
            return

        self.time_accumulator += delta_time
        if self.time_accumulator < self.seconds_per_turn:
            return

        self.time_accumulator = 0.0
        if self.current_turn < len(self.snapshots) - 1:
            self.current_turn += 1
        else:
            self.finished = True

    def _draw_connections(self) -> None:
        for connection in self.graph.connections:
            x1, y1 = self.zone_coords[connection.zone_a]
            x2, y2 = self.zone_coords[connection.zone_b]
            arcade.draw_line(x1, y1, x2, y2, arcade.color.LIGHT_GRAY, 2)

    def _draw_zones(self) -> None:
        for name, zone in self.graph.zones.items():
            x, y = self.zone_coords[name]
            color = resolve_color(zone.color)
            arcade.draw_circle_filled(x, y, ZONE_RADIUS, color)
            arcade.draw_circle_outline(
                x, y, ZONE_RADIUS, arcade.color.BLACK, 2
            )
            arcade.draw_text(
                name,
                x,
                y + ZONE_RADIUS + 6,
                arcade.color.BLACK,
                10,
                anchor_x="center",
            )

    def _draw_drones(self) -> None:
        positions = self.snapshots[self.current_turn]
        by_location: dict[str, list[str]] = {}
        for drone_id, location in positions.items():
            by_location.setdefault(location, []).append(drone_id)

        for location, drone_ids in by_location.items():
            center = self.zone_coords.get(
                location
            ) or self.connection_midpoints.get(location)
            if center is None:
                continue
            x, y = center
            count = len(drone_ids)
            for index, drone_id in enumerate(sorted(drone_ids)):
                offset = (index - (count - 1) / 2) * (DRONE_RADIUS * 3)
                dx, dy = x + offset, y - ZONE_RADIUS - 14
                arcade.draw_circle_filled(
                    dx, dy, DRONE_RADIUS, arcade.color.RED
                )
                arcade.draw_text(
                    drone_id,
                    dx,
                    dy - 14,
                    arcade.color.RED,
                    8,
                    anchor_x="center",
                )

    def _draw_hud(self) -> None:
        total = len(self.snapshots) - 1
        label = f"Turn {self.current_turn}/{total}"
        if self.finished:
            label += "  (finished)"
        arcade.draw_text(
            label, 10, WINDOW_HEIGHT - 24, arcade.color.BLACK, 14
        )


def run_graphic_renderer(
    graph: Graph,
    nb_drones: int,
    output_lines: list[str],
    seconds_per_turn: float = DEFAULT_SECONDS_PER_TURN,
) -> None:
    """Launch the graphical visualization for a completed simulation.

    Args:
        graph: The simulated network.
        nb_drones: Number of drones in the simulation.
        output_lines: The turn-by-turn output produced by Simulator.
        seconds_per_turn: How long each turn is displayed before
            automatically advancing.
    """
    snapshots = build_turn_snapshots(graph, nb_drones, output_lines)
    SimulationView(graph, snapshots, seconds_per_turn)
    arcade.run()

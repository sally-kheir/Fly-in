"""Graphical UI renderer with detailed node statuses and visuals."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from flyin.models.graph import Graph
from flyin.models.zone import ZoneType


class GUIRenderer:
    """Tkinter GUI renderer with metrics, blockages, and animations."""

    RAINBOW_COLORS = (
        "#ff0000",
        "#ff7f00",
        "#ffff00",
        "#00ff00",
        "#00ffff",
        "#0000ff",
        "#8b00ff",
    )

    def __init__(
        self,
        graph: Graph,
        output_lines: list[str],
        width: int = 1200,
        height: int = 850,
        is_challenger: bool = False,
    ) -> None:
        self.graph = graph
        self.output_lines = output_lines
        self.width = width
        self.height = height
        self.is_challenger = is_challenger

        self.root = tk.Tk()
        self.root.title(
            "Fly-in Drone Routing Simulation - Detailed View"
        )
        self.root.geometry(f"{width}x{height}")

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(
            fill=tk.BOTH,
            expand=True
        )

        self.canvas = tk.Canvas(
            self.main_frame,
            bg="#181825"
        )

        self.h_scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )

        self.v_scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )

        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
        )

        self.h_scrollbar.pack(
            side=tk.BOTTOM,
            fill=tk.X
        )

        self.v_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        self.control_frame = tk.Frame(
            self.root,
            bg="#11111b",
            height=70
        )

        self.control_frame.pack(
            fill=tk.X,
            side=tk.BOTTOM
        )

        self.status_label = tk.Label(
            self.control_frame,
            text=f"Turn: 0 / {len(output_lines)}",
            fg="#cdd6f4",
            bg="#11111b",
            font=("Helvetica", 12, "bold"),
        )

        self.status_label.pack(
            side=tk.LEFT,
            padx=20,
            pady=15
        )

        self.btn_next = tk.Button(
            self.control_frame,
            text="Next Turn",
            command=self.next_turn,
            bg="#89b4fa",
            fg="#11111b",
            font=("Helvetica", 10, "bold"),
        )

        self.btn_next.pack(
            side=tk.RIGHT,
            padx=10,
            pady=15
        )

        self.btn_auto = tk.Button(
            self.control_frame,
            text="Auto Play",
            command=self.toggle_auto,
            bg="#a6e3a1",
            fg="#11111b",
            font=("Helvetica", 10, "bold"),
        )

        self.btn_auto.pack(
            side=tk.RIGHT,
            padx=10,
            pady=15
        )

        self.tooltip = tk.Label(
            self.canvas,
            text="",
            bg="#313244",
            fg="#cdd6f4",
            font=("Consolas", 9),
            justify=tk.LEFT,
            relief=tk.SOLID,
            bd=1,
            padx=8,
            pady=6,
        )

        self._compute_node_positions()

        self.current_turn = 0
        self.auto_playing = False
        self.animating = False

        self.drone_pos: dict[str, tuple[float, float]] = {}
        self.drone_logical_zone: dict[str, str] = {}

        start_zone = self.graph.get_start_zone().name

        start_coords = self.coords.get(
            start_zone,
            (100.0, 100.0)
        )

        for line in self.output_lines:
            for move in line.strip().split():
                if "-" in move:
                    d_id = move.split("-")[0]

                    if d_id not in self.drone_pos:
                        self.drone_pos[d_id] = start_coords
                        self.drone_logical_zone[d_id] = start_zone

        self.canvas.bind(
            "<Motion>",
            self._on_mouse_move
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

        self.draw_state()

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Scroll vertically with the mouse wheel."""

        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def _safe_color(
        self,
        color: str | None,
        fallback: str
    ) -> str:
        """Return a valid Tkinter color."""

        if not color:
            return fallback

        color = str(color).strip()

        if not color:
            return fallback

        try:
            self.root.winfo_rgb(color)
            return color
        except tk.TclError:
            return fallback

    def _get_zone_style(
        self,
        zone_name: str
    ) -> tuple[str, str, str, str]:
        """Return fill, border, style and label for a zone."""

        zone = self.graph.get_zone(zone_name)
        name = zone_name.lower()

        if name.startswith("dead_end"):
            return (
                "#000000",
                "#808080",
                "blocked",
                "BLOCKED"
            )

        if name.startswith("trap_loop"):
            color = self._safe_color(
                zone.color,
                "#313244"
            )

            return (
                color,
                color,
                "blocked",
                "BLOCKED"
            )

        if zone.zone_type == ZoneType.BLOCKED:
            color = self._safe_color(
                zone.color,
                "#313244"
            )

            return (
                color,
                color,
                "blocked",
                "BLOCKED"
            )

        color = self._safe_color(
            zone.color,
            "#89b4fa"
        )

        border_color = color

        if zone.is_start:
            return (
                color,
                border_color,
                "normal",
                "START"
            )

        if zone.is_end:
            return (
                color,
                border_color,
                "normal",
                "GOAL"
            )

        if zone.zone_type == ZoneType.RESTRICTED:
            return (
                color,
                border_color,
                "restricted",
                "RESTRICTED"
            )

        if zone.zone_type == ZoneType.PRIORITY:
            return (
                color,
                border_color,
                "normal",
                "PRIORITY"
            )

        return (
            color,
            border_color,
            "normal",
            "NORMAL"
        )

    def _draw_rainbow_goal(
        self,
        x: float,
        y: float,
        radius: float,
    ) -> None:
        """Draw a rainbow goal for Challenger Maps."""

        outer_radius = radius + 6
        inner_radius = radius - 5

        segment_count = len(self.RAINBOW_COLORS)
        extent = 360 / segment_count

        for index, color in enumerate(
            self.RAINBOW_COLORS
        ):
            start_angle = index * extent

            self.canvas.create_arc(
                x - outer_radius,
                y - outer_radius,
                x + outer_radius,
                y + outer_radius,
                start=start_angle,
                extent=extent,
                outline=color,
                width=8,
                style=tk.ARC,
            )

        self.canvas.create_oval(
            x - inner_radius,
            y - inner_radius,
            x + inner_radius,
            y + inner_radius,
            fill="#ffffff",
            outline="#ffffff",
            width=2,
        )

        self.canvas.create_text(
            x,
            y,
            text="GOAL",
            fill="#11111b",
            font=("Helvetica", 8, "bold"),
        )

    def _get_wait_time(self, zone: Any) -> int:
        """Safely fetch wait/delay time."""

        for attr in [
            "wait_time",
            "delay",
            "wait_turns",
            "wait"
        ]:
            if hasattr(zone, attr):
                val = getattr(zone, attr)

                if isinstance(val, int):
                    return val

        return 0

    def _compute_node_positions(self) -> None:
        """Transform graph coordinates into canvas space."""

        zones = list(self.graph.zones.values())

        if not zones:
            self.coords: dict[
                str,
                tuple[float, float]
            ] = {}
            return

        xs = [z.x for z in zones]
        ys = [z.y for z in zones]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        dx = (
            max_x - min_x
            if max_x != min_x
            else 1
        )

        dy = (
            max_y - min_y
            if max_y != min_y
            else 1
        )

        margin = 150
        usable_w = 2200
        usable_h = 1200

        self.coords = {}

        for zone in zones:
            px = (
                margin
                + ((zone.x - min_x) / dx)
                * usable_w
            )

            py = (
                margin
                + ((zone.y - min_y) / dy)
                * usable_h
            )

            self.coords[zone.name] = (
                px,
                py
            )

    def draw_state(self) -> None:
        """Redraw graph, nodes, labels and drones."""

        self.canvas.delete("all")

        for conn in self.graph.connections:

            if (
                conn.zone_a in self.coords
                and conn.zone_b in self.coords
            ):
                x1, y1 = self.coords[conn.zone_a]
                x2, y2 = self.coords[conn.zone_b]

                self.canvas.create_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill="#45475a",
                    width=3
                )

        radius = 24

        for name, (x, y) in self.coords.items():

            zone = self.graph.get_zone(name)

            (
                fill_col,
                border_col,
                style,
                tag
            ) = self._get_zone_style(name)

            wait_t = self._get_wait_time(zone)

            width = (
                4
                if style in [
                    "blocked",
                    "restricted"
                ]
                else 2
            )

            dash_pattern = (
                (4, 4)
                if style == "blocked"
                else ()
            )

            if zone.is_end and self.is_challenger:

                self._draw_rainbow_goal(
                    x,
                    y,
                    radius
                )

            else:

                self.canvas.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=fill_col,
                    outline=border_col,
                    width=width,
                    dash=dash_pattern,
                )

            self.canvas.create_text(
                x,
                y - radius - 10,
                text=name,
                fill="#cdd6f4",
                font=("Helvetica", 9, "bold"),
            )

            if wait_t > 0:

                self.canvas.create_text(
                    x,
                    y + radius + 12,
                    text=f"Wait: {wait_t}t",
                    fill="#a6adc8",
                    font=("Consolas", 8, "bold"),
                )

            self.canvas.create_text(
                x,
                y + radius + 24,
                text=f"[{tag}]",
                fill=(
                    "#ffffff"
                    if zone.is_end
                    and self.is_challenger
                    else border_col
                ),
                font=("Helvetica", 7, "bold"),
            )

        for d_id, (dx, dy) in self.drone_pos.items():

            self._draw_drone(
                dx,
                dy,
                d_id
            )

        self.canvas.update_idletasks()

        self.canvas.config(
            scrollregion=self.canvas.bbox("all")
        )

    def _draw_drone(
        self,
        x: float,
        y: float,
        drone_id: str
    ) -> None:
        """Render a single drone."""

        r = 10

        self.canvas.create_oval(
            x - r,
            y - r,
            x + r,
            y + r,
            fill="#f9e2af",
            outline="#11111b",
            width=1.5,
        )

        self.canvas.create_text(
            x,
            y,
            text=drone_id,
            fill="#11111b",
            font=("Helvetica", 7, "bold"),
        )

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Show zone information on hover."""

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        hovered_zone = None

        for name, (x, y) in self.coords.items():

            if (
                (canvas_x - x) ** 2
                + (canvas_y - y) ** 2
                <= 24 ** 2
            ):
                hovered_zone = name
                break

        if hovered_zone:

            zone = self.graph.get_zone(
                hovered_zone
            )

            current = sum(
                1
                for loc in (
                    self.drone_logical_zone.values()
                )
                if loc == hovered_zone
            )

            cap = (
                zone.max_drones
                if zone.max_drones is not None
                else "Unlimited"
            )

            wait_t = self._get_wait_time(zone)

            text = (
                f"Zone: {zone.name}\n"
                f"Type: {zone.zone_type.value}\n"
                f"Coordinates: "
                f"({zone.x}, {zone.y})\n"
                f"Drones: {current} / {cap}\n"
                f"Wait Time: {wait_t} turns\n"
                f"Color: {zone.color or 'N/A'}"
            )

            self.tooltip.config(
                text=text
            )

            self.tooltip.place(
                x=event.x + 15,
                y=event.y + 15
            )

        else:
            self.tooltip.place_forget()

    def _resolve_target_coords(
        self,
        dest: str
    ) -> tuple[float, float] | None:
        """Resolve destination to canvas coordinates."""

        if dest in self.coords:
            return self.coords[dest]

        if "-" in dest:

            parts = dest.split("-")

            if (
                len(parts) == 2
                and parts[0] in self.coords
                and parts[1] in self.coords
            ):
                x1, y1 = self.coords[parts[0]]
                x2, y2 = self.coords[parts[1]]

                return (
                    (x1 + x2) / 2.0,
                    (y1 + y2) / 2.0
                )

        return None

    def next_turn(self) -> None:
        """Trigger one turn animation step."""

        if (
            self.animating
            or self.current_turn
            >= len(self.output_lines)
        ):
            return

        line = self.output_lines[
            self.current_turn
        ]

        moves = line.strip().split()

        targets: dict[
            str,
            tuple[float, float]
        ] = {}

        new_logical: dict[str, str] = {}

        for move in moves:

            if "-" in move:

                drone_id, dest = move.split(
                    "-",
                    1
                )

                coords = (
                    self._resolve_target_coords(dest)
                )

                if coords:

                    targets[drone_id] = coords
                    new_logical[drone_id] = dest

        if targets:

            self.animating = True

            self._animate_move(
                targets,
                new_logical,
                step=0,
                max_steps=15
            )

        else:

            self.current_turn += 1

            self.status_label.config(
                text=(
                    f"Turn: {self.current_turn} / "
                    f"{len(self.output_lines)}"
                )
            )

    def _animate_move(
        self,
        targets: dict[
            str,
            tuple[float, float]
        ],
        new_logical: dict[str, str],
        step: int,
        max_steps: int,
    ) -> None:
        """Animate drone movement."""

        if step < max_steps:

            for d_id, (
                target_x,
                target_y
            ) in targets.items():

                start_x, start_y = (
                    self.drone_pos[d_id]
                )

                new_x = (
                    start_x
                    + (
                        target_x - start_x
                    ) / (max_steps - step)
                )

                new_y = (
                    start_y
                    + (
                        target_y - start_y
                    ) / (max_steps - step)
                )

                self.drone_pos[d_id] = (
                    new_x,
                    new_y
                )

            self.draw_state()

            self.root.after(
                25,
                lambda: self._animate_move(
                    targets,
                    new_logical,
                    step + 1,
                    max_steps
                ),
            )

        else:

            for d_id, target in targets.items():

                self.drone_pos[d_id] = target

                if d_id in new_logical:
                    self.drone_logical_zone[d_id] = (
                        new_logical[d_id]
                    )

            self.current_turn += 1

            self.status_label.config(
                text=(
                    f"Turn: {self.current_turn} / "
                    f"{len(self.output_lines)}"
                )
            )

            self.draw_state()

            self.animating = False

            if self.auto_playing:

                self.root.after(
                    300,
                    self._auto_step
                )

    def toggle_auto(self) -> None:
        """Toggle auto-play mode."""

        self.auto_playing = (
            not self.auto_playing
        )

        if self.auto_playing:

            self.btn_auto.config(
                text="Pause",
                bg="#f38ba8"
            )

            self._auto_step()

        else:

            self.btn_auto.config(
                text="Auto Play",
                bg="#a6e3a1"
            )

    def _auto_step(self) -> None:
        """Automatically step forward."""

        if (
            self.auto_playing
            and self.current_turn
            < len(self.output_lines)
        ):
            self.next_turn()

        else:

            self.auto_playing = False

            self.btn_auto.config(
                text="Auto Play",
                bg="#a6e3a1"
            )

    def start(self) -> None:
        """Start the GUI loop."""

        self.root.mainloop()


def render_gui_simulation(
    graph: Graph,
    output_lines: list[str],
    is_challenger: bool = False,
) -> None:
    """Start the GUI simulation."""

    gui = GUIRenderer(
        graph,
        output_lines,
        is_challenger=is_challenger,
    )

    gui.start()

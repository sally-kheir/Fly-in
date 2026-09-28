*This project has been created as part of the 42 curriculum by skheir.*

## Description & Algorithm

Fly-In is a Python multi-drone pathfinding and simulation engine based on **Dijkstra's algorithm**.

The project handles:

* Shortest-path calculation
* Multi-drone movement
* Colllision avoidance
* Time-based reservations
* Dead-end pruning
* Zone and connection capacity management
* Restricted and priority zones
* CLI and GUI modes
* Custom map parsing and error handling
* Graphical visualization of the map, zones, connections, and drone movements

The main flow is:

```text
Map → Parser → Tokenizer → Graph → Dijkstra → Simulator → Terminal / GUI
```

## Visualization

The project includes a **graphical interface built with Tkinter** to visualize the simulation.

The GUI displays:

* The different zones of the map
* Connections between zones
* Zone types and colors
* Zone capacities
* Drone positions and movements
* The simulation progress turn by turn

## Output Example

```text
D1-waypoint1

D1-waypoint2 D2-waypoint1

D1-goal D2-waypoint2

D2-goal
```

## Instructions

Install the required dependencies:

```bash
pip install -r requirements.txt
```
## Code Quality

Run Flake8:

```bash
flake8 src/flyin
```

Run Mypy:

```bash
mypy src/flyin
```

Ruff can automatically fix many style issues:

```bash
ruff check . --fix
```
Run code :
```
make run
PYTHONPATH=src python3 -m flyin maps/medium/02_circular_loop.txt --gui
```
## Resources

* Python Documentation
* Dijkstra's Algorithm
* Graph Theory
* Tkinter Documentation
* Flake8 Doc*

"""Issue #10 checks for the occupancy grid and world/grid conversion helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np


# This only saves a PNG, so use a backend that does not open a window.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-check-grid")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# Paths are built from this file's location so the script can be run from the
# repo root without needing hard-coded absolute paths.
WEBOTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEBOTS_ROOT.parent
CONTROLLER_DIR = WEBOTS_ROOT / "controllers" / "group_project_controller"

# Use the helper functions already supplied with the project.
# Do not copy the conversion logic into this file.
sys.path.insert(0, str(CONTROLLER_DIR))
from project_utils import CONFIG, grid_to_world, world_to_grid  # noqa: E402


GRID_PATH = WEBOTS_ROOT / "maps" / "occupancy_grid.npy"
INFO_PATH = WEBOTS_ROOT / "maps" / "occupancy_grid_info.json"
LAYOUT_PATH = WEBOTS_ROOT / "maps" / "world_layout.png"

# These are the two output files for Issue #10: a visual overlay and a short
# Markdown summary of the checks.
OVERLAY_PATH = REPO_ROOT / "docs" / "data" / "grid_overlay.png"
REPORT_PATH = REPO_ROOT / "docs" / "grid_check.md"


def report(name: str, passed: bool, detail: str = "") -> bool:
    # Print each check clearly and keep the result for the final overall result.
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {name}{suffix}")
    return passed


def in_bounds(row: int, col: int, rows: int, cols: int) -> bool:
    # Grid indexes must stay between 0 and 39 for this 40 x 40 map.
    return 0 <= row < rows and 0 <= col < cols


def cell_is_free(grid: np.ndarray, row: int, col: int) -> bool:
    # Starts and observe points should be inside the grid and on free cells.
    return in_bounds(row, col, *grid.shape) and int(grid[row, col]) == 0


def full_round_trip(rows: int, cols: int) -> list[tuple[int, int, tuple[int, int]]]:
    """Check every grid cell: grid -> world centre -> grid."""
    # For each grid cell, convert it to the world coordinate at the cell centre.
    # Then convert that world coordinate back into a grid cell. If the helpers
    # are consistent, we should get exactly the original row and column.
    failures = []
    for row in range(rows):
        for col in range(cols):
            x, y = grid_to_world(row, col)
            actual = world_to_grid(x, y)
            if actual != (row, col):
                failures.append((row, col, actual))
    return failures


def world_coordinate_sweep(metadata: dict) -> list[tuple]:
    """Sweep world-space cell centres and check they map back to themselves."""
    # This uses the arena bounds and resolution to make world coordinates across
    # the map, then checks that they still match the correct grid cells.
    x_min = metadata["x_min"]
    y_max = metadata["y_max"]
    resolution = metadata["resolution_m_per_cell"]
    rows = metadata["rows"]
    cols = metadata["cols"]
    failures = []

    for row in range(rows):
        for col in range(cols):
            # Use the cell centre so the point is not sitting on a boundary.
            expected_x = x_min + (col + 0.5) * resolution
            expected_y = y_max - (row + 0.5) * resolution
            actual_row, actual_col = world_to_grid(expected_x, expected_y)

            # If a point from inside the arena maps outside the grid, the world
            # to grid conversion is wrong.
            if not in_bounds(actual_row, actual_col, rows, cols):
                failures.append((expected_x, expected_y, (actual_row, actual_col), "out of bounds"))
                continue

            # Convert back to world coordinates and make sure we are still at
            # the same cell centre.
            actual_x, actual_y = grid_to_world(actual_row, actual_col)
            if not np.allclose((actual_x, actual_y), (expected_x, expected_y), atol=1e-9):
                failures.append((expected_x, expected_y, (actual_row, actual_col), (actual_x, actual_y)))

    return failures


def collect_config_points(grid: np.ndarray) -> tuple[list[dict], list[dict]]:
    """Read starts and station observe positions directly from CONFIG."""
    # Read these from CONFIG so they stay matched to project_config.json.
    starts = []
    stations = []

    # Starts have an (x, y, heading) pose. For the grid check we only need x,y.
    for start in CONFIG["starts"]:
        x, y, _ = start["pose"]
        row, col = world_to_grid(x, y)
        starts.append(
            {
                "id": start["id"],
                "x": x,
                "y": y,
                "row": row,
                "col": col,
                "in_bounds": in_bounds(row, col, *grid.shape),
                "free": cell_is_free(grid, row, col),
            }
        )

    # Station observe positions are already stored as (x, y) points.
    for station in CONFIG["stations"]:
        x, y = station["observe"]
        row, col = world_to_grid(x, y)
        stations.append(
            {
                "id": station["id"],
                "x": x,
                "y": y,
                "row": row,
                "col": col,
                "in_bounds": in_bounds(row, col, *grid.shape),
                "free": cell_is_free(grid, row, col),
            }
        )

    return starts, stations


def save_overlay(grid: np.ndarray, metadata: dict, starts: list[dict], stations: list[dict]) -> None:
    """Draw the grid in world coordinates and overlay start/observe positions."""
    # This overlay is for comparing the grid with maps/world_layout.png.
    x_min = metadata["x_min"]
    x_max = metadata["x_max"]
    y_min = metadata["y_min"]
    y_max = metadata["y_max"]

    OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 7))
    # Put the image onto Webots world axes. Row 0 is at the top of the arena.
    # Black cells are obstacles and white cells are free space.
    ax.imshow(
        grid,
        cmap="Greys",
        origin="upper",
        extent=[x_min, x_max, y_min, y_max],
        interpolation="none",
    )

    start_x = [point["x"] for point in starts]
    start_y = [point["y"] for point in starts]
    station_x = [point["x"] for point in stations]
    station_y = [point["y"] for point in stations]

    # Blue circles mark starts. Red crosses mark station observe positions.
    ax.scatter(start_x, start_y, marker="o", s=90, color="tab:blue", label="Starts A-C")
    ax.scatter(station_x, station_y, marker="x", s=90, color="tab:red", label="Station observe S1-S8")

    # Add labels so the image can be compared against maps/world_layout.png.
    for point in starts:
        ax.annotate(f"Start {point['id']}", (point["x"], point["y"]), xytext=(5, 5), textcoords="offset points")
    for point in stations:
        ax.annotate(point["id"], (point["x"], point["y"]), xytext=(5, 5), textcoords="offset points")

    ax.set_title("Occupancy grid with start and station observe positions")
    ax.set_xlabel("World x (m)")
    ax.set_ylabel("World y (m)")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.3, alpha=0.5)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(OVERLAY_PATH, dpi=200)
    plt.close(fig)


def write_markdown_report(
    grid: np.ndarray,
    metadata: dict,
    actual_values: list[int],
    round_trip_failures: list,
    sweep_failures: list,
    starts: list[dict],
    stations: list[dict],
) -> None:
    # Keep the report short and only include the Issue #10 results.
    def point_rows(points: list[dict]) -> str:
        # Use the same table format for starts and station observe points.
        return "\n".join(
            f"| {p['id']} | `({p['x']:.2f}, {p['y']:.2f})` | `({p['row']}, {p['col']})` | "
            f"{p['in_bounds']} | {p['free']} |"
            for p in points
        )

    table_header = "| ID | World `(x, y)` | Grid `(row, col)` | In bounds | Free cell |\n|---|---:|---:|---|---|"

    report_text = f"""# Grid Check

## Grid
- Shape: `{grid.shape}`
- Unique values: `{actual_values}`
- Metadata: `{metadata['rows']} rows x {metadata['cols']} cols`
- Resolution: `{metadata['resolution_m_per_cell']} m/cell`
- Encoding: `{metadata['encoding']['free']} = free`, `{metadata['encoding']['obstacle']} = obstacle`

## Conversion
- 1600-cell round-trip failures: `{len(round_trip_failures)}`
- World-coordinate sweep failures/out-of-bounds: `{len(sweep_failures)}`

## Starts
{table_header}
{point_rows(starts)}

## Station Observe Positions
{table_header}
{point_rows(stations)}

## Overlay
- Generated overlay: `{OVERLAY_PATH.relative_to(REPO_ROOT)}`
- Manually compared with `{LAYOUT_PATH.relative_to(WEBOTS_ROOT)}`.
"""

    REPORT_PATH.write_text(report_text)


def main() -> int:
    # Load the supplied grid and metadata. This does not edit the grid file.
    grid = np.load(GRID_PATH)
    metadata = json.loads(INFO_PATH.read_text())
    rows, cols = grid.shape
    actual_values = sorted(int(value) for value in np.unique(grid))
    encoding = metadata["encoding"]

    # First check the grid file and metadata are what the project expects.
    # These are objective checks, so a failure should make the script return a
    # non-zero exit status.
    results = [
        report("grid shape is exactly (40, 40)", grid.shape == (40, 40), f"{grid.shape}"),
        report("unique grid values are exactly [0, 1]", actual_values == [0, 1], f"{actual_values}"),
        report("metadata rows and cols are 40 x 40", metadata["rows"] == 40 and metadata["cols"] == 40),
        report("resolution is 0.1 m/cell", metadata["resolution_m_per_cell"] == 0.1),
        report("encoding is 0 = free and 1 = obstacle", encoding["free"] == 0 and encoding["obstacle"] == 1),
    ]

    print("\nFull grid round-trip")
    # This reports the number of failures, as required by Issue #10.
    round_trip_failures = full_round_trip(rows, cols)
    results.append(report("all 1600 cells round-trip exactly", len(round_trip_failures) == 0, f"{len(round_trip_failures)} failures"))

    print("\nWorld-coordinate sweep")
    # This is a second conversion check using world coordinates made from the
    # supplied map bounds and resolution.
    sweep_failures = world_coordinate_sweep(metadata)
    results.append(report("world-coordinate sweep has no failures", len(sweep_failures) == 0, f"{len(sweep_failures)} failures"))

    starts, stations = collect_config_points(grid)

    print("\nStart free-cell checks")
    # These checks make sure later navigation code will start from valid cells.
    for point in starts:
        detail = f"{point['id']} -> ({point['row']}, {point['col']}), free={point['free']}"
        results.append(report(f"start {point['id']} is in bounds and free", point["in_bounds"] and point["free"], detail))

    print("\nStation observe free-cell checks")
    # These checks make sure each observation pose is reachable in the map, at
    # least at the occupancy-grid level.
    for point in stations:
        detail = f"{point['id']} -> ({point['row']}, {point['col']}), free={point['free']}"
        results.append(report(f"station {point['id']} observe is in bounds and free", point["in_bounds"] and point["free"], detail))

    # Save the overlay image and the short Markdown summary.
    save_overlay(grid, metadata, starts, stations)
    write_markdown_report(grid, metadata, actual_values, round_trip_failures, sweep_failures, starts, stations)

    results.append(report("overlay figure saved", OVERLAY_PATH.exists(), str(OVERLAY_PATH.relative_to(REPO_ROOT))))
    results.append(report("grid check report saved", REPORT_PATH.exists(), str(REPORT_PATH.relative_to(REPO_ROOT))))
    print(f"Manually compared {OVERLAY_PATH.relative_to(REPO_ROOT)} with maps/world_layout.png.")

    overall = all(results)
    print(f"\nOVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

# Report Section 3.2 -- component contract: Telemetry takes state/pose/label/
# time and writes/flushes as it goes, so a run stopped part way still leaves
# usable data. Also the source of Section 7's mission_summary.csv figures.
"""Telemetry (Issue #18): per-run interval CSV and the committed summary row.

Two files per Mission run:
  - an interval-sampled CSV under runs/ (gitignored -- raw per-run detail, not
    something the report cites directly), one row every TELEMETRY_LOG_INTERVAL_STEPS
    control steps so logging stays cheap
  - one appended row in the committed docs/data/mission_summary.csv, the source
    table for the report's completion-time figures
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

# The column headings for the two CSV files. The values we write later are put
# in these same orders, so each number lands under the right heading.
INTERVAL_FIELDS = [
    "sim_time", "state", "x", "y", "yaw", "station", "label", "confidence",
    "behaviour", "max_proximity",
]
SUMMARY_FIELDS = [
    "run_timestamp", "start_id", "target", "station", "final_distance",
    "completion_time", "outcome",
]


# Report Section 3.2/6.3 -- the Telemetry component itself, driven by
# Mission._log_telemetry_row() / Mission._finish() in the controller
class TelemetryLogger:
    """Writes the interval row straight to disk (flushed) as each one is logged,
    rather than buffering in memory -- a Webots controller can be killed by
    pressing Stop mid-mission, and a buffered log would lose everything from a
    run that never reached its own summary write.
    """

    # Opens the per-run CSV and writes its heading row. If logging is turned
    # off we do nothing at all, so no files get created.
    def __init__(self, runs_dir, summary_path, enabled=True):
        self.enabled = enabled
        self.summary_path = Path(summary_path)
        self._file = None
        self._writer = None
        self.interval_path = None
        self.run_timestamp = None
        if self.enabled:
            runs_dir = Path(runs_dir)
            runs_dir.mkdir(parents=True, exist_ok=True)
            # A timestamp in the file name keeps each run's CSV separate.
            self.run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self.interval_path = runs_dir / f"run_{self.run_timestamp}.csv"
            self._file = self.interval_path.open("w", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(INTERVAL_FIELDS)

    # Add one line to this run's CSV describing where the robot is and what
    # it is doing right now. flush() pushes it to disk straight away.
    # Report Section 3.2 -- one interval row (state/pose/label/behaviour), the
    # raw per-run detail behind the gitignored runs/ CSVs
    def log_step(self, sim_time, state, x, y, yaw, station, label, confidence,
                 behaviour, max_proximity):
        if not self.enabled:
            return
        row = [sim_time, state, x, y, yaw, station, label, confidence,
               behaviour, max_proximity]
        self._writer.writerow(row)
        self._file.flush()

    # Called once at the end of the mission. Closes this run's CSV, then adds
    # one line to the shared summary file that the report uses.
    # Report Section 7.2 -- appends the one summary row per run that Table 13
    # /14's headline results (mean completion time, worst final distance,
    # outcome) are computed from
    def log_summary(self, start_id, target, station, final_distance,
                    completion_time, outcome):
        if not self.enabled:
            return
        if self._file is not None:
            self._file.close()
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        # Only write the heading row the very first time the file is made.
        write_header = not self.summary_path.exists()
        row = [self.run_timestamp, start_id, target, station, final_distance,
               completion_time, outcome]
        with self.summary_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(SUMMARY_FIELDS)
            writer.writerow(row)

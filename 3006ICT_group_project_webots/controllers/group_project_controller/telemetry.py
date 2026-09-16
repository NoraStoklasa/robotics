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

INTERVAL_FIELDS = [
    "sim_time", "state", "x", "y", "yaw", "station", "label", "confidence",
    "behaviour", "max_proximity",
]
SUMMARY_FIELDS = [
    "run_timestamp", "start_id", "target", "station", "final_distance",
    "completion_time", "outcome",
]


class TelemetryLogger:
    """Writes the interval row straight to disk (flushed) as each one is logged,
    rather than buffering in memory -- a Webots controller can be killed by
    pressing Stop mid-mission, and a buffered log would lose everything from a
    run that never reached its own summary write.
    """

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
            self.run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self.interval_path = runs_dir / f"run_{self.run_timestamp}.csv"
            self._file = self.interval_path.open("w", newline="")
            self._writer = csv.DictWriter(self._file, fieldnames=INTERVAL_FIELDS)
            self._writer.writeheader()

    def log_step(self, **fields):
        if not self.enabled:
            return
        self._writer.writerow(fields)
        self._file.flush()

    def log_summary(self, **fields):
        if not self.enabled:
            return
        if self._file is not None:
            self._file.close()
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.summary_path.exists()
        with self.summary_path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({"run_timestamp": self.run_timestamp, **fields})

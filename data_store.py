"""CSV-backed persistence for student records."""

from pathlib import Path

import pandas as pd

COLUMNS = [
    "student_name",
    "subject",
    "marks",
    "attendance_pct",
    "assignments_done",
    "target_marks",
    "target_cgpa",
    "timestamp",
]


def load_records(path):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path)


def append_record(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row], columns=COLUMNS)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)

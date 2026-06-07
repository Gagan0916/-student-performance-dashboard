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


REQUIRED_COLUMNS = ["student_name", "subject", "marks", "attendance_pct"]
OPTIONAL_DEFAULTS = {
    "assignments_done": 0,
    "target_marks": 0,
    "target_cgpa": 0.0,
    "timestamp": "uploaded",
}


def prepare_uploaded_df(df):
    """Validates an uploaded DataFrame against the app schema and fills in any
    optional columns with sensible defaults. Raises ValueError on missing
    required columns."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected at least: {', '.join(REQUIRED_COLUMNS)}."
        )

    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default

    df["student_name"] = df["student_name"].astype(str).str.strip()
    df["subject"] = df["subject"].astype(str).str.strip()
    df["marks"] = pd.to_numeric(df["marks"], errors="coerce").fillna(0).astype(int)
    df["attendance_pct"] = pd.to_numeric(df["attendance_pct"], errors="coerce").fillna(0).astype(int)
    df["assignments_done"] = pd.to_numeric(df["assignments_done"], errors="coerce").fillna(0).astype(int)
    df["target_marks"] = pd.to_numeric(df["target_marks"], errors="coerce").fillna(0).astype(int)
    df["target_cgpa"] = pd.to_numeric(df["target_cgpa"], errors="coerce").fillna(0.0)
    df["timestamp"] = df["timestamp"].astype(str)

    df = df.dropna(subset=["student_name", "subject"])
    df = df[(df["student_name"] != "") & (df["subject"] != "")]

    return df[COLUMNS].reset_index(drop=True)


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

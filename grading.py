"""Grading config and pure calculation helpers. Tune the constants below for RCEE's pattern."""

# (minimum score inclusive, letter grade, display color)
GRADE_BANDS = [
    (90, "A", "green"),
    (75, "B", "green"),
    (60, "C", "yellow"),
    (40, "D", "yellow"),
    (0, "F", "red"),
]

GRADE_POINTS = {"A": 10, "B": 8, "C": 6, "D": 4, "F": 0}

ATTENDANCE_THRESHOLD = 75


def score_to_grade(score):
    for minimum, label, color in GRADE_BANDS:
        if score >= minimum:
            return label, color
    return GRADE_BANDS[-1][1], GRADE_BANDS[-1][2]


def grade_point(label):
    return GRADE_POINTS.get(label, 0)


def compute_cgpa(rows):
    if not rows:
        return 0.0
    points = [grade_point(score_to_grade(row["marks"])[0]) for row in rows]
    return round(sum(points) / len(points), 2)


def attendance_status(pct):
    """Returns True when attendance is below the risk threshold."""
    return pct < ATTENDANCE_THRESHOLD

"""Class-average comparison and goal-progress calculations."""


def subject_class_average(df, subject):
    matches = df[df["subject"] == subject]["marks"]
    if matches.empty:
        return None
    return round(matches.mean(), 2)


def compare_to_class(current_rows, df):
    comparison = []
    for row in current_rows:
        avg = subject_class_average(df, row["subject"])
        comparison.append({
            "subject": row["subject"],
            "your_marks": row["marks"],
            "class_average": avg,
            "delta": None if avg is None else round(row["marks"] - avg, 2),
        })
    return comparison


def goal_progress(current_value, target_value):
    if not target_value or target_value <= 0:
        return None
    progress_pct = max(0, min(100, round((current_value / target_value) * 100, 1)))
    gap = round(max(0, target_value - current_value), 2)
    return {
        "progress_pct": progress_pct,
        "gap": gap,
        "met": current_value >= target_value,
    }

"""Class-average comparison and goal-progress calculations."""

from grading import attendance_status, compute_cgpa, score_to_grade


def class_overview(df):
    """Computes class-wide stats from an uploaded records DataFrame."""
    if df.empty:
        return None

    grades = df["marks"].apply(lambda m: score_to_grade(m)[1])
    grade_counts = {
        "green": int((grades == "green").sum()),
        "yellow": int((grades == "yellow").sum()),
        "red": int((grades == "red").sum()),
    }

    flagged = df[df["attendance_pct"].apply(attendance_status)]
    at_risk_students = sorted(flagged["student_name"].dropna().unique().tolist())

    subject_avgs = (
        df.groupby("subject")["marks"].mean().round(2).sort_values(ascending=False)
    )

    student_cgpas = []
    for name, group in df.groupby("student_name"):
        student_cgpas.append({"student_name": name, "cgpa": compute_cgpa(group.to_dict("records"))})
    student_cgpas.sort(key=lambda s: s["cgpa"], reverse=True)

    return {
        "num_students": df["student_name"].nunique(),
        "num_subjects": df["subject"].nunique(),
        "num_records": len(df),
        "avg_marks": round(df["marks"].mean(), 2),
        "avg_attendance": round(df["attendance_pct"].mean(), 2),
        "grade_counts": grade_counts,
        "at_risk_students": at_risk_students,
        "subject_averages": subject_avgs,
        "top_students": student_cgpas[:3],
        "bottom_students": student_cgpas[-3:][::-1] if len(student_cgpas) > 3 else [],
    }


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

"""AI-generated study insights, backed by Gemini with rule-based fallbacks.

Every public function returns (text, source) where source is "gemini" or "fallback",
so the UI can show where the insight came from. Gemini failures of any kind (missing
key, network, rate limit) silently fall back — the dashboard never breaks.
"""

import os

from grading import attendance_status, score_to_grade

_MODEL_NAME = "gemini-2.0-flash"


def _call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        text = (response.text or "").strip()
        return text or None
    except Exception:
        return None


def _weakest_subject(rows):
    return min(rows, key=lambda r: r["marks"])


# ---------------------------------------------------------------------------
# Focus tip
# ---------------------------------------------------------------------------

def generate_tip(subject_rows):
    if not subject_rows:
        return "Add at least one subject to get a personalized tip.", "fallback"

    prompt = (
        "You are a supportive academic mentor. In ONE short sentence, tell the "
        "student which subject to focus on next and why, based on this data "
        f"(subject, marks out of 100, attendance %): {_rows_summary(subject_rows)}. "
        "Be specific and encouraging, no preamble."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    weak = _weakest_subject(subject_rows)
    return (
        f"Focus on {weak['subject']} - your score of {weak['marks']} is borderline, "
        "a bit more practice there will help most.",
        "fallback",
    )


# ---------------------------------------------------------------------------
# Narrative summary
# ---------------------------------------------------------------------------

def generate_summary(subject_rows, cgpa):
    if not subject_rows:
        return "Add subjects to see a performance summary.", "fallback"

    prompt = (
        "You are an academic advisor. Write a warm, 2-3 sentence overview of this "
        f"student's standing. CGPA: {cgpa}. Subjects (name, marks/100, attendance %): "
        f"{_rows_summary(subject_rows)}. Mention strengths, weak spots, and any "
        "attendance risk. No preamble, no markdown."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    grades = [score_to_grade(r["marks"]) for r in subject_rows]
    greens = sum(1 for _, color in grades if color == "green")
    yellows = sum(1 for _, color in grades if color == "yellow")
    reds = sum(1 for _, color in grades if color == "red")
    flagged = [r["subject"] for r in subject_rows if attendance_status(r["attendance_pct"])]

    parts = [f"Your current CGPA is {cgpa}, with {greens} strong, {yellows} average, "
             f"and {reds} weak subject(s)."]
    if flagged:
        parts.append(f"Attendance is below 75% in {', '.join(flagged)} - keep an eye on that.")
    else:
        parts.append("Attendance looks healthy across all subjects.")
    weak = _weakest_subject(subject_rows)
    parts.append(f"{weak['subject']} is your area with the most room to grow.")
    return " ".join(parts), "fallback"


# ---------------------------------------------------------------------------
# Weekly study plan
# ---------------------------------------------------------------------------

def generate_study_plan(subject_rows):
    if not subject_rows:
        return "Add subjects to get a weekly study plan.", "fallback"

    prompt = (
        "You are a study coach. Create a short weekly study plan (Mon-Sun, a few "
        "lines max) that prioritizes the weakest subjects, based on this data "
        f"(subject, marks out of 100, attendance %): {_rows_summary(subject_rows)}. "
        "Keep it concrete and brief, plain text with line breaks, no markdown headers."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    ranked = sorted(subject_rows, key=lambda r: r["marks"])
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    lines = []
    for i, day in enumerate(days):
        subject = ranked[i % len(ranked)]["subject"]
        lines.append(f"{day}: focused practice on {subject}")
    return "\n".join(lines), "fallback"


# ---------------------------------------------------------------------------
# Performance forecast / risk outlook
# ---------------------------------------------------------------------------

def generate_risk_forecast(subject_rows, cgpa_trend, current_cgpa):
    """cgpa_trend: chronological list of past CGPA values (may have 0 or 1 entries)."""
    if not subject_rows:
        return "Add subjects to get a performance forecast.", "fallback"

    trend_desc = (
        f"past CGPA values over time, oldest to newest: {cgpa_trend}"
        if len(cgpa_trend) > 1 else "only one submission so far, so no trend yet"
    )
    prompt = (
        "You are a supportive academic forecaster, not a fortune teller. In ONE short, "
        f"encouraging sentence with a light caveat that this is an estimate, tell the "
        f"student where they appear to be headed. Current CGPA: {current_cgpa}. "
        f"Trend: {trend_desc}. Subjects (name, marks/100, attendance %): "
        f"{_rows_summary(subject_rows)}. No preamble, no markdown."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    if len(cgpa_trend) > 1:
        delta = round(cgpa_trend[-1] - cgpa_trend[0], 2)
        if delta > 0.2:
            outlook = f"trending upward (+{delta} CGPA recently) - keep this momentum going"
        elif delta < -0.2:
            outlook = f"trending downward ({delta} CGPA recently) - a course correction soon would help"
        else:
            outlook = "holding steady - consistent effort should keep it that way"
        return (f"Based on your recent submissions, your CGPA looks {outlook}. "
                "(This is an estimate from limited data, not a guarantee.)", "fallback")

    flagged = [r["subject"] for r in subject_rows if attendance_status(r["attendance_pct"])]
    note = (f" Keep an eye on attendance in {', '.join(flagged)} - it tends to drag CGPA "
            "down over time." if flagged else "")
    return (f"With a current CGPA of {current_cgpa}, you're on track to hold a similar "
            f"standing if your effort stays consistent.{note} "
            "(Estimate based on a single submission - submit again later for a real trend.)", "fallback")


# ---------------------------------------------------------------------------
# Subject improvement roadmap
# ---------------------------------------------------------------------------

def generate_subject_roadmap(subject_rows):
    if not subject_rows:
        return "Add subjects to get an improvement roadmap.", "fallback"

    weak = [r for r in subject_rows if score_to_grade(r["marks"])[1] in ("yellow", "red")]
    if not weak:
        return "All your subjects are in good shape right now - no roadmap needed. Keep it up!", "fallback"

    prompt = (
        "You are a subject-matter tutor. For each of these weaker subjects (name and "
        f"marks out of 100): {_rows_summary(weak)}, give ONE concrete, topic-level "
        "suggestion of what to revisit or practice next (e.g. 'In DBMS, revisit "
        "normalization and indexing'). One short line per subject, plain text, no markdown."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    lines = [
        f"{r['subject']}: revisit core fundamentals, redo recent assignments and quizzes, "
        "and practice the specific topics you found hardest in your last test."
        for r in weak
    ]
    return "\n".join(lines), "fallback"


# ---------------------------------------------------------------------------
# Personalized goal suggestions
# ---------------------------------------------------------------------------

def generate_goal_suggestions(subject_rows, cgpa):
    if not subject_rows:
        return "Add subjects to get personalized goal suggestions.", "fallback"

    prompt = (
        "You are a goal-setting coach. Based on this student's current CGPA "
        f"({cgpa}) and subjects (name, marks out of 100): {_rows_summary(subject_rows)}, "
        "suggest ONE realistic target CGPA and ONE realistic target marks-per-subject "
        "for their next term, with a one-line reason why it's a sensible stretch. "
        "Keep it to 2-3 short sentences, plain text, no markdown."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    suggested_cgpa = round(min(10.0, cgpa + 0.5), 1)
    avg_marks = sum(r["marks"] for r in subject_rows) / len(subject_rows)
    suggested_marks = min(100, round(avg_marks + 8))
    return (
        f"A realistic next step would be aiming for a CGPA around {suggested_cgpa} and "
        f"around {suggested_marks} marks per subject - a steady improvement over your "
        "current average without overreaching.", "fallback"
    )


def generate_class_overview(stats):
    """stats: the dict returned by analytics.class_overview()."""
    if not stats:
        return "Upload student records to see a class-wide overview.", "fallback"

    top_line = ", ".join(f"{s['student_name']} ({s['cgpa']})" for s in stats["top_students"])
    risk_line = ", ".join(stats["at_risk_students"]) if stats["at_risk_students"] else "none"
    subject_line = ", ".join(f"{subj}: {avg}" for subj, avg in stats["subject_averages"].items())

    prompt = (
        "You are an academic analytics assistant briefing a teacher on their class. "
        "Write a warm, 3-4 sentence narrative overview covering overall performance, "
        "standout students, subjects that need attention, and attendance risk. "
        f"Stats - students: {stats['num_students']}, subjects: {stats['num_subjects']}, "
        f"records: {stats['num_records']}, average marks: {stats['avg_marks']}/100, "
        f"average attendance: {stats['avg_attendance']}%, grade spread (green/yellow/red): "
        f"{stats['grade_counts']['green']}/{stats['grade_counts']['yellow']}/{stats['grade_counts']['red']}, "
        f"top performers (name, CGPA): {top_line or 'not enough data'}, "
        f"subject averages: {subject_line}, students with attendance below 75%: {risk_line}. "
        "No preamble, no markdown."
    )
    text = _call_gemini(prompt)
    if text:
        return text, "gemini"

    parts = [
        f"This dataset covers {stats['num_students']} student(s) across {stats['num_subjects']} "
        f"subject(s) ({stats['num_records']} records), averaging {stats['avg_marks']}/100 in marks "
        f"and {stats['avg_attendance']}% attendance.",
        f"Grade spread is {stats['grade_counts']['green']} strong, {stats['grade_counts']['yellow']} "
        f"average, and {stats['grade_counts']['red']} weak performance(s).",
    ]
    if top_line:
        parts.append(f"Leading the class: {top_line}.")
    if stats["at_risk_students"]:
        parts.append(f"Attendance needs attention for: {risk_line}.")
    else:
        parts.append("No students currently fall below the 75% attendance threshold.")
    return " ".join(parts), "fallback"


def _rows_summary(rows):
    return "; ".join(
        f"{r['subject']}: {r['marks']}/100 marks, {r['attendance_pct']}% attendance"
        for r in rows
    )

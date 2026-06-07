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


def _rows_summary(rows):
    return "; ".join(
        f"{r['subject']}: {r['marks']}/100 marks, {r['attendance_pct']}% attendance"
        for r in rows
    )

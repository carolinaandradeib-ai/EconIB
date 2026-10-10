"""grade_calculator.py: you input all the marks that you received in the paper/IA, and it estimates a 1-7 grade.
it uses the 2027 IB Economics weightings (first exams 2027):
  SL: Paper 1 = 30%, Paper 2 = 40%, IA = 30%
  HL: Paper 1 = 20%, Paper 2 = 30%, Paper 3 = 30%, IA = 20%
the boundaries are approximations for now since the real 2027 ones aren't out yet."""

components = {
    "SL": [
        ("p1", "Paper 1 (Extended Response)", 25, 0.30),
        ("p2", "Paper 2 (Data Response)", 40, 0.40),
        ("ia", "Internal Assessment (Portfolio)", 45, 0.30),
    ],
    "HL": [
        ("p1", "Paper 1 (Extended Response)", 25, 0.20),
        ("p2", "Paper 2 (Data Response)", 40, 0.30),
        ("p3", "Paper 3 (Policy Paper)", 60, 0.30),
        ("ia", "Internal Assessment (Portfolio)", 45, 0.20),
    ],
}
boundaries = [(77, 7), (63, 6), (51, 5), (39, 4), (28, 3), (15, 2), (0, 1)]


def calculate(level, marks):
    if level not in components:
        raise ValueError("Level must be 'SL' or 'HL'.")

    overall = 0.0
    breakdown = []
    for key, name, max_marks, weight in components[level]:
        mark = float(marks.get(key, 0) or 0)
        mark = max(0.0, min(mark, max_marks))
        contribution = (mark/max_marks)*weight*100
        overall += contribution
        breakdown.append({
            "key": key, "name": name, "mark": mark, "max": max_marks,
            "weight": round(weight*100), "percent": round((mark/max_marks)*100, 1),
            "contribution": round(contribution, 1),
        })

    grade =1
    boundary =0
    for cutoff, g in boundaries:
        if overall >= cutoff:
            grade = g
            boundary =cutoff
            break

    return {
        "level": level,
        "overall":round(overall, 1),
        "grade": grade,
        "boundary": boundary,
        "breakdown": breakdown,
    }

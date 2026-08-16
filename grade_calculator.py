# grade_calculator.py
# takes my paper marks and estimates a 1-7 grade (SC-06).
# it uses the 2027 IB Economics weightings (first exams 2027):
#   SL: Paper 1 = 30%, Paper 2 = 40%, IA = 30%
#   HL: Paper 1 = 20%, Paper 2 = 30%, Paper 3 = 30%, IA = 20%
# the boundaries lower down are approximate for now because the real 2027 ones aren't out yet.

# each row is: (key, name shown on screen, max marks, weight as a decimal)
# the weights add up to 1.0 (100%) for each level
COMPONENTS = {
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

# the % you need for each grade. i put them highest first on purpose so the loop below
# can stop at the first one you reach.
BOUNDARIES = [(77, 7), (63, 6), (51, 5), (39, 4), (28, 3), (15, 2), (0, 1)]


def calculate(level, marks):
    # level is "SL" or "HL", marks is a dict like {"p1": 20, "p2": 30, "ia": 38}
    if level not in COMPONENTS:
        raise ValueError("Level must be 'SL' or 'HL'.")

    overall = 0.0
    breakdown = []
    for key, name, max_marks, weight in COMPONENTS[level]:
        mark = float(marks.get(key, 0) or 0)     # if the box is empty just treat it as 0
        # clamp the mark so it can't be silly. e.g. if i type 999 out of 25 it becomes 25,
        # and a negative number becomes 0, so the grade never comes out broken.
        mark = max(0.0, min(mark, max_marks))
        # turn this paper into a % of itself, then scale it by how much the paper is worth.
        # adding all of these up gives one overall % out of 100, which is how IB combines papers.
        contribution = (mark / max_marks) * weight * 100
        overall += contribution
        breakdown.append({
            "key": key, "name": name, "mark": mark, "max": max_marks,
            "weight": round(weight * 100), "percent": round((mark / max_marks) * 100, 1),
            "contribution": round(contribution, 1),
        })

    # now turn the overall % into a 1-7. walk down the boundaries (highest first) and the
    # first one you're above is your grade, then break so it doesn't overwrite it.
    grade, boundary = 1, 0
    for cutoff, g in BOUNDARIES:
        if overall >= cutoff:
            grade, boundary = g, cutoff
            break

    return {
        "level": level,
        "overall": round(overall, 1),
        "grade": grade,
        "boundary": boundary,
        "breakdown": breakdown,
    }

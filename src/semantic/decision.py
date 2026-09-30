def classify_alignment(alignment, goal, activity):
    alignment = float(alignment)

    if alignment >= 0.30:
        classification = "relevant"
        reason = "strong_semantic_match"
    elif alignment >= 0.20:
        classification = "uncertain"
        reason = "borderline_semantic_match"
    else:
        classification = "unrelated"
        reason = "weak_semantic_match"

    return {
        "alignment": alignment,
        "classification": classification,
        "reason": reason,
    }
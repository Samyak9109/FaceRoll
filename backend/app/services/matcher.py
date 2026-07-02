import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def find_best_match(
    query_embedding: list[float],
    candidates: list[dict],
    threshold: float,
) -> tuple[dict | None, float]:
    best: dict | None = None
    best_score = -1.0
    for candidate in candidates:
        score = cosine_similarity(query_embedding, candidate["face_embedding"])
        if score > best_score:
            best = candidate
            best_score = score
    if best is None or best_score < threshold:
        return None, best_score
    return best, best_score

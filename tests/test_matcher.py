import pytest

from app.services.matcher import cosine_similarity, find_best_match


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_find_best_match_respects_threshold():
    candidates = [
        {"_id": "a", "face_embedding": [1.0, 0.0]},
        {"_id": "b", "face_embedding": [0.0, 1.0]},
    ]
    match, score = find_best_match([0.8, 0.2], candidates, threshold=0.8)
    assert match["_id"] == "a"
    assert score > 0.8

    match, _ = find_best_match([0.8, 0.2], candidates, threshold=0.99)
    assert match is None

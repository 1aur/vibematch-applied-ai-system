from src.evaluator import evaluate_recommendations


PROFILE = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.8,
    "likes_acoustic": False,
    "priority": "balanced",
}

CATALOG = [
    {
        "id": 1,
        "title": "Match",
        "artist": "Artist A",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.9,
        "danceability": 0.8,
        "acousticness": 0.2,
    },
    {
        "id": 2,
        "title": "Different",
        "artist": "Artist B",
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.5,
        "tempo_bpm": 90,
        "valence": 0.7,
        "danceability": 0.5,
        "acousticness": 0.8,
    },
]


def test_empty_recommendations_require_retry():
    report = evaluate_recommendations(PROFILE, [], CATALOG, "balanced", requested_k=5)

    assert report.quality_score == 0.0
    assert report.requires_retry is True
    assert "No recommendations were returned." in report.warnings


def test_complete_strong_recommendation_has_bounded_quality_score():
    recommendations = [(CATALOG[0], 4.5, "genre match, mood match")]

    report = evaluate_recommendations(
        PROFILE,
        recommendations,
        CATALOG,
        "balanced",
        requested_k=1,
    )

    assert 0.0 <= report.quality_score <= 1.0
    assert report.explanation_completeness == 1.0
    assert report.requires_retry is False


def test_missing_explanation_is_reported():
    recommendations = [(CATALOG[0], 4.5, "")]

    report = evaluate_recommendations(
        PROFILE,
        recommendations,
        CATALOG,
        "balanced",
        requested_k=1,
    )

    assert report.explanation_completeness == 0.0
    assert any("missing explanations" in warning for warning in report.warnings)

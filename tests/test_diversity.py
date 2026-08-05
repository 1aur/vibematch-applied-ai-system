from src.diversity import rerank_for_diversity


def _recommendation(title, artist, genre, score):
    return (
        {
            "title": title,
            "artist": artist,
            "genre": genre,
        },
        score,
        "test explanation",
    )


def test_diversity_guardrail_defers_repeated_artist():
    candidates = [
        _recommendation("First", "Same Artist", "pop", 4.0),
        _recommendation("Second", "Same Artist", "rock", 3.9),
        _recommendation("Third", "Other Artist", "jazz", 3.8),
    ]

    selected, adjustments = rerank_for_diversity(
        candidates,
        k=2,
        max_per_artist=1,
        max_per_genre=2,
    )

    assert [item[0]["title"] for item in selected] == ["First", "Third"]
    assert any("artist limit" in adjustment for adjustment in adjustments)


def test_diversity_guardrail_relaxes_limit_to_fill_requested_count():
    candidates = [
        _recommendation("First", "Same Artist", "pop", 4.0),
        _recommendation("Second", "Same Artist", "pop", 3.9),
    ]

    selected, adjustments = rerank_for_diversity(
        candidates,
        k=2,
        max_per_artist=1,
        max_per_genre=1,
    )

    assert len(selected) == 2
    assert any("Relaxed a diversity limit" in adjustment for adjustment in adjustments)

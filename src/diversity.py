"""Diversity guardrails for the final recommendation list."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple


RecommendationTuple = Tuple[Dict, float, str]


def rerank_for_diversity(
    recommendations: List[RecommendationTuple],
    k: int,
    max_per_artist: int = 1,
    max_per_genre: int = 2,
) -> tuple[List[RecommendationTuple], list[str]]:
    """Build a top-k list while limiting repeated artists and genres."""

    if k <= 0:
        return [], []

    selected: list[RecommendationTuple] = []
    deferred: list[RecommendationTuple] = []
    artist_counts: Counter[str] = Counter()
    genre_counts: Counter[str] = Counter()
    adjustments: list[str] = []

    for recommendation in recommendations:
        song = recommendation[0]
        artist = str(song["artist"]).strip().lower()
        genre = str(song["genre"]).strip().lower()

        artist_limit_reached = artist_counts[artist] >= max_per_artist
        genre_limit_reached = genre_counts[genre] >= max_per_genre

        if artist_limit_reached or genre_limit_reached:
            deferred.append(recommendation)
            reason = "artist limit" if artist_limit_reached else "genre limit"
            adjustments.append(
                f"Deferred {song['title']} by {song['artist']} because of the {reason}."
            )
            continue

        selected.append(recommendation)
        artist_counts[artist] += 1
        genre_counts[genre] += 1

        if len(selected) == k:
            break

    if len(selected) < k:
        for recommendation in deferred:
            if len(selected) == k:
                break
            if recommendation not in selected:
                selected.append(recommendation)
                song = recommendation[0]
                adjustments.append(
                    f"Relaxed a diversity limit to return {k} results and included "
                    f"{song['title']} by {song['artist']}."
                )

    return selected, adjustments

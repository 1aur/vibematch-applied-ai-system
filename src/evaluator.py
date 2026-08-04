"""Reliability evaluation for recommendation results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .strategies import get_strategy, maximum_possible_score
from .validation import validate_user_profile


RecommendationTuple = Tuple[Dict, float, str]


@dataclass(frozen=True)
class EvaluationReport:
    """Structured quality report used by the recommendation agent."""

    quality_score: float
    priority_alignment: float
    energy_alignment: float
    diversity_score: float
    score_strength: float
    explanation_completeness: float
    catalog_support: float
    recommendation_count: int
    warnings: tuple[str, ...]
    requires_retry: bool

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""

        return asdict(self)


def _matches(song: Dict, field: str, target: str) -> bool:
    return str(song[field]).strip().lower() == str(target).strip().lower()


def _ranked_categorical_alignment(
    recommendations: List[RecommendationTuple],
    catalog: List[Dict],
    field: str,
    target: str,
) -> tuple[float, bool]:
    """Score whether available exact matches appear near the top of the ranking."""

    support_count = sum(_matches(song, field, target) for song in catalog)
    if support_count == 0:
        return 0.0, False

    rank_weights = [1.0, 0.75, 0.50, 0.25, 0.10]
    available_slots = min(support_count, len(recommendations), len(rank_weights))
    maximum = sum(rank_weights[:available_slots])
    actual = 0.0

    for index, recommendation in enumerate(recommendations[: len(rank_weights)]):
        if _matches(recommendation[0], field, target):
            actual += rank_weights[index]

    return min(actual / maximum, 1.0) if maximum else 0.0, True


def _acoustic_alignment(
    recommendations: List[RecommendationTuple],
    likes_acoustic: bool | None,
) -> float:
    if likes_acoustic is None or not recommendations:
        return 1.0

    matches = 0
    for song, _, _ in recommendations:
        is_acoustic = float(song["acousticness"]) >= 0.60
        matches += is_acoustic == likes_acoustic
    return matches / len(recommendations)


def evaluate_recommendations(
    user_prefs: Dict,
    recommendations: List[RecommendationTuple],
    catalog: List[Dict],
    strategy_name: str,
    requested_k: int,
) -> EvaluationReport:
    """Measure reliability and decide whether one corrective retry is useful."""

    user = validate_user_profile(user_prefs)
    strategy = get_strategy(strategy_name)
    selected = recommendations[:requested_k]

    if not selected:
        return EvaluationReport(
            quality_score=0.0,
            priority_alignment=0.0,
            energy_alignment=0.0,
            diversity_score=0.0,
            score_strength=0.0,
            explanation_completeness=0.0,
            catalog_support=0.0,
            recommendation_count=0,
            warnings=("No recommendations were returned.",),
            requires_retry=True,
        )

    genre_alignment, genre_supported = _ranked_categorical_alignment(
        selected,
        catalog,
        "genre",
        user["favorite_genre"],
    )
    mood_alignment, mood_supported = _ranked_categorical_alignment(
        selected,
        catalog,
        "mood",
        user["favorite_mood"],
    )

    energy_alignment = sum(
        max(0.0, 1.0 - abs(float(song["energy"]) - user["target_energy"]))
        for song, _, _ in selected
    ) / len(selected)

    acoustic_alignment = _acoustic_alignment(
        selected,
        user.get("likes_acoustic"),
    )

    unique_artist_ratio = len(
        {str(song["artist"]).strip().lower() for song, _, _ in selected}
    ) / len(selected)
    unique_genre_ratio = len(
        {str(song["genre"]).strip().lower() for song, _, _ in selected}
    ) / len(selected)
    diversity_score = (unique_artist_ratio + unique_genre_ratio) / 2.0

    max_score = maximum_possible_score(strategy, user)
    score_strength = min(
        sum(score for _, score, _ in selected) / len(selected) / max_score,
        1.0,
    )
    explanation_completeness = sum(
        bool(str(explanation).strip()) for _, _, explanation in selected
    ) / len(selected)

    supported_requests = int(genre_supported) + int(mood_supported)
    catalog_support = supported_requests / 2.0

    priority = user["priority"]
    if priority == "genre":
        priority_alignment = genre_alignment
    elif priority == "mood":
        priority_alignment = mood_alignment
    elif priority == "energy":
        priority_alignment = energy_alignment
    elif priority == "discovery":
        priority_alignment = diversity_score
    else:
        components = [energy_alignment, acoustic_alignment]
        if genre_supported:
            components.append(genre_alignment)
        if mood_supported:
            components.append(mood_alignment)
        priority_alignment = sum(components) / len(components)

    quality_score = (
        0.40 * priority_alignment
        + 0.20 * energy_alignment
        + 0.20 * diversity_score
        + 0.10 * score_strength
        + 0.10 * explanation_completeness
    )

    warnings: list[str] = []
    if len(selected) < requested_k:
        warnings.append(
            f"Only {len(selected)} of {requested_k} requested recommendations were returned."
        )
    if not genre_supported:
        warnings.append(
            f"The catalog has no exact genre match for '{user['favorite_genre']}'."
        )
    if not mood_supported:
        warnings.append(
            f"The catalog has no exact mood match for '{user['favorite_mood']}'."
        )
    if priority in {"genre", "mood"} and priority_alignment < 0.70:
        warnings.append(
            f"The initial ranking underrepresented the user's {priority} priority."
        )
    if priority == "energy" and energy_alignment < 0.75:
        warnings.append("The initial ranking was weakly aligned with target energy.")
    if priority == "discovery" and diversity_score < 0.75:
        warnings.append("The initial ranking did not provide enough variety.")
    if diversity_score < 0.70:
        warnings.append("The recommendation list has limited artist or genre diversity.")
    if explanation_completeness < 1.0:
        warnings.append("One or more recommendations are missing explanations.")
    if quality_score < 0.55:
        warnings.append("The overall recommendation quality score is below threshold.")

    retry_for_priority = (
        priority in {"genre", "mood"} and priority_alignment < 0.70
    ) or (priority == "energy" and energy_alignment < 0.75) or (
        priority == "discovery" and diversity_score < 0.75
    )
    requires_retry = retry_for_priority or quality_score < 0.55

    return EvaluationReport(
        quality_score=round(quality_score, 4),
        priority_alignment=round(priority_alignment, 4),
        energy_alignment=round(energy_alignment, 4),
        diversity_score=round(diversity_score, 4),
        score_strength=round(score_strength, 4),
        explanation_completeness=round(explanation_completeness, 4),
        catalog_support=round(catalog_support, 4),
        recommendation_count=len(selected),
        warnings=tuple(warnings),
        requires_retry=requires_retry,
    )

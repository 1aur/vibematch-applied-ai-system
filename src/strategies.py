"""Scoring strategies used by the adaptive VibeMatch recommender."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ScoringWeights:
    """Weights that control how strongly each feature affects a song score."""

    genre: float
    mood: float
    energy: float
    acousticness: float
    valence: float = 0.0
    danceability: float = 0.0
    tempo: float = 0.0


@dataclass(frozen=True)
class ScoringStrategy:
    """Named recommendation strategy with a short explanation and weights."""

    name: str
    description: str
    weights: ScoringWeights


_STRATEGIES: Dict[str, ScoringStrategy] = {
    "balanced": ScoringStrategy(
        name="balanced",
        description="Preserves the original VibeMatch 1.0 weighting recipe.",
        weights=ScoringWeights(
            genre=2.0,
            mood=1.0,
            energy=1.0,
            acousticness=0.5,
        ),
    ),
    "genre_first": ScoringStrategy(
        name="genre_first",
        description="Prioritizes exact genre matches while retaining other signals.",
        weights=ScoringWeights(
            genre=2.5,
            mood=0.75,
            energy=0.75,
            acousticness=0.5,
        ),
    ),
    "mood_first": ScoringStrategy(
        name="mood_first",
        description="Prioritizes emotional atmosphere and optional valence alignment.",
        weights=ScoringWeights(
            genre=1.0,
            mood=2.5,
            energy=1.0,
            acousticness=0.5,
            valence=1.0,
        ),
    ),
    "energy_focused": ScoringStrategy(
        name="energy_focused",
        description="Prioritizes energy, danceability, and tempo for activity-based listening.",
        weights=ScoringWeights(
            genre=0.75,
            mood=0.75,
            energy=2.0,
            acousticness=0.5,
            danceability=1.5,
            tempo=1.0,
        ),
    ),
    "discovery": ScoringStrategy(
        name="discovery",
        description="Reduces exact-genre dominance and rewards broader vibe similarity.",
        weights=ScoringWeights(
            genre=0.5,
            mood=1.5,
            energy=1.25,
            acousticness=0.5,
            valence=0.75,
            danceability=0.75,
        ),
    ),
}


def normalize_strategy_name(name: str) -> str:
    """Normalize common strategy spellings to the internal snake_case names."""

    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def get_strategy(name: str = "balanced") -> ScoringStrategy:
    """Return a configured strategy or raise a clear error for an unknown name."""

    normalized = normalize_strategy_name(name)
    if normalized == "auto":
        normalized = "balanced"

    try:
        return _STRATEGIES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted(_STRATEGIES))
        raise ValueError(
            f"Unknown scoring strategy '{name}'. Choose one of: {choices}."
        ) from exc


def available_strategies() -> tuple[str, ...]:
    """Return the supported strategy names in a stable order."""

    return tuple(_STRATEGIES)


def maximum_possible_score(strategy: ScoringStrategy, user_prefs: dict) -> float:
    """Calculate the maximum score available for the provided preferences."""

    weights = strategy.weights
    maximum = weights.genre + weights.mood + weights.energy

    if user_prefs.get("likes_acoustic") is not None:
        maximum += weights.acousticness
    if user_prefs.get("target_valence") is not None:
        maximum += weights.valence
    if user_prefs.get("target_danceability") is not None:
        maximum += weights.danceability
    if user_prefs.get("target_tempo_bpm") is not None:
        maximum += weights.tempo

    return max(maximum, 1.0)

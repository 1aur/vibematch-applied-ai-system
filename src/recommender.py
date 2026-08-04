import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .strategies import ScoringStrategy, get_strategy
from .validation import (
    CatalogValidationError,
    parse_song_row,
    validate_catalog_headers,
    validate_user_profile,
)


logger = logging.getLogger("vibematch.recommender")


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: Optional[bool]
    priority: str = "balanced"
    target_valence: Optional[float] = None
    target_danceability: Optional[float] = None
    target_tempo_bpm: Optional[float] = None


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        strategy: str = "balanced",
    ) -> List[Song]:
        # TODO: Implement recommendation logic
        validated_user = validate_user_profile(vars(user))
        selected_strategy = get_strategy(strategy)
        ranked_songs = sorted(
            self.songs,
            key=lambda song: _score_validated_song(
                validated_user,
                vars(song),
                selected_strategy,
            )[0],
            reverse=True,
        )
        return ranked_songs[:max(k, 0)]

    def explain_recommendation(
        self,
        user: UserProfile,
        song: Song,
        strategy: str = "balanced",
    ) -> str:
        # TODO: Implement explanation logic
        _, reasons = score_song(vars(user), vars(song), strategy=strategy)
        return ", ".join(reasons) if reasons else "No strong feature matches."


def load_songs(csv_path: str, strict: bool = True) -> List[Dict]:
    """
    Loads and validates songs from a CSV file.
    Required by src/main.py

    In strict mode, any invalid row stops the load with a readable error.
    In lenient mode, invalid rows are logged and skipped.
    """
    # TODO: Implement CSV loading logic
    print(f"Loading songs from {csv_path}...")

    path = Path(csv_path)
    if not path.exists():
        raise CatalogValidationError(f"Song catalog not found: {csv_path}")
    if not path.is_file():
        raise CatalogValidationError(f"Song catalog path is not a file: {csv_path}")

    songs: List[Dict] = []
    errors: list[str] = []
    seen_ids: set[int] = set()
    seen_title_artist: set[tuple[str, str]] = set()

    try:
        with path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            validate_catalog_headers(reader.fieldnames)

            for row_number, row in enumerate(reader, start=2):
                if not row or not any(str(value).strip() for value in row.values()):
                    logger.warning("Skipped blank catalog row %s", row_number)
                    continue

                try:
                    song = parse_song_row(row, row_number)
                    song_key = (
                        song["title"].strip().lower(),
                        song["artist"].strip().lower(),
                    )
                    if song["id"] in seen_ids:
                        raise ValueError(
                            f"Row {row_number}: duplicate song id {song['id']}."
                        )
                    if song_key in seen_title_artist:
                        raise ValueError(
                            f"Row {row_number}: duplicate title and artist combination."
                        )

                    seen_ids.add(song["id"])
                    seen_title_artist.add(song_key)
                    songs.append(song)
                except ValueError as exc:
                    errors.append(str(exc))
    except OSError as exc:
        raise CatalogValidationError(
            f"Could not read the song catalog '{csv_path}': {exc}"
        ) from exc

    if errors and strict:
        formatted = "\n- ".join(errors)
        raise CatalogValidationError(
            f"Song catalog validation failed:\n- {formatted}"
        )

    for error in errors:
        logger.warning("Skipped invalid catalog row: %s", error)

    if not songs:
        raise CatalogValidationError(
            "The song catalog did not contain any valid songs."
        )

    logger.info(
        "Loaded %s valid songs from %s; rejected %s rows",
        len(songs),
        csv_path,
        len(errors),
    )
    return songs


def _similarity(value: float, target: float) -> float:
    return max(0.0, 1.0 - abs(float(value) - float(target)))


def _tempo_similarity(tempo: float, target: float) -> float:
    # A 180 BPM span covers most values in the classroom catalog.
    return max(0.0, 1.0 - min(abs(float(tempo) - float(target)) / 180.0, 1.0))


def _score_validated_song(
    user_prefs: Dict,
    song: Dict,
    strategy: ScoringStrategy,
) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: list[str] = []
    weights = strategy.weights

    if song["genre"].strip().lower() == user_prefs["favorite_genre"]:
        score += weights.genre
        reasons.append(f"genre match (+{weights.genre:.2f})")

    if song["mood"].strip().lower() == user_prefs["favorite_mood"]:
        score += weights.mood
        reasons.append(f"mood match (+{weights.mood:.2f})")

    energy_similarity = _similarity(
        float(song["energy"]),
        user_prefs["target_energy"],
    )
    energy_points = energy_similarity * weights.energy
    score += energy_points
    reasons.append(f"energy similarity (+{energy_points:.2f})")

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None and weights.acousticness > 0:
        song_is_acoustic = float(song["acousticness"]) >= 0.60
        if song_is_acoustic == likes_acoustic:
            score += weights.acousticness
            reasons.append(
                f"acoustic preference match (+{weights.acousticness:.2f})"
            )

    target_valence = user_prefs.get("target_valence")
    if target_valence is not None and weights.valence > 0:
        points = _similarity(float(song["valence"]), target_valence) * weights.valence
        score += points
        reasons.append(f"valence similarity (+{points:.2f})")

    target_danceability = user_prefs.get("target_danceability")
    if target_danceability is not None and weights.danceability > 0:
        points = (
            _similarity(float(song["danceability"]), target_danceability)
            * weights.danceability
        )
        score += points
        reasons.append(f"danceability similarity (+{points:.2f})")

    target_tempo = user_prefs.get("target_tempo_bpm")
    if target_tempo is not None and weights.tempo > 0:
        points = _tempo_similarity(float(song["tempo_bpm"]), target_tempo) * weights.tempo
        score += points
        reasons.append(f"tempo similarity (+{points:.2f})")

    return score, reasons


def score_song(
    user_prefs: Dict,
    song: Dict,
    strategy: str = "balanced",
) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    # TODO: Implement scoring logic using your Algorithm Recipe from Phase 2.
    # Expected return format: (score, reasons)
    validated_user = validate_user_profile(user_prefs)
    selected_strategy = get_strategy(strategy)
    return _score_validated_song(validated_user, song, selected_strategy)


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: str = "balanced",
) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # TODO: Implement scoring and ranking logic
    # Expected return format: (song_dict, score, explanation)
    if k <= 0 or not songs:
        return []

    validated_user = validate_user_profile(user_prefs)
    selected_strategy = get_strategy(strategy)
    scored_songs: list[Tuple[Dict, float, str]] = []

    for song in songs:
        score, reasons = _score_validated_song(
            validated_user,
            song,
            selected_strategy,
        )
        explanation = (
            ", ".join(reasons)
            if reasons
            else "No strong feature matches."
        )
        scored_songs.append((song, score, explanation))

    ranked_songs = sorted(
        scored_songs,
        key=lambda result: result[1],
        reverse=True,
    )

    logger.info(
        "Ranked %s songs with strategy=%s and requested k=%s",
        len(songs),
        selected_strategy.name,
        k,
    )
    return ranked_songs[:max(k, 0)]

"""Validation and defensive parsing for VibeMatch inputs."""

from __future__ import annotations

from typing import Any, Mapping


REQUIRED_SONG_COLUMNS = {
    "id",
    "title",
    "artist",
    "genre",
    "mood",
    "energy",
    "tempo_bpm",
    "valence",
    "danceability",
    "acousticness",
}

SUPPORTED_PRIORITIES = {
    "balanced",
    "genre",
    "mood",
    "energy",
    "discovery",
}


class VibeMatchError(Exception):
    """Base exception for expected, user-facing VibeMatch failures."""


class CatalogValidationError(VibeMatchError):
    """Raised when a song catalog cannot be loaded safely."""


class ProfileValidationError(VibeMatchError):
    """Raised when a user preference profile is incomplete or invalid."""


def _clean_text(value: Any, field_name: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} cannot be blank.")
    return text


def _parse_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric; received {value!r}.") from exc


def _parse_unit_interval(value: Any, field_name: str) -> float:
    number = _parse_float(value, field_name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
    return number


def parse_boolean(value: Any, field_name: str = "value") -> bool:
    """Parse booleans without treating the string 'False' as truthy."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "y"}:
            return True
        if normalized in {"false", "no", "0", "n"}:
            return False
    raise ValueError(f"{field_name} must be true or false.")


def validate_catalog_headers(fieldnames: list[str] | None) -> None:
    """Verify that the CSV contains every required song attribute."""

    if not fieldnames:
        raise CatalogValidationError("The song catalog is empty or has no header row.")

    missing = sorted(REQUIRED_SONG_COLUMNS.difference(fieldnames))
    if missing:
        raise CatalogValidationError(
            "The song catalog is missing required columns: " + ", ".join(missing)
        )


def parse_song_row(row: Mapping[str, Any], row_number: int) -> dict:
    """Convert and validate one CSV row, returning a normalized song dictionary."""

    try:
        song_id = int(row.get("id", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: id must be a whole number.") from exc

    if song_id <= 0:
        raise ValueError(f"Row {row_number}: id must be greater than zero.")

    try:
        tempo = _parse_float(row.get("tempo_bpm"), "tempo_bpm")
        if tempo <= 0:
            raise ValueError("tempo_bpm must be greater than zero.")

        return {
            "id": song_id,
            "title": _clean_text(row.get("title"), "title"),
            "artist": _clean_text(row.get("artist"), "artist"),
            "genre": _clean_text(row.get("genre"), "genre").lower(),
            "mood": _clean_text(row.get("mood"), "mood").lower(),
            "energy": _parse_unit_interval(row.get("energy"), "energy"),
            "tempo_bpm": tempo,
            "valence": _parse_unit_interval(row.get("valence"), "valence"),
            "danceability": _parse_unit_interval(
                row.get("danceability"), "danceability"
            ),
            "acousticness": _parse_unit_interval(
                row.get("acousticness"), "acousticness"
            ),
        }
    except ValueError as exc:
        message = str(exc)
        if not message.startswith(f"Row {row_number}:"):
            message = f"Row {row_number}: {message}"
        raise ValueError(message) from exc


def _optional_unit_interval(
    profile: Mapping[str, Any], field_name: str
) -> float | None:
    value = profile.get(field_name)
    if value in (None, ""):
        return None
    return _parse_unit_interval(value, field_name)


def validate_user_profile(user_prefs: Mapping[str, Any]) -> dict:
    """Validate and normalize a user profile before recommendation begins."""

    if not isinstance(user_prefs, Mapping):
        raise ProfileValidationError("User preferences must be provided as a mapping.")

    try:
        genre = _clean_text(
            user_prefs.get("favorite_genre", user_prefs.get("genre")),
            "favorite_genre",
        ).lower()
        mood = _clean_text(
            user_prefs.get("favorite_mood", user_prefs.get("mood")),
            "favorite_mood",
        ).lower()
        energy = _parse_unit_interval(
            user_prefs.get("target_energy", user_prefs.get("energy")),
            "target_energy",
        )

        acoustic_value = user_prefs.get("likes_acoustic")
        likes_acoustic = (
            None
            if acoustic_value in (None, "")
            else parse_boolean(acoustic_value, "likes_acoustic")
        )

        priority = str(user_prefs.get("priority", "balanced")).strip().lower()
        priority = priority.replace("-", "_").replace(" ", "_")
        if priority not in SUPPORTED_PRIORITIES:
            choices = ", ".join(sorted(SUPPORTED_PRIORITIES))
            raise ValueError(f"priority must be one of: {choices}.")

        target_tempo = user_prefs.get("target_tempo_bpm")
        if target_tempo in (None, ""):
            parsed_tempo = None
        else:
            parsed_tempo = _parse_float(target_tempo, "target_tempo_bpm")
            if parsed_tempo <= 0:
                raise ValueError("target_tempo_bpm must be greater than zero.")

        return {
            "favorite_genre": genre,
            "favorite_mood": mood,
            "target_energy": energy,
            "likes_acoustic": likes_acoustic,
            "priority": priority,
            "target_valence": _optional_unit_interval(
                user_prefs, "target_valence"
            ),
            "target_danceability": _optional_unit_interval(
                user_prefs, "target_danceability"
            ),
            "target_tempo_bpm": parsed_tempo,
        }
    except ValueError as exc:
        raise ProfileValidationError(str(exc)) from exc

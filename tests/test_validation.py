import pytest

from src.validation import (
    CatalogValidationError,
    ProfileValidationError,
    parse_boolean,
    validate_catalog_headers,
    validate_user_profile,
)


def test_validate_user_profile_normalizes_aliases_and_text():
    result = validate_user_profile(
        {
            "genre": " Pop ",
            "mood": " Happy ",
            "energy": "0.8",
            "likes_acoustic": "false",
            "priority": "Energy",
        }
    )

    assert result["favorite_genre"] == "pop"
    assert result["favorite_mood"] == "happy"
    assert result["target_energy"] == pytest.approx(0.8)
    assert result["likes_acoustic"] is False
    assert result["priority"] == "energy"


def test_validate_user_profile_rejects_out_of_range_energy():
    with pytest.raises(ProfileValidationError, match="between 0.0 and 1.0"):
        validate_user_profile(
            {
                "favorite_genre": "pop",
                "favorite_mood": "happy",
                "target_energy": 1.2,
                "likes_acoustic": False,
            }
        )


def test_parse_boolean_handles_false_string_safely():
    assert parse_boolean("False", "likes_acoustic") is False
    assert parse_boolean("yes", "likes_acoustic") is True


def test_validate_catalog_headers_reports_missing_columns():
    with pytest.raises(CatalogValidationError, match="missing required columns"):
        validate_catalog_headers(["id", "title", "artist"])

from pathlib import Path

import pytest

from src.recommender import load_songs
from src.validation import CatalogValidationError


HEADER = (
    "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
)
VALID_ROW = "1,Valid Song,Valid Artist,pop,happy,0.8,120,0.9,0.8,0.2\n"
INVALID_ROW = "2,Bad Song,Bad Artist,pop,happy,1.5,120,0.9,0.8,0.2\n"


def _write_catalog(path: Path) -> None:
    path.write_text(HEADER + VALID_ROW + INVALID_ROW, encoding="utf-8")


def test_strict_catalog_loading_stops_on_invalid_row(tmp_path):
    catalog = tmp_path / "songs.csv"
    _write_catalog(catalog)

    with pytest.raises(CatalogValidationError, match="validation failed"):
        load_songs(str(catalog), strict=True)


def test_lenient_catalog_loading_skips_invalid_row(tmp_path):
    catalog = tmp_path / "songs.csv"
    _write_catalog(catalog)

    songs = load_songs(str(catalog), strict=False)

    assert len(songs) == 1
    assert songs[0]["title"] == "Valid Song"

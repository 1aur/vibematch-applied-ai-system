"""Command-line runner for the adaptive VibeMatch applied AI system."""

from __future__ import annotations

import argparse
import sys
from typing import Dict

from .agent import RecommendationAgent
from .logging_config import configure_logging
from .recommender import load_songs
from .strategies import available_strategies
from .validation import CatalogValidationError, ProfileValidationError


DEFAULT_PROFILES: dict[str, Dict] = {
    "high-energy-pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.80,
        "likes_acoustic": False,
        "priority": "energy",
        "target_danceability": 0.85,
        "target_tempo_bpm": 125,
    },
    "chill-lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.40,
        "likes_acoustic": True,
        "priority": "balanced",
        "target_valence": 0.58,
    },
    "deep-intense-rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.90,
        "likes_acoustic": False,
        "priority": "balanced",
    },
    "conflicting-sad-workout": {
        "favorite_genre": "pop",
        "favorite_mood": "melancholic",
        "target_energy": 0.90,
        "likes_acoustic": False,
        "priority": "mood",
        "target_valence": 0.30,
    },
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate explained music recommendations with validation, diversity "
            "guardrails, reliability scoring, and one bounded corrective retry."
        )
    )
    parser.add_argument("--catalog", default="data/songs.csv")
    parser.add_argument(
        "--profile",
        choices=("all", *DEFAULT_PROFILES.keys()),
        default="all",
        help="Run a built-in evaluation profile.",
    )
    parser.add_argument("--genre", help="Favorite genre for a custom profile.")
    parser.add_argument("--mood", help="Favorite mood for a custom profile.")
    parser.add_argument("--energy", type=float, help="Target energy from 0.0 to 1.0.")
    parser.add_argument(
        "--priority",
        choices=("balanced", "genre", "mood", "energy", "discovery"),
        default="balanced",
    )
    parser.add_argument("--target-valence", type=float)
    parser.add_argument("--target-danceability", type=float)
    parser.add_argument("--target-tempo-bpm", type=float)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--strategy",
        choices=("auto", *available_strategies()),
        default="auto",
    )
    parser.add_argument(
        "--lenient-catalog",
        action="store_true",
        help="Skip invalid CSV rows instead of stopping the run.",
    )

    acoustic_group = parser.add_mutually_exclusive_group()
    acoustic_group.add_argument(
        "--acoustic",
        dest="likes_acoustic",
        action="store_true",
        help="Prefer songs classified as acoustic.",
    )
    acoustic_group.add_argument(
        "--non-acoustic",
        dest="likes_acoustic",
        action="store_false",
        help="Prefer songs classified as non-acoustic.",
    )
    parser.set_defaults(likes_acoustic=None)
    return parser


def _custom_profile(args: argparse.Namespace) -> Dict | None:
    custom_values = [args.genre, args.mood, args.energy, args.likes_acoustic]
    if not any(value is not None for value in custom_values):
        return None

    missing = []
    if args.genre is None:
        missing.append("--genre")
    if args.mood is None:
        missing.append("--mood")
    if args.energy is None:
        missing.append("--energy")
    if args.likes_acoustic is None:
        missing.append("--acoustic or --non-acoustic")
    if missing:
        raise ProfileValidationError(
            "A custom profile is missing: " + ", ".join(missing)
        )

    return {
        "favorite_genre": args.genre,
        "favorite_mood": args.mood,
        "target_energy": args.energy,
        "likes_acoustic": args.likes_acoustic,
        "priority": args.priority,
        "target_valence": args.target_valence,
        "target_danceability": args.target_danceability,
        "target_tempo_bpm": args.target_tempo_bpm,
    }


def _display_result(profile_name: str, result) -> None:
    print(f"\n{'=' * 72}")
    print(f"User profile: {profile_name}")
    print(f"Initial strategy: {result.initial_strategy}")
    print(f"Final strategy: {result.final_strategy}")
    print(f"Corrective retry: {'yes' if result.retry_triggered else 'no'}")
    print(
        "Quality score: "
        f"{result.initial_evaluation.quality_score:.2f} -> "
        f"{result.final_evaluation.quality_score:.2f}"
    )

    if result.final_evaluation.warnings:
        print("Reliability warnings:")
        for warning in result.final_evaluation.warnings:
            print(f"  - {warning}")
    else:
        print("Reliability warnings: none")

    if result.diversity_adjustments:
        print("Diversity guardrail actions:")
        for adjustment in result.diversity_adjustments:
            print(f"  - {adjustment}")

    print("\nTop recommendations:\n")
    for index, (song, score, explanation) in enumerate(
        result.recommendations,
        start=1,
    ):
        print(f"{index}. {song['title']} by {song['artist']}")
        print(f"   Score: {score:.2f}")
        print(f"   Reasons: {explanation}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging()

    try:
        songs = load_songs(args.catalog, strict=not args.lenient_catalog)
        print(f"Loaded songs: {len(songs)}")
        agent = RecommendationAgent(songs)

        custom_profile = _custom_profile(args)
        if custom_profile is not None:
            profiles = {"custom": custom_profile}
        elif args.profile == "all":
            profiles = DEFAULT_PROFILES
        else:
            profiles = {args.profile: DEFAULT_PROFILES[args.profile]}

        for profile_name, user_prefs in profiles.items():
            result = agent.run(
                user_prefs,
                k=args.top_k,
                strategy=args.strategy,
            )
            _display_result(profile_name, result)
        return 0
    except (CatalogValidationError, ProfileValidationError, ValueError) as exc:
        print(f"VibeMatch could not complete the request: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

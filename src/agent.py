"""Bounded plan-recommend-evaluate-revise workflow for VibeMatch."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .diversity import rerank_for_diversity
from .evaluator import EvaluationReport, evaluate_recommendations
from .recommender import recommend_songs
from .strategies import get_strategy, normalize_strategy_name
from .validation import validate_user_profile


logger = logging.getLogger("vibematch.agent")
RecommendationTuple = Tuple[Dict, float, str]


@dataclass(frozen=True)
class AgentResult:
    """Complete result of one bounded recommendation-agent run."""

    recommendations: List[RecommendationTuple]
    initial_strategy: str
    final_strategy: str
    retry_triggered: bool
    initial_evaluation: EvaluationReport
    final_evaluation: EvaluationReport
    diversity_adjustments: tuple[str, ...]

    def to_dict(self) -> dict:
        """Return a structured form suitable for future JSON evaluation logs."""

        return {
            "recommendations": [
                {
                    "song": song,
                    "score": round(score, 4),
                    "explanation": explanation,
                }
                for song, score, explanation in self.recommendations
            ],
            "initial_strategy": self.initial_strategy,
            "final_strategy": self.final_strategy,
            "retry_triggered": self.retry_triggered,
            "initial_evaluation": asdict(self.initial_evaluation),
            "final_evaluation": asdict(self.final_evaluation),
            "diversity_adjustments": list(self.diversity_adjustments),
        }


class RecommendationAgent:
    """Plan, rank, check, and optionally revise recommendations once."""

    def __init__(
        self,
        songs: List[Dict],
        max_per_artist: int = 1,
        max_per_genre: int = 2,
    ) -> None:
        if not songs:
            raise ValueError("RecommendationAgent requires at least one valid song.")
        self.songs = songs
        self.max_per_artist = max_per_artist
        self.max_per_genre = max_per_genre

    def _corrective_strategy(self, priority: str, current: str) -> str:
        mapping = {
            "genre": "genre_first",
            "mood": "mood_first",
            "energy": "energy_focused",
            "discovery": "discovery",
            "balanced": "discovery",
        }
        correction = mapping.get(priority, "discovery")
        return "discovery" if correction == current else correction

    def _rank_and_evaluate(
        self,
        user: Dict,
        strategy_name: str,
        k: int,
    ) -> tuple[List[RecommendationTuple], list[str], EvaluationReport]:
        candidate_count = min(len(self.songs), max(k * 3, k))
        candidates = recommend_songs(
            user,
            self.songs,
            k=candidate_count,
            strategy=strategy_name,
        )
        recommendations, adjustments = rerank_for_diversity(
            candidates,
            k=k,
            max_per_artist=self.max_per_artist,
            max_per_genre=self.max_per_genre,
        )
        evaluation = evaluate_recommendations(
            user,
            recommendations,
            self.songs,
            strategy_name,
            requested_k=k,
        )
        return recommendations, adjustments, evaluation

    def run(
        self,
        user_prefs: Dict,
        k: int = 5,
        strategy: str = "auto",
    ) -> AgentResult:
        """Execute at most one corrective retry after evaluating the first ranking."""

        if k <= 0:
            raise ValueError("k must be greater than zero.")

        user = validate_user_profile(user_prefs)
        requested_strategy = normalize_strategy_name(strategy)
        initial_strategy = (
            "balanced" if requested_strategy == "auto" else get_strategy(strategy).name
        )

        logger.info(
            "Starting recommendation run with initial_strategy=%s priority=%s k=%s",
            initial_strategy,
            user["priority"],
            k,
        )

        initial_recommendations, initial_adjustments, initial_evaluation = (
            self._rank_and_evaluate(user, initial_strategy, k)
        )

        if not initial_evaluation.requires_retry:
            logger.info(
                "Initial ranking passed with quality_score=%.4f",
                initial_evaluation.quality_score,
            )
            return AgentResult(
                recommendations=initial_recommendations,
                initial_strategy=initial_strategy,
                final_strategy=initial_strategy,
                retry_triggered=False,
                initial_evaluation=initial_evaluation,
                final_evaluation=initial_evaluation,
                diversity_adjustments=tuple(initial_adjustments),
            )

        corrective_strategy = self._corrective_strategy(
            user["priority"],
            initial_strategy,
        )
        logger.warning(
            "Initial ranking requested one corrective retry: %s -> %s",
            initial_strategy,
            corrective_strategy,
        )

        final_recommendations, final_adjustments, final_evaluation = (
            self._rank_and_evaluate(user, corrective_strategy, k)
        )

        logger.info(
            "Corrective ranking finished with quality_score=%.4f",
            final_evaluation.quality_score,
        )
        return AgentResult(
            recommendations=final_recommendations,
            initial_strategy=initial_strategy,
            final_strategy=corrective_strategy,
            retry_triggered=True,
            initial_evaluation=initial_evaluation,
            final_evaluation=final_evaluation,
            diversity_adjustments=tuple(initial_adjustments + final_adjustments),
        )

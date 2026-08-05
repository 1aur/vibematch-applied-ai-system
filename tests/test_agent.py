from src.agent import RecommendationAgent
from src.main import DEFAULT_PROFILES
from src.recommender import load_songs


def _agent():
    return RecommendationAgent(load_songs("data/songs.csv"))


def test_strong_profile_passes_without_corrective_retry():
    result = _agent().run(DEFAULT_PROFILES["high-energy-pop"], k=5)

    assert result.retry_triggered is False
    assert result.initial_strategy == "balanced"
    assert result.final_strategy == "balanced"
    assert result.final_evaluation.quality_score >= 0.85
    assert result.recommendations[0][0]["title"] == "Sunrise City"


def test_conflicting_profile_triggers_mood_correction_and_improves_quality():
    result = _agent().run(DEFAULT_PROFILES["conflicting-sad-workout"], k=5)

    assert result.retry_triggered is True
    assert result.initial_strategy == "balanced"
    assert result.final_strategy == "mood_first"
    assert (
        result.final_evaluation.quality_score
        > result.initial_evaluation.quality_score
    )
    assert result.recommendations[0][0]["title"] == "Blue Sunday"


def test_agent_result_is_json_serializable_structure():
    result = _agent().run(DEFAULT_PROFILES["chill-lofi"], k=3)
    payload = result.to_dict()

    assert payload["recommendations"]
    assert payload["final_evaluation"]["quality_score"] >= 0.0
    assert isinstance(payload["diversity_adjustments"], list)


def test_agent_rejects_nonpositive_k():
    agent = _agent()

    try:
        agent.run(DEFAULT_PROFILES["high-energy-pop"], k=0)
    except ValueError as exc:
        assert "greater than zero" in str(exc)
    else:
        raise AssertionError("Expected a ValueError for k=0")

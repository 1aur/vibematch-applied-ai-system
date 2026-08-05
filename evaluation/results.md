# VibeMatch Reliability Evaluation Results

## Reproduce the evaluation

```bash
python -m evaluation.run_evaluation
pytest
```

## Summary

10 out of 10 benchmark checks passed (100%). The six recommendation scenarios produced an average final quality score of 0.90. One scenario required the bounded corrective rerank; its quality improved from 0.71 to 0.90. Invalid profile values and malformed catalog rows were handled through explicit validation rather than unhandled crashes.

| Metric | Result |
|---|---:|
| Benchmark checks passed | 10 / 10 |
| Pass rate | 100% |
| Recommendation scenarios | 6 |
| Guardrail and reliability checks | 4 |
| Average initial quality | 0.8711 |
| Average final quality | 0.9036 |
| Corrective retries triggered | 1 |
| Scenarios improved after retry | 1 |

## Parseable check results

| Check ID | Category | Evaluation criteria | Result | Key evidence |
|---|---|---|---|---|
| `profile-high-energy-pop` | recommendation | top result is Sunrise City; retry=false; final strategy=balanced; final quality >= 0.85 | **Pass** | top=Sunrise City; quality=0.9014→0.9014; retry=false |
| `profile-chill-lofi` | recommendation | top result is Midnight Coding; retry=false; final strategy=balanced; final quality >= 0.85 | **Pass** | top=Midnight Coding; quality=0.9042→0.9042; retry=false |
| `profile-deep-intense-rock` | recommendation | top result is Storm Runner; retry=false; final strategy=balanced; final quality >= 0.85 | **Pass** | top=Storm Runner; quality=0.9395→0.9395; retry=false |
| `profile-conflicting-sad-workout` | recommendation | top result is Blue Sunday; retry=true; final strategy=mood_first; final quality >= 0.85; final quality improves | **Pass** | top=Blue Sunday; quality=0.7076→0.9029; retry=true |
| `profile-custom-acoustic-jazz` | recommendation | top result is Coffee Shop Stories; retry=false; final strategy=balanced; final quality >= 0.85 | **Pass** | top=Coffee Shop Stories; quality=0.8782→0.8782; retry=false |
| `profile-missing-catalog-support` | recommendation | top result is Concrete Crown; retry=false; final strategy=balanced; final quality >= 0.85; warning contains 'no exact genre match' | **Pass** | top=Concrete Crown; quality=0.8956→0.8956; retry=false |
| `guardrail-invalid-energy` | guardrail | Validation rejects the value with a readable range message | **Pass** | target_energy must be between 0.0 and 1.0. |
| `guardrail-strict-catalog` | guardrail | Strict mode rejects the catalog with a readable validation error | **Pass** | Song catalog validation failed: - Row 3: energy must be between 0.0 and 1.0. |
| `guardrail-lenient-catalog` | guardrail | Lenient mode skips the malformed row and retains the valid row | **Pass** | valid rows returned=1 |
| `reliability-deterministic-repeat` | reliability | Both structured outputs are identical | **Pass** | identical=True; top_recommendation=Sunrise City; quality_score=0.9014 |

## Interpretation

The benchmark supports reliability claims within the included 18-song catalog. The quality score is a deterministic heuristic used for comparison and retry decisions; it is not a calibrated probability that a listener will enjoy a song. The missing-catalog-support scenario passes because the system returns a stable energy-aligned ranking while explicitly warning that exact genre and mood matches are unavailable.

Complete machine-readable results are stored in [`results.json`](results.json).

# Model Card: VibeMatch 2.0

## 1. System Name and Version

**VibeMatch 2.0: Adaptive and Reliable Music Recommender**

VibeMatch 2.0 is an explainable, deterministic, content-based recommendation system. It extends the original **Music Recommender Simulation**, also called **VibeMatch 1.0**, from Modules 1–3 into a complete applied AI system with validation, modular scoring strategies, a bounded agentic workflow, diversity guardrails, reliability evaluation, logging, and reproducible testing.

## 2. Intended Use

VibeMatch generates ranked music recommendations from a local catalog using a listener's stated preferences. A user can select a built-in profile or provide custom preferences for genre, mood, energy, acousticness, priority, and optional musical features such as valence, danceability, and tempo.

The system is intended for:

- Classroom exploration of recommendation logic and applied AI reliability
- Demonstrating explainable ranking and bounded self-correction
- Testing how design choices and scoring weights affect recommendations
- A technical portfolio example for software engineering and AI roles

The system assumes that users can express their current preferences through structured attributes. It does not infer identity, mental health, personality, or emotional state.

VibeMatch should not be used as:

- A commercial recommendation service
- An objective measure of song quality
- A calibrated prediction that a person will enjoy a song
- Evidence about a person's identity, mood, or behavior
- A replacement for a production platform trained on large-scale listening data

## 3. Original Project and System Evolution

The original Modules 1–3 project was **Music Recommender Simulation / VibeMatch 1.0**. It loaded a fictional song catalog, represented listener preferences as structured data, calculated weighted content-similarity scores, and returned explained top-k recommendations. Its original balanced formula prioritized exact genre and mood matches, energy similarity, and acoustic preference.

VibeMatch 2.0 preserves that original formula as the `balanced` strategy while adding:

- Strict and lenient catalog validation
- User-profile validation and normalization
- Multiple scoring strategies
- A `RecommendationAgent` that plans, recommends, evaluates, and revises
- A one-retry limit for predictable behavior
- Artist and genre diversity controls
- A structured reliability evaluator
- Catalog-support warnings
- Runtime logging
- Expanded automated tests
- A reproducible evaluation benchmark

## 4. How the System Works

### Inputs

The system accepts:

1. Listener preferences from the command-line interface
2. Song metadata from `data/songs.csv`

Each song contains:

- ID
- Title
- Artist
- Genre
- Mood
- Energy
- Tempo
- Valence
- Danceability
- Acousticness

A user profile can contain:

- Favorite genre
- Favorite mood
- Target energy
- Acoustic preference
- Priority
- Optional target valence
- Optional target danceability
- Optional target tempo

### Validation

Before ranking begins, VibeMatch checks user preferences and catalog fields. Invalid ranges, missing values, unsupported booleans, malformed rows, and missing headers produce readable errors.

Strict catalog mode stops when malformed data is found. Lenient mode skips invalid rows and keeps valid rows when partial recovery is more useful.

### Strategy Selection

VibeMatch includes five scoring strategies:

- `balanced`
- `genre_first`
- `mood_first`
- `energy_focused`
- `discovery`

The original VibeMatch 1.0 weights are preserved in `balanced`. Other strategies adjust the relative importance of preference signals. These are transparent, manually designed heuristics rather than learned model weights.

### Agentic Workflow

The `RecommendationAgent` performs a bounded workflow:

1. Validate and normalize the user profile.
2. Select an initial strategy.
3. Score and rank a larger candidate pool.
4. Apply artist and genre diversity limits.
5. Evaluate the resulting top-k list.
6. Return the result if quality is sufficient.
7. When the evaluator detects an underrepresented priority, select a corrective strategy and rerank once.
8. Return the final result after the retry, even if additional improvement might still be possible.

The one-retry limit prevents infinite loops and makes behavior easier to reproduce and inspect.

### Explanations

Each recommendation includes the score contributions that affected its ranking, such as:

- Genre match
- Mood match
- Energy similarity
- Acoustic preference match
- Valence similarity
- Danceability similarity
- Tempo similarity

### Reliability Evaluation

The evaluator measures:

- Priority alignment
- Energy alignment
- Artist and genre diversity
- Score strength
- Explanation completeness
- Catalog support
- Number of recommendations returned

The final quality score is a deterministic heuristic used to compare results and decide whether a retry is useful. It is **not** a probability, calibrated confidence estimate, or guarantee of user satisfaction.

## 5. Data

VibeMatch uses 18 fictional songs stored in `data/songs.csv`. The catalog includes multiple genres and moods, with continuous attributes for energy, tempo, valence, danceability, and acousticness.

### Data strengths

- The data is small enough to inspect manually.
- Every recommendation can be traced back to explicit catalog attributes.
- Fictional songs avoid collecting personal listener data.
- The catalog supports deterministic testing.

### Data limitations

- Eighteen songs cannot represent the full diversity of music.
- Genre and mood are stored as single exact labels.
- Some preference combinations have limited or no exact support.
- The catalog was manually constructed and may reflect developer assumptions.
- There is no real listening history, user feedback, skip behavior, replay behavior, language information, or cultural context.

When the requested genre or mood is absent, the system can still return an energy-aligned ranking, but it explicitly warns the user that exact catalog support is missing.

## 6. Reliability and Evaluation Results

The project includes automated tests, deterministic benchmarking, validation checks, error handling, structured logs, and human-readable explanations.

### Automated testing

**18 out of 18 automated tests passed.**

The suite covers:

- Original ranking behavior
- Explanation generation
- Profile normalization
- Invalid numerical ranges
- Boolean parsing
- Required catalog headers
- Strict malformed-row rejection
- Lenient malformed-row recovery
- Artist and genre diversity limits
- Diversity-limit relaxation
- Empty recommendation behavior
- Missing explanation warnings
- Quality-score boundaries
- Strong-profile pass-through behavior
- Corrective agent reranking
- Agent-result serialization
- Invalid top-k handling
- Safe CLI failure without a traceback

### Deterministic benchmark

**10 out of 10 benchmark checks passed.**

| Metric | Result |
|---|---:|
| Benchmark pass rate | 100% |
| Recommendation scenarios | 6 |
| Guardrail and reliability checks | 4 |
| Average initial quality | 0.8711 |
| Average final quality | 0.9036 |
| Corrective retries triggered | 1 |
| Scenarios improved after retry | 1 |

The strongest corrective example was the `conflicting-sad-workout` profile:

- Initial strategy: `balanced`
- Initial quality: `0.7076`
- Final strategy: `mood_first`
- Final quality: `0.9029`
- Quality improvement: `0.1953`
- Final top recommendation: `Blue Sunday`

The benchmark also confirmed that:

- Strong profiles remain unchanged when correction is unnecessary.
- Repeated runs produce identical structured output.
- Invalid profile values are rejected safely.
- Strict mode rejects malformed catalogs.
- Lenient mode preserves valid rows.
- Unsupported genre and mood requests produce explicit warnings.

The complete evidence is stored in:

- `evaluation/results.md`
- `evaluation/results.json`
- `evaluation/reproducible-output.txt`

Reproduce the results with:

```bash
pytest -q
python -m evaluation.run_evaluation
```

## 7. Strengths

VibeMatch works best when the catalog contains songs that directly support the listener's preferences. Its main strengths are:

- Transparent scoring rules
- Deterministic and reproducible behavior
- Explanations for every recommendation
- Visible quality and guardrail information
- Early validation and safe failures
- Modular strategies
- Bounded self-correction
- Diversity controls
- Structured runtime logging
- Machine-readable evaluation evidence

The agentic workflow meaningfully changes system behavior. It does not merely print an evaluation beside the original result. When a priority is underrepresented, the evaluator requests a retry, the agent changes strategies, and the final ranking can change.

## 8. Limitations, Bias, and Failure Modes

### Small and manually selected catalog

The catalog contains only 18 fictional songs. Users with underrepresented preferences may receive weak or indirect matches. A high quality score within this catalog does not imply strong real-world recommendation quality.

### Exact categorical labels

Genre and mood are compared as exact labels. The system cannot recognize that two differently labeled songs may share musical qualities, or that one song may span multiple genres and emotional states.

### Developer-selected weights

Every strategy uses manually selected weights. These choices encode assumptions about which features should matter most. A different developer could choose different weights and produce different rankings.

### Subjective reliability thresholds

The evaluator's thresholds are heuristics. They are useful for consistent testing but may not align with every listener's subjective judgment.

### Simplified acoustic preference

Acoustic preference is treated as a binary classification using a fixed threshold, even though acousticness is continuous.

### No personalization from behavior

VibeMatch does not learn from likes, skips, replays, searches, session context, or long-term listening patterns. It cannot adapt across sessions.

### One-retry limit

The bounded retry improves predictability, but one correction may be insufficient when the catalog lacks appropriate content or several priorities conflict.

### Diversity trade-off

The diversity guardrail may move a slightly lower-scoring song above a repeated artist or genre. This improves variety but can reduce strict score optimality.

### Quality score interpretation

The quality score is not a confidence probability. Reporting it as the chance that a user will enjoy a recommendation would be misleading.

### Potential representation bias

The manually created genres, moods, artists, and song characteristics may reflect a limited cultural perspective. A production system would require broader data review, representative evaluation, and input from diverse listeners.

## 9. Human Oversight and Responsible Use

Users and developers should review:

- Recommendation explanations
- Reliability warnings
- Catalog-support warnings
- Diversity adjustments
- Initial and final strategy choices
- Runtime logs
- Parseable benchmark results

Human review remains important because musical preference is subjective. Passing the benchmark means that the system met predefined technical criteria within the included catalog, not that every recommendation is personally correct.

The system should be presented as an educational recommendation tool. It should not make sensitive inferences, profile users beyond their provided preferences, or claim certainty about emotional state or identity.

## 10. AI Collaboration Reflection

### How I collaborated with AI

I used AI as a development assistant while extending VibeMatch 1.0 into VibeMatch 2.0. AI helped me break the assignment into phases, brainstorm an agentic workflow, separate scoring behavior into modular strategies, draft validation and evaluation cases, organize documentation, and generate test scenarios. I applied each phase locally, inspected the changed files, ran the application and tests, reviewed terminal output, and committed the work only after verification.

AI did not make final decisions independently. I was responsible for preserving the original project history, checking repository state, verifying actual outputs, deciding which suggestions matched the rubric, and rejecting or correcting claims that were not supported by the code.

### One helpful AI suggestion

A particularly helpful suggestion was to use a **bounded evaluator-driven retry** rather than simply adding more scoring weights to the original recommender. This created a meaningful agentic loop: the system generates a ranking, measures whether the user's stated priority is represented, selects a corrective strategy when necessary, and reranks once. The conflicting sad-workout benchmark demonstrated that this suggestion improved the quality score from `0.7076` to `0.9029` and changed the top recommendation to `Blue Sunday`.

### One flawed AI suggestion

During an earlier weight-shift experiment, an AI-assisted plan proposed reducing the genre contribution and doubling the energy contribution. The first implementation changed the genre weight but accidentally left the energy multiplier at its original value. The explanation therefore described an experiment that the code had not fully performed.

I caught the problem by inspecting the scoring code and comparing the actual rankings with the expected effect. I corrected the experiment before using its findings. This reinforced that AI-generated code and explanations must be verified against the implementation and runtime output.

### What I verified manually

I manually verified:

- The original Git history remained intact.
- The new repository remote was correct.
- Original recommendation behavior remained available through `balanced`.
- All application profiles executed.
- Invalid inputs failed safely.
- The conflicting profile triggered exactly one retry.
- The final strategy and rankings changed as expected.
- Plain `pytest` worked after project configuration was corrected.
- All 18 tests passed.
- All 10 benchmark checks passed.
- Runtime logs were generated but ignored by Git.
- The architecture diagram matched real modules.
- README examples matched actual command output.
- The quality score was described as a heuristic rather than a probability.

## 11. Ethical Lessons

This project showed me that an AI system can return valid-looking output while still underrepresenting the user's most important intent. Reliability therefore requires more than checking whether the code runs. It requires explicit criteria, edge cases, warnings, explanations, reproducibility, and human review.

It also showed me that transparency does not remove bias. Even when every weight is visible, the selected features, thresholds, catalog, and evaluation rules still reflect human decisions. Responsible development means documenting those decisions, measuring their effects, and avoiding claims that the evidence does not support.

## 12. Future Work

Potential improvements include:

- Expanding and auditing the catalog
- Supporting multiple genres and moods per song
- Learning ranking weights from user feedback
- Adding collaborative filtering
- Parsing natural-language preferences
- Adding persistent likes, skips, and replay signals
- Testing with human evaluators from varied backgrounds
- Measuring ranking metrics on a larger labeled dataset
- Calibrating or replacing heuristic quality thresholds
- Testing every strategy and threshold combination
- Adding a graphical interface
- Allowing users to inspect and adjust strategy weights

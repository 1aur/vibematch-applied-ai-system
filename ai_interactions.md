# AI Interactions Log

> **Stretch features only.** This file documents the agentic development workflow and design-pattern work used while extending VibeMatch.

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

I asked the AI assistant to help extend my Modules 1–3 Music Recommender Simulation into a complete applied AI system. The upgraded system needed an integrated agentic workflow, reliability evaluation, guardrails, logging, reproducible tests, a Mermaid architecture diagram, professional documentation, and a responsible-AI model card. I also required the original Git history and balanced scoring behavior to remain intact.

**Prompts used:**

Key instructions included:

- "Extend my Module 3 music recommender into a full applied AI system with an agentic workflow, reliability testing, guardrails, logging, and reproducible setup."
- "Preserve the original scoring behavior and original TODO comments where applicable."
- "Make the advanced feature change the application's actual behavior, not just run as a standalone script."
- "Create each phase as a ZIP, let me apply and test it locally, and tell me exactly what to commit."
- "Audit the entire repository against the full CodePath project checklist."

**What did the agent generate or change?**

The AI assistant helped draft or organize:

- `src/agent.py`
- `src/diversity.py`
- `src/evaluator.py`
- `src/logging_config.py`
- `src/strategies.py`
- `src/validation.py`
- Updates to `src/main.py` and `src/recommender.py`
- `pytest.ini`
- Expanded automated test files
- `evaluation/run_evaluation.py`
- Parseable JSON, Markdown, and text evaluation evidence
- `diagrams/vibematch-system-architecture.mmd`
- The employer-facing `README.md`
- The updated `model_card.md`

The work was delivered in phases so that each group of changes could be applied, executed, inspected, tested, and committed separately.

**What did you verify or fix manually?**

I manually:

- Corrected the local repository and remote setup after initially working in a non-Git copy.
- Preserved the original commit history.
- Confirmed that generated ZIP files extracted into the correct paths.
- Ran every built-in and custom profile.
- Verified the conflicting profile changed from `balanced` to `mood_first`.
- Confirmed the quality score improved from `0.7076` to `0.9029`.
- Tested invalid input and catalog error handling.
- Resolved the Python and pytest import-path mismatch.
- Ran all 18 automated tests and the 10-check benchmark.
- Inspected logging output and Git ignore behavior.
- Compared README examples with actual output.
- Reviewed staged files before every commit.
- Corrected misleading or unsupported language, especially any suggestion that the quality score was a probability.

One flawed AI-assisted experiment proposed reducing genre weight and doubling energy influence, but the first code change did not actually modify the energy multiplier. I caught this by reviewing the code and output before accepting the result.

---

## Design Pattern (SF10)

**Which design pattern did you use?**

I used the **Strategy pattern** for recommendation scoring.

**How did AI help you brainstorm or implement it?**

The AI assistant suggested separating scoring configurations from the core ranking loop instead of adding more conditional logic directly inside the recommender. We discussed preserving the original scoring formula as a default strategy while supporting targeted alternatives for genre, mood, energy, and discovery.

This approach made it possible for the agent to change behavior during a corrective retry without rewriting the recommendation algorithm.

**How does the pattern appear in your final code?**

The pattern is implemented in `src/strategies.py`, which defines named scoring strategies and exposes a registry through functions such as `get_strategy` and `normalize_strategy_name`.

`src/recommender.py` receives a strategy name and applies the selected weights while scoring songs. `src/agent.py` initially uses `balanced` in automatic mode, evaluates the output, and can switch to `genre_first`, `mood_first`, `energy_focused`, or `discovery` for one corrective rerank.

This keeps strategy selection separate from candidate scoring and makes new strategies easier to add and test.

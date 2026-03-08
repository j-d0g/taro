# Harness Engineering

## Core Principle

An environment rich with **JIT feedback and verification methods** is essential for harness engineering.

The art is in describing the edges and boundaries — but placing them in the right spots. The model needs **unconstrained creativity** in *how* it achieves a solution, paired with **rigorous methods for verifying** *when* a solution suffices.

Constraints define the shape of the solution space. Verification confirms you've landed inside it.

## The Feedback Spectrum

Harness signals range from hard/automated to soft/human, and from synchronous to asynchronous:

### Hard Signals (automated, deterministic)
- **Linters** — immediate structural correctness feedback on every edit
- **Type checkers** — catch contract violations before runtime
- **Test suites** — verify behavior against known expectations
- **Custom error messages** — domain-specific guardrails that speak the model's language ("you forgot to close the DB connection" > generic stack trace)
- **File-system naming conventions** — structural constraints that encode intent (e.g., `test_*.py`, `schema/*.surql`)

### Soft Signals (heuristic, probabilistic)
- **Reranker scores** — confidence measure on retrieval quality; low scores signal the search missed
- **Tool-call efficiency** — are we making 12 calls where 3 would do? Measures solution elegance
- **Model confusions** — when the model asks clarifying questions or contradicts itself, the harness is under-specified
- **To-do lists / plans** — structured self-tracking that externalizes intent and progress

### Async / Reflective Signals
- **Async reflection agent reviewing stack traces** — a second model pass that diagnoses failures with fresh context, not the sunk-cost reasoning of the agent that caused them
- **Conversation abandonment** — the user gave up; strongest negative signal, hardest to capture
- **Human dissatisfaction** — explicit thumbs-down, corrections, or re-prompts; the ground truth that all other signals approximate

## Design Heuristics

1. **Constrain outputs, not process.** Define what "done" looks like. Don't prescribe the steps to get there.
2. **Make failure loud and specific.** A custom error message that says "BM25 index missing on field X" is worth more than a generic 500.
3. **Layer feedback by latency.** Linters fire in ms, tests in seconds, reflection agents in minutes, human feedback in hours. Cover all timescales.
4. **Treat verification as a product.** The quality of your verification signals directly determines the ceiling of what the agent can achieve autonomously.
5. **Watch for signal absence.** The most dangerous state is when the harness is silent but the solution is wrong. Actively probe for gaps.

# Strategy 4 - Isolation via Sub-Agents

Source: CS440 Agentic AI Context Engineering slides

The main Claude Code agent acts as orchestrator.
It can delegate limited-scope work to the specialist definitions under `.claude/agents/`:

- `environment-reviewer`: reviews simulator rules and model separation.
- `test-reviewer`: reviews tests and coverage.
- `researcher`: plans how to build a piece around the environment, read-only.
- `research-implementer`: turns the researcher's brief into docs under `context/research/`, and edits nothing else.
- `research-verifier`: reviews the docs in `context/research/` and runs the research verification tests listed in `context/testing.md`; edits nothing.

Every agent reads the shared rules in `.claude/constraints.md` and returns JSON matching `.claude/agents/report.schema.json`.
The orchestrator combines their short findings, preventing full project history from leaking into every specialist task.

## Running
Run from `strategy_4/`:

- `python orchestrator.py` (or `review [agent ...]`): run the reviewers.
- `python orchestrator.py pipeline "question"`: researcher -> research-implementer -> research-verifier.

The pipeline stops if the researcher reports any FAIL or UNKNOWN.
The implementer receives only a brief built by code from the researcher's INFO findings, never the researcher's context.

## Demonstration prompt
"Use the environment-reviewer subagent to check grid and terminal-state rules, and the test-reviewer subagent to check test coverage.
Return separate findings and a brief combined summary.
Do not implement Q-learning."

Everything stays inside `strategy_4/`; the only outside access is read-only `../vacuum/`.
Launch Claude Code from `strategy_4/` so it finds `.claude/agents/`.

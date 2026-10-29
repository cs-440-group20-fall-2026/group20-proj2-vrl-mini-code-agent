# Strategy 4 - Isolation via Sub-Agents

Source: CS440 Agentic AI Context Engineering slides

The main Claude Code agent acts as orchestrator.
It can delegate limited-scope work to the specialist definitions under `.claude/agents/`:

- `environment-reviewer`: reviews simulator rules and model separation.
- `test-reviewer`: reviews tests and coverage.

Each agent's prompt restricts its scope to specific files.
The orchestrator combines their short findings, preventing full project history from leaking into every specialist task.

## Demonstration prompt
"Use the environment-reviewer subagent to check grid and terminal-state rules, and the test-reviewer subagent to check test coverage.
Return separate findings and a brief combined summary.
Do not implement Q-learning."

Everything stays inside `strategy_4/`; the only outside access is read-only `../vacuum/`.
Launch Claude Code from `strategy_4/` so it finds `.claude/agents/`, or run `python orchestrator.py` to spawn each agent in its own process.

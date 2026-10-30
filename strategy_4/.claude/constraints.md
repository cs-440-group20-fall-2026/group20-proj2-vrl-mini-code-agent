# Shared Agent Constraints

Every agent in `.claude/agents/` follows these rules.

## Scope
- Stay inside `strategy_4/`; its subdirectories are included and paths are relative to it.
- Only exception: `../vacuum/` may be read, never edited.
- No web access.
- Work only from the task you're given; don't access unrelated project history.

## Rules
- The RL learner never gets T or R tables; it learns only from `reset()` and `step()`.
- Python standard library only.

## Forbidden: Q-learning is a later lab
- No Q-learning in code or docs. Forbidden terms: Q-learning, Q-tables, Q-values, Q(s,a), Bellman updates, value iteration, policy iteration, temporal-difference updates, TD updates, SARSA, learning rates.
- Don't mention these terms at all, even to rule them out.
- `orchestrator.py` blocks any research finding that mentions them and flags any research doc that does.
- `tests/test_research.py` fails on them.

## Output
- Return only JSON matching `.claude/agents/report.schema.json`.
- One finding per point.
- Cite evidence as `file:line`, or the path you changed.

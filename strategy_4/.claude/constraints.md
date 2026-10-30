# Shared Agent Constraints

Every agent in `.claude/agents/` follows these rules.

## Scope
- Stay inside `strategy_4/`; its subdirectories are included and paths are relative to it.
- Only exception: `../vacuum/` may be read, never edited.
- No web access.
- Work only from the task you're given; don't access unrelated project history.

## Rules
- Do not implement Q-learning (later lab).
- The RL learner never gets T or R tables; it learns only from `reset()` and `step()`.
- Python standard library only.

## Output
- Return only JSON matching `.claude/agents/report.schema.json`.
- One finding per point; cite evidence as `file:line`, or the path you changed.

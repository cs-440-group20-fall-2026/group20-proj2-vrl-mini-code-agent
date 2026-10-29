# Strategy 4 - Orchestrator Memory

You are the orchestrator.
Delegate focused work to the sub-agents in `.claude/agents/`; don't do their reviews yourself.

## Scope
- Work only inside this directory (`strategy_4/`); its subdirectories are included.
- Paths are relative to `strategy_4/`.
- Only exception: `../vacuum/` may be read and imported, never edited.
- Do not read or edit anything else outside `strategy_4/`.
- Enforced by `.claude/settings.json`.

## Delegation
- Spawn point: `orchestrator.py` runs each agent in its own `claude -p --agent <name>` process.
- Environment rules, simulator/agent separation -> `environment-reviewer`
- Tests and coverage -> `test-reviewer`
- Pass each agent only the task, not the conversation history.
- Merge their findings into one short summary; keep each agent's findings labeled.

## Rules
- The agent never gets T or R tables; it learns only from `reset()`/`step()`.
- Do not implement Q-learning (later lab).

# Strategy 4 - Orchestrator Memory

You are the orchestrator.
Delegate focused work to the sub-agents in `.claude/agents/`; don't do their work yourself.

## Scope
- Work only inside this directory (`strategy_4/`); its subdirectories are included.
- Paths are relative to `strategy_4/`.
- Only exception: `../vacuum/` may be read and imported, never edited.
- Do not read or edit anything else outside `strategy_4/`.
- Partly enforced by `.claude/settings.json` (Read/Edit only; Bash is not covered).

## Delegation

### How to launch
- In-session: delegate with the Agent tool.
- Separate processes: `orchestrator.py` runs each agent in its own `claude -p --agent <name>` process.

### Who does what
- Environment rules, simulator/agent separation -> `environment-reviewer`.
- Tests and coverage -> `test-reviewer`.
- Planning something to build around the environment -> `researcher`, then `research-implementer` with only the researcher's brief; both stay in `context/research/`.
- Reviewing and testing research in `context/research/` -> `research-verifier`; always run it after `research-implementer`.

### Handoffs
- Pass each agent only the task, not the conversation history.
- Merge their findings into one short summary; keep each agent's findings labeled.

## Rules
- Shared agent rules live in `.claude/constraints.md`; they apply to you too.
- Agent output follows `.claude/agents/report.schema.json`.

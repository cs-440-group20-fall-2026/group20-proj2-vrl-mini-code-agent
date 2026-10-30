# Strategy 4 - Isolation via Sub-Agents

Source: CS440 Agentic AI Context Engineering slides

The main Claude Code agent acts as orchestrator.
It delegates limited-scope work to specialist sub-agents, so full project history never leaks into each specialist's task.

## Agents
Definitions live under `.claude/agents/`:

| Agent | Job | Writes |
|---|---|---|
| `environment-reviewer` | reviews simulator rules and model separation | nothing |
| `test-reviewer` | reviews tests and coverage | nothing |
| `researcher` | researches groundwork for our RL problem (episode runner, exploration, sample logging, counts, metrics) | nothing |
| `research-implementer` | turns the researcher's brief into docs | `context/research/` only |
| `research-verifier` | reviews the docs in `context/research/` and runs the research verification tests listed in `context/testing.md` | nothing |

## Shared files
- `.claude/constraints.md`: rules every agent reads first.
- `.claude/agents/report.schema.json`: the JSON every agent returns.
- The orchestrator combines their short findings into one labeled summary.

## Running
Run from `strategy_4/`:

```bash
python3 orchestrator.py                      # run the reviewers (or: review [agent ...])
python3 orchestrator.py pipeline "question"  # researcher -> research-implementer -> research-verifier
```

On Windows, use `python` instead of `python3`.

## Pipeline gate
The pipeline stops if the researcher:
- reports any FAIL,
- has no INFO findings (an off-topic decline), or
- mentions a forbidden term.

The implementer receives only a brief built by code from the researcher's INFO findings, plus its UNKNOWN findings as open questions.
It never sees the researcher's context.

## Q-learning gate
Q-learning is a later lab, so it is gated in three layers:
- Rule: the "Forbidden" list in `.claude/constraints.md`, which every agent reads.
- Code: `orchestrator.py` scans research findings with a regex (no LLM) and stops the pipeline before the implementer; it also scans `context/research/` afterwards and adds a FAIL.
- Test: `tests/test_research.py` fails if any research doc contains a forbidden term; the verifier runs it.

## Demonstration prompt
"Use the environment-reviewer subagent to check grid and terminal-state rules, and the test-reviewer subagent to check test coverage.
Return separate findings and a brief combined summary.
Do not implement Q-learning."

## Scope
Everything stays inside `strategy_4/`; the only outside access is read-only `../vacuum/`.
Launch Claude Code from `strategy_4/` so it finds `.claude/agents/`.

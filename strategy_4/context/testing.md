# Testing Context (test-reviewer, research-verifier)

## Scope
Scope: `strategy_4/` and its subdirectories only; paths are relative to it.
Tests import the environment from `../vacuum/` (read-only).

## Running
Run from `strategy_4/`:

```bash
PYTHONPATH=.. python3 -m unittest discover -s tests -v
```

On Windows: `set PYTHONPATH=..`, then `python -m unittest discover -s tests -v`.

## Files
- `tests/test_ground_truth.py` - one recorded run: input actions and expected outputs.
  Don't modify.
- `tests/test_orchestrator.py` - sub-agent config wiring, and learner isolation (only `reset()`/`step()`).
- `tests/test_research.py` - research docs in `context/research/` stay groundwork-only (no Q-learning).

## Rules
- Deterministic tests use `intended_probability=1`; stochastic tests use fixed seeds.
- Never assume a stochastic run always succeeds.
- Tests use only `reset()`/`step()`, never simulator internals.

## Research verification
Run by `research-verifier` after every research implementation in `context/research/`.
`orchestrator.py` sets `PYTHONPATH`, so the commands need no prefix.

- `python3 -m unittest tests.test_ground_truth -v`: the environment still matches the recorded run.
- `python3 -m unittest tests.test_orchestrator -v`: agent wiring and learner isolation still hold.
- `python3 -m unittest tests.test_research -v`: research docs contain no Q-learning terms.

A FAIL in any of these means the research implementation can't be accepted.

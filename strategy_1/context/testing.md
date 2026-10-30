# Testing Context

## Scope
- **Scope:** `strategy_1/` and its subdirectories only; paths are relative to it. 
- **Read-only Exception:** Tests import the environment from `../vacuum/` (read-only).


## Files
All tests live in `testing/`:
- `testing/baseline_test.py` — Verifies the deterministic scripted path (`intended_probability=1.0`) starts at `START`, reaches the charger, and receives the `+10` reward.
- `testing/test_performance.py` — Runs multi-episode evaluations: deterministic baseline reward/step metrics (fixed seeds `42`+) and a stochastic completion-rate benchmark (seeds `100`+).
- `testing/performance_benchmark.py` — Runs a 20-episode stochastic benchmark (seeds `200`+) and reports success rate and average episode reward.

## Rules & Constraints
- **Determinism & Seeds:** Use `intended_probability=1` for deterministic verification tests, and fixed seeds (e.g., `seed=42`) for reproducible stochastic test runs.
- **Stochastic Expectation:** Never assume a stochastic run always succeeds; account for movement variance.
- **Simulator Isolation:** Tests must interact exclusively via `reset()` and `step()` methods, never accessing private simulator internal tables ($T$ or $R$).
- **No Q-learning:** Ensure test files remain focused on environment verification and performance metrics without implementing Q-learning.

## Running Tests
Run tests from the `strategy_1/` directory. The `-p "*.py"` pattern is required because `baseline_test.py` and `performance_benchmark.py` do not match unittest's default `test*.py` pattern:

From Root Directory (vacuum-rl-context-engineering):

PYTHONPATH=. python3 -m unittest discover -s strategy_1/testing -p "*.py" -v

From Inside strategy_1/ Directory:

cd strategy_1
PYTHONPATH=.. python3 -m unittest discover -s testing -p "*.py" -v

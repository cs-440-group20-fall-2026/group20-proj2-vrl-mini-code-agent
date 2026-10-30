# Testing Context

## Scope
- **Scope:** `strategy_1/` and its subdirectories only; paths are relative to it. 
- **Read-only Exception:** Tests import the environment from `../vacuum/` (read-only).


## Files
- `tests/test_environment.py` — Verifies core grid behavior, boundaries, obstacles, and terminal states (`reset`, `charger_terminal`, `trap_terminal`).
- `tests/test_performance.py` — Runs multi-episode evaluations, tracking performance metrics, rewards, and multi-run success rates under deterministic and stochastic conditions.

## Rules & Constraints
- **Determinism & Seeds:** Use `intended_probability=1` for deterministic verification tests, and fixed seeds (e.g., `seed=42`) for reproducible stochastic test runs.
- **Stochastic Expectation:** Never assume a stochastic run always succeeds; account for movement variance.
- **Simulator Isolation:** Tests must interact exclusively via `reset()` and `step()` methods, never accessing private simulator internal tables ($T$ or $R$).
- **No Q-learning:** Ensure test files remain focused on environment verification and performance metrics without implementing Q-learning.

## Running Tests
Run tests from the `strategy_1/` directory using:
```bash
PYTHONPATH=.. python3 -m unittest discover -s tests -v
(On Windows: set PYTHONPATH=.., then run python -m unittest discover -s tests -v)


---
name: vacuum-rl-report
description: Run the CS440 Lab 5 tabular Q-learning experiments for the 4x4 vacuum robot, verify the tests, and summarize the generated CSV/Markdown reports (charger success rate, trap rate, mean reward, mean steps). Use when asked to train/evaluate the vacuum Q-learner, regenerate Lab 5 reports, or compare living reward, gamma, alpha, or epsilon settings.
argument-hint: "[--quick] [--seeds 0 1 2] [--train-episodes N] [--eval-episodes N]"
allowed-tools: Bash(python -m unittest *), Bash(python -m lab_5.run_experiments *), Read, Grep, Glob
---

# Vacuum RL Report (Lab 5)

Produce and summarize Q-learning reports for the vacuum environment. Work from the
repository root.

## Ground rules
- The learner (`lab_5/q_learning.py`) may use **only** `env.reset()` and `env.step(action)`.
  Never pass transition or reward tables, `_rng`, `_intended_probability`, or other
  simulator internals to it, and never read them to "explain" results.
- Do not edit `strategy_1/` or `strategy_4/` (Lab 4 deliverables), or `vacuum/environment.py`
  unless the user explicitly asks for an environment change.
- Living reward is set through the public constructor argument
  `VacuumEnvironment(living_reward=...)` (default `-0.04`).
- Keep seeds deterministic; do not report a single lucky seed as the result.

## Steps
1. **Run the tests first.** Stop and report failures verbatim if any fail:
   ```bash
   python -m unittest discover -s lab_5/tests -t . -v
   python -m unittest discover -s tests -v
   ```
2. **Generate reports**, forwarding any arguments the user gave (`$ARGUMENTS`):
   ```bash
   python -m lab_5.run_experiments $ARGUMENTS
   ```
   With no arguments this runs the full grid (living reward x gamma x alpha x epsilon,
   seeds 0 1 2). Use `--quick` for a fast two-configuration check.
3. **Read** `lab_5/reports/report.md` (and `lab_5/reports/results.csv` if a figure needs checking).
4. **Summarize** in at most ~10 lines:
   - the best configuration and its charger success rate, trap rate, mean reward, mean steps;
   - how living reward changes trap rate and mean reward (note the trade-off around -5.5);
   - any effect of gamma, alpha, or epsilon visible in the table;
   - any timeouts (episodes that hit `--max-steps`).
   Quote numbers from the report; do not invent them.
5. Tell the user where the files are and the exact command to reproduce them.

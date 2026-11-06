# Lab 5 - Tabular Q-Learning for the Vacuum Robot

Lab 5 adds a model-free Q-learning agent on top of the Lab 4 simulator in `vacuum/`.
Lab 4 work (`strategy_1/`, `strategy_4/`, `scripts/demo.py`, `tests/`) is unchanged.

## Files
```
lab_5/
├── q_learning.py        # QLearningAgent, QLearningConfig, train(), evaluate(), run_trial()
├── run_experiments.py   # hyperparameter grid, metrics, CSV + Markdown report writers
├── reports/             # generated: results.csv, report.md
└── tests/
    ├── test_q_learning.py   # updates, terminal handling, exploration, reproducibility
    └── test_reports.py      # metrics, CSV/Markdown generation, CLI
.claude/skills/vacuum-rl-report/SKILL.md   # Claude Code skill that runs and summarizes this
```

## How the learner sees the environment
- The agent interacts only through `env.reset()` and `env.step(action)`, and learns from the
  returned `state`, `reward` and `terminated` values. It never receives transition
  probabilities or reward tables. `test_learner_uses_only_reset_and_step` uses a fake
  environment that fails on any other attribute access.
- Living reward is set through the existing public constructor argument
  `VacuumEnvironment(living_reward=...)`. It already defaulted to `-0.04`, so the environment did not change.
- Update: `Q(s,a) += alpha * (target - Q(s,a))`, with `target = r` at terminal states and
  `r + gamma * max_a' Q(s',a')` otherwise.
- Exploration: epsilon-greedy with seeded random tie-breaking; optional `--epsilon-decay`.
- Training runs on an environment seeded with `seed`. Evaluation runs **greedy, with no
  learning**, on a separate environment seeded with `seed + 10000`.
- Charger, trap and timeout labels are assigned by the experiment harness, not the agent.

## Run
From the repository root (Python 3.10+, standard library only):

```bash
python -m unittest discover -s lab_5/tests -t . -v   # Lab 5 tests
python -m lab_5.run_experiments                      # full grid, seeds 0 1 2 (~10 s)
python -m lab_5.run_experiments --quick              # 2 configs, fast check
python -m lab_5.run_experiments --seeds 0 1 2 3 4 --train-episodes 5000 --eval-episodes 1000
```

Options: `--seeds`, `--train-episodes` (2000), `--eval-episodes` (500), `--max-steps` (100),
`--epsilon-decay` (1.0), `--output-dir` (`lab_5/reports`), `--quick`.

Outputs:
- `lab_5/reports/results.csv`: one row per configuration (living reward, gamma, alpha, epsilon),
  pooled across seeds, with `charger_success_rate`, `trap_rate`, `timeout_rate`, `mean_reward`,
  `mean_steps`, and `train_charger_rate`.
- `lab_5/reports/report.md`: the same results as a table, plus the best configuration and its greedy policy grid.

## Invoking the Claude Code skill
Open Claude Code in the repository root, then either:

- type `/vacuum-rl-report` (full grid), or pass arguments such as
  `/vacuum-rl-report --quick` or `/vacuum-rl-report --seeds 0 1 2 3 4`; or
- ask in plain language, e.g. *"Regenerate the Lab 5 Q-learning report and summarize it."*
  Claude loads the skill automatically from its description.

The skill runs the tests, generates the reports, reads `report.md`, and summarizes the
best configuration and the effect of living reward, gamma, alpha and epsilon. It is
not allowed to give the learner simulator internals or to edit the Lab 4 strategy folders.

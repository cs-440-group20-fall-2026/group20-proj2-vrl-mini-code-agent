---
name: vacuum-rl-validator
description: Validates the vacuum robot Q-learning implementation, experiment parameters, and test coverage. Use before generating reinforcement learning reports or when checking experiment correctness.
---

# Vacuum RL Validator

Validate the Lab 5 implementation without changing code.

## Procedure

1. Inspect `lab_5/q_learning.py` and `lab_5/run_experiments.py`.
2. Confirm that:
   - Learning rate alpha is between 0 and 1.
   - Discount factor gamma is between 0 and 1.
   - Epsilon is between 0 and 1.
   - Terminal Q-learning updates do not bootstrap.
   - The learner uses only reset() and step().
   - Experiments use reproducible random seeds.
3. Run:

   `python -m unittest discover -s lab_5/tests -v`

4. Summarize passing tests, failures, and risks.
5. Do not modify files unless explicitly requested.

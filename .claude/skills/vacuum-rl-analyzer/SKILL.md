---
name: vacuum-rl-analyzer
description: Analyzes existing vacuum robot Q-learning experiment reports to compare living rewards, gamma, alpha, and epsilon. Use when interpreting results, identifying the best configuration, or explaining reinforcement learning tradeoffs.
---

# Vacuum RL Analyzer

Analyze existing results without retraining.

## Procedure

1. Read `lab_5/reports/experiments.csv` or locate the generated CSV report.
2. Compare configurations using:
   - Charger success rate
   - Trap rate
   - Mean episode reward
   - Mean steps
3. Identify the best configuration for charger success, using trap rate and mean reward as secondary criteria.
4. Explain how changes in living reward, gamma, alpha, and epsilon relate to observed performance.
5. Distinguish observed results from theoretical expectations.
6. Do not invent results or rerun experiments.

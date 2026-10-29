# Vacuum Robot RL Lab - Context Engineering Strategies 1 and 4

CS440 Fall 2026. One repository demonstrates **Strategy 1: Write (Persistent Memory Architecture)** and **Strategy 4: Isolation via Sub-Agents**, using the course's Agentir AI Context Engineering lecture.

## Scope
A 4x4 vacuum robot environment with start `(0,0)`, obstacle `(1,1)`, trap `(3,1)`, and charging station `(3,3)`. The simulator privately holds its transition and reward mechanics; a future learning agent will receive only action feedback. **Q-learning is not implemented in this lab.**

## Structure
```
CLAUDE.md
.claude/context/
.claude/agents/
strategy_1/README.md
strategy_4/README.md
vacuum/environment.py
scripts/demo.py
tests/test_environment.py
docs/environment_specification.md
repository_links.txt
```

## Run
Python 3.10+; no third-party dependencies.

```bash
python -m unittest discover -s tests -v
python -m scripts.demo
```

## Context strategy demonstrations
1. Strategy 1: Open the repository in Claude Code and ask it to review the environment while following `CLAUDE.md` and the focused context file.
2. Strategy 4: Ask the orchestrator to delegate environmnet and test reviews to the two `.claude/agents/` specialists. See `strategy_4/README.md` for the exact prompt.

## Important distinction
The lab states T and R are unknown **to the agent**, not that a runnable simulator can operate without internal rules. This example uses a clearly labeled assumed stochastic model, documented in `docs/environment_specifications.md`. No agent is given the transition or reward tables.

## Submission
Submit the `group_20.txt`, this `README.md`, and a video link to Canvas for Lab 4.

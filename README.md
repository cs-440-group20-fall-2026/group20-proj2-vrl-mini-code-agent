# Vacuum Robot RL Lab - Context Engineering Strategies 1 and 4

CS440 Fall 2026, Group 20. One repository demonstrates **Strategy 1: Write (Persistent Memory Architecture)** and **Strategy 4: Isolation via Sub-Agents**, based on the course's Agentic AI Context Engineering lecture.

## Scope
A 4x4 vacuum robot environment with start `(0,0)`, obstacle `(1,1)`, trap `(3,1)`, and charging station `(3,3)`. The simulator privately holds its transition and reward mechanics; a future learning agent will receive only action feedback. **Q-learning is not implemented in this lab.**

## Structure
```
.
├── CLAUDE.md                       # root project memory (shared rules)
├── .claude/
│   ├── context/                    # focused context: environment.md, testing.md
│   └── agents/                     # environment-reviewer, test-reviewer
├── vacuum/                         # shared simulator package
│   ├── __init__.py
│   └── environment.py
├── scripts/demo.py                 # scripted demo (not Q-learning)
├── tests/test_environment.py       # simulator tests
├── docs/environment_specification.md
├── strategy_1/                     # Strategy 1: persistent memory
│   ├── CLAUDE.md
│   ├── README.md
│   ├── context/                    # environment.md, testing.md
│   └── testing/                    # baseline_test, performance_benchmark, test_performance
├── strategy_4/                     # Strategy 4: sub-agent isolation
│   ├── CLAUDE.md
│   ├── README.md
│   ├── orchestrator.py             # runs reviewers and research pipeline
│   ├── context/                    # environment.md, testing.md
│   ├── .claude/
│   │   ├── constraints.md          # rules every agent reads first
│   │   ├── settings.json
│   │   └── agents/                 # reviewers, researcher, research-implementer,
│   │                               # research-verifier, report.schema.json
│   └── tests/                      # test_ground_truth, test_orchestrator
├── Instructions.md                 # lab assignment
├── group_20.txt                    # repository links for submission
└── requirements.txt                # no third-party dependencies
```

## Run
Python 3.10+; no third-party dependencies. From the repository root:

```bash
python -m unittest discover -s tests -v                       # simulator tests
python -m unittest discover -s strategy_1/testing -p "*.py"   # strategy 1 baseline/performance
python -m scripts.demo                                        # scripted demo
```

Strategy 4 runs from `strategy_4/` and needs the root on the import path for `vacuum`:

```bash
cd strategy_4
PYTHONPATH=.. python -m unittest discover -s tests
python orchestrator.py                       # run the reviewers
python orchestrator.py pipeline "question"   # researcher -> implementer -> verifier
```

## Context strategy demonstrations
1. **Strategy 1:** Open the repository in Claude Code and ask it to review the environment while following `CLAUDE.md` and the focused context file. See `strategy_1/README.md`.
2. **Strategy 4:** Launch Claude Code from `strategy_4/` and ask the orchestrator to delegate environment and test reviews to the `.claude/agents/` specialists. See `strategy_4/README.md` for the exact prompt and pipeline gates.

## Important distinction
The lab states T and R are unknown **to the agent**, not that a runnable simulator can operate without internal rules. This example uses a clearly labeled assumed stochastic model, documented in `docs/environment_specification.md`. No agent is given the transition or reward tables.

## Submission
Submit `group_20.txt`, this `README.md`, and a video link to Canvas for Lab 4.

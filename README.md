# Vacuum Robot RL Lab - Context Engineering Strategies 1 and 4

CS440 Fall 2026, Group 20. One repository demonstrates **Strategy 1: Write (Persistent Memory Architecture)** and **Strategy 4: Isolation via Sub-Agents**, based on the course's Agentic AI Context Engineering lecture.

## Scope
A 4x4 vacuum robot environment with start `(0,0)`, obstacle `(1,1)`, trap `(3,1)`, and charging station `(3,3)`. The simulator privately holds its transition and reward mechanics; a future learning agent will receive only action feedback. **Q-learning is not part of the Lab 4 deliverables;** Lab 5 adds it in `lab_5/` (see `lab_5/README.md`).

## Structure
```
.
├── CLAUDE.md                       # root project memory (shared rules)
├── .claude/
│   ├── context/                    # focused context: environment.md, testing.md
│   ├── agents/                     # environment-reviewer, test-reviewer
│   └── skills/vacuum-rl-report/    # Lab 5 skill: run + summarize Q-learning reports
│   └── hooks.json                  # Claude Code event hooks 
├── vacuum/                         # shared simulator package
│   ├── __init__.py
│   └── environment.py
├── scripts/
│   ├── demo.py                     # scripted demo (not Q-learning)
│   └── evaluate_mdp_hook.py        # MDP telemetry hook script
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
│   └── tests/                      # test_ground_truth, test_orchestrator, test_research
├── lab_5/                          # Lab 5: tabular Q-learning
│   ├── q_learning.py               # agent, train/evaluate (reset()/step() only)
│   ├── run_experiments.py          # grid runner, CSV + Markdown reports
│   ├── reports/                    # generated results.csv, report.md
│   └── tests/                      # test_q_learning, test_reports
├── Instructions.md                 # lab assignment
├── group_20.txt                    # repository links for submission
└── requirements.txt                # no third-party dependencies
```

## Run
Python 3.10+; no third-party dependencies. From the repository root:

```bash
python -m unittest discover -s tests -v                       # simulator tests
python -m unittest discover -s strategy_1/testing -p "*.py"   # strategy 1 baseline/performance
python scripts/evaluate_mdp_hook.py                           # test MDP evaluation hook directly
python -m scripts.demo                                        # scripted demo
python -m unittest discover -s lab_5/tests -t . -v            # Lab 5 Q-learning tests
python -m lab_5.run_experiments                               # Lab 5 reports -> lab_5/reports/
```

In Claude Code, `/vacuum-rl-report` runs the Lab 5 tests and experiments and summarizes the report (see `lab_5/README.md`).

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
The lab states T and R are unknown **to the agent**, not that a runnable simulator can operate without internal rules. This example uses a clearly labeled assumed stochastic model, documented in `docs/environment_specification.md`. No agent is given the transition or reward tables; the Lab 5 learner uses only `reset()` and `step()`.

## Code Feature Implementation: Hooks (Group 20 - Individual Contribution)
We implemented a `PostToolUse` event hook located in `.claude/hooks.json` that triggers `scripts/evaluate_mdp_hook.py`.

### MDP Hyperparameters Tracked:
- **Living Reward ($R_{live}$):** `-0.05`
- **Discount Factor ($\gamma$):** `0.95`
- **Learning Rate ($\alpha$):** `0.10`
- **Epsilon ($\epsilon$):** `0.10`

### How to Verify:
```powershell
echo '{"tool_name": "Bash"}' | python scripts/evaluate_mdp_hook.py
(On Unix/macOS: echo '{"tool_name": "Bash"}' | PYTHONPATH=. python3 scripts/evaluate_mdp_hook.py)

## Submission
Submit `group_20.txt`, this `README.md`, and a video link to Canvas for Lab 4. Lab 5 deliverables are in `lab_5/`.

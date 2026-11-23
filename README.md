# Vacuum Robot RL Lab - Context Engineering, Q-Learning, and Agent Skills

CS440 Fall 2026, Group 20. This repository holds three assignments built on the same 4x4 vacuum robot environment:

| Assignment | Folder | What it is |
|---|---|---|
| Lab 4 | `strategy_1/`, `strategy_4/` | **Strategy 1: Write (Persistent Memory Architecture)** and **Strategy 4: Isolation via Sub-Agents**, from the course's Agentic AI Context Engineering lecture |
| Lab 5 | `lab_5/` | Model-free tabular Q-learning (see `lab_5/README.md`) |
| **Project 2** | **`mini-coding-agent/`** | An **Agent Skills component** for [`rasbt/mini-coding-agent`](https://github.com/rasbt/mini-coding-agent). The agent uses the Lab 5 skill to solve Lab 4. See **[`mini-coding-agent/README.md`](mini-coding-agent/README.md)** |

## Project 2 at a glance
- **Component:** `mini-coding-agent/skills.py` finds folder skills (`skills/<name>/skill.md` and `.claude/skills/<name>/SKILL.md`). It scores every prompt against each skill and runs the best match when it reaches the 0.30 threshold. The agent can also load a skill itself mid-task with the `load_skill` tool.
- **Audit log:** every check is written to `mini-coding-agent/agent_skills.log`: the prompt, the similarity scores, and the executed skill. `verify_skills_log.py` checks the log against the spec.
- **Result:** in a live run on a local Ollama model (`qwen3.5:4b`), the agent triggered the Lab 5 skill `vacuum-rl-report`. It ran the Lab 5 tests and experiments and reported the best configuration: living reward -0.04, gamma 0.99, alpha 0.1, epsilon 0.3, with 100.0% charger success and 0.0% trap rate.
- **SDLC:** `intent.md` → `spec.md` → `plan.md` → code and tests (59 unit tests) → `test-report.md`.

## Scope
A 4x4 vacuum robot environment with start `(0,0)`, obstacle `(1,1)`, trap `(3,1)`, and charging station `(3,3)`. The simulator privately holds its transition and reward mechanics; a future learning agent will receive only action feedback. **Q-learning is not part of the Lab 4 deliverables;** Lab 5 adds it in `lab_5/` (see `lab_5/README.md`).

## Structure
```
.
├── CLAUDE.md                       # root project memory (shared rules)
├── .claude/
│   ├── context/                    # focused context: environment.md, testing.md
│   ├── agents/                     # environment-reviewer, test-reviewer
│   ├── skills/                     # Lab 5 skills: vacuum-rl-report (used by Project 2),
│   │                               # vacuum-rl-analyzer, vacuum-rl-validator
│   └── hooks.json                  # Claude Code event hooks
├── mini-coding-agent/              # Project 2: agent + Agent Skills component
│   ├── intent.md, spec.md, plan.md, test-report.md   # SDLC stages
│   ├── mini_coding_agent.py        # vendored upstream agent + skills hooks
│   ├── skills.py                   # Agent Skills component
│   ├── verify_skills_log.py        # audit log checker
│   ├── skills/pr-review/skill.md   # agent-local skill
│   ├── agent_skills.log            # live-run audit log
│   └── tests/                      # test_skills, test_verify_skills_log
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
python -m unittest discover -s mini-coding-agent/tests -v     # Project 2 skills component tests
python mini-coding-agent/verify_skills_log.py                 # Project 2 audit log check
```

To run the Project 2 agent live, you need Ollama with an 8,192-token context. See `mini-coding-agent/README.md` and `mini-coding-agent/test-report.md` §7.

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

## Code Feature Implementation: Hooks
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
```

## Video Presentations (Group 20)
- Lab 4: https://drive.google.com/file/d/1Osd5g_S4EvvsdKJquhdupRjLKOM8RzhG/view?usp=sharing
- Project 2: the private link is submitted on Canvas only, because this repository is public

## Submission
- **Project 2:** submit `group_20.txt` to Canvas, with the private video link added to that copy only. Also submit `mini-coding-agent/README.md` and the video.
- **Lab 4:** submitted earlier from the `vacuum-rl-context-engineering` repository. Lab 5 deliverables are in `lab_5/`.



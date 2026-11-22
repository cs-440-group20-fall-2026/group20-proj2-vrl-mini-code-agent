# Mini Coding Agent with Agent Skills Component — Vacuum RL (CS440 Group 20)

This repository extends [`rasbt/mini-coding-agent`](https://github.com/rasbt/mini-coding-agent) with a custom **Agent Skills Component** (`skills.py`) and applies our **Lab 5 Tabular Q-Learning skill** to solve and verify **Lab 4 Vacuum Robot RL** tasks.

## Architecture Overview
Building on the six core components of `mini-coding-agent` (live repo context, stable prompt prefix, structured tools with approval gates, context reduction, durable transcripts/memory, and bounded sub-agents), we added a seventh component:
- **Skill Discovery (`SkillManager`):** Scans `skills/*/skill.md` at startup to register modular domain skills.
- **Dual Triggering:**
  1. **Prompt Similarity Trigger:** Evaluates every incoming user prompt against registered skills using similarity scoring (`compute_similarity`) and injects matching `skill.md` instructions automatically.
  2. **Mid-Execution Trigger (`load_skill` tool):** Allows the coding agent to request and execute a specific `skill.md` during its multi-step tool loop when a subtask requires specialized guidance.
- **Audit Logging (`agent_skills.log`):** Logs every prompt, similarity check score across skills, and executed skill in structured JSON format.

## Repository Structure
```text
.
├── intent.md                           # SDLC Stage 1: Project intent & objectives
├── spec.md                             # SDLC Stage 2: Functional & logging specifications
├── plan.md                             # SDLC Stage 3: Phased implementation & test plan
├── skills.py                           # Agent Skills Component (discovery, similarity, logging)
├── mini_coding_agent.py                # Mini coding agent integrated with SkillManager
├── agent_skills.log                    # Audit log of prompts, similarity checks, and executed skills
├── group_20.txt                        # Canvas submission file (repo & private video links)
├── skills/
│   └── vacuum-rl-optimizer/
│       └── skill.md                    # Lab 5 Q-learning skill instructions applied to Lab 4
├── vacuum/                             # Shared 4x4 vacuum environment simulator (Lab 4)
│   ├── __init__.py
│   └── environment.py
├── strategy_1/                         # Lab 4 Context Engineering Strategy 1 (Persistent Memory)
├── strategy_4/                         # Lab 4 Context Engineering Strategy 4 (Sub-agent Isolation)
├── lab_5/                              # Lab 5 Model-Free Tabular Q-Learning
│   ├── q_learning.py                   # QLearningAgent (interacts via reset()/step() only)
│   ├── run_experiments.py              # Hyperparameter grid runner & CSV/Markdown report generator
│   ├── reports/                        # Generated results.csv and report.md
│   └── tests/                          # Unit tests for Q-learning and report generation
├── scripts/
│   ├── demo.py                         # Scripted baseline demo
│   └── evaluate_mdp_hook.py            # MDP telemetry hook
└── tests/
    └── test_environment.py             # Simulator unit tests

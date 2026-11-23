# Project 2: Mini Coding Agent with Agent Skills Component (CS440 Group 20)

Project 2 extends [`rasbt/mini-coding-agent`](https://github.com/rasbt/mini-coding-agent) with a seventh architectural component, **Agent Skills**. The agent finds folder-based skills (for example `skills/pr-review/skill.md`) and runs a skill's instructions in two cases: when a user prompt matches the skill, or when the agent asks for the skill partway through a task. To demonstrate it, the agent uses our **Lab 5 Q-learning skill** to solve the **Lab 4 vacuum robot** task.

## Assignment requirements
| # | Requirement | Where it is addressed |
|---|---|---|
| R1 | Add an Agent Skills component to the mini coding agent | `mini-coding-agent/skills.py` |
| R2 | Find folder skills (`<skills dir>/<name>/skill.md`) | `SkillManager.discover()` |
| R3 | Run a skill when a prompt matches it **or** when the agent needs it mid-task | `match_and_trigger()` in `MiniAgent.ask()` + `load_skill` tool |
| R4 | Use the Lab 5 skill to solve Lab 4 | `.claude/skills/vacuum-rl-report/SKILL.md`, run against `vacuum/` + `lab_5/` (live run *planned*) |
| R5 | Log the prompt, the similarity check, and the executed skill | `SkillManager.log()` → `mini-coding-agent/agent_skills.log`, checked by `verify_skills_log.py` |
| R6 | Follow an SDLC with one document per stage | `intent.md` → `spec.md` → `plan.md` (done) |

## Architecture overview
The six core components of `mini-coding-agent` stay as they are: live repo context, a stable prompt prefix, structured tools with approval gates, context reduction, durable transcripts and memory, and bounded sub-agents. We add a seventh:

- **Skill discovery (`SkillManager`):** at startup, scans `.claude/skills/`, `mini-coding-agent/skills/`, `skills/`, and `skill/` for `*/skill.md` and `*/SKILL.md`, then registers each skill's name, description, and instructions.
- **Two triggers:**
  1. **Prompt similarity:** each user prompt is scored against every registered skill (`compute_similarity`, an IDF-weighted word overlap; see `spec.md` FR-2). If the best score meets the threshold (0.30), that skill's instructions are added to the turn.
  2. **Mid-task request (`load_skill` tool):** the model can call a skill by name from inside its tool loop when a subtask needs it.
- **Audit log (`agent_skills.log`):** one JSON line per check, recording the timestamp, trigger type, prompt, score for every skill, best skill and threshold, and the executed skill and its path.
- **Log verification (`verify_skills_log.py`):** checks every log line against spec FR-4. It confirms the fields are present, scores are in [0, 1], the best skill really has the top score, and a skill ran exactly when the rules say it should. It also confirms that each `skill_path` exists. `--selfcheck` writes and verifies a log offline, without Ollama.

## Repository structure
Items marked *(planned)* do not exist yet. Everything else is in the repository now.

```text
.
├── CLAUDE.md                           # Project memory (shared rules for Claude Code)
├── README.md                           # Lab 4 / Lab 5 overview
├── Instructions.md                     # Lab 4 assignment text
├── group_20.txt                        # Canvas submission links
├── requirements.txt                    # No third-party dependencies
├── .gitignore                          # also ignores .mini-coding-agent/ (agent session files)
├── .claude/
│   ├── agents/                         # environment-reviewer.md, test-reviewer.md
│   ├── context/                        # environment.md, testing.md
│   ├── hooks.json                      # PostToolUse hook -> scripts/evaluate_mdp_hook.py
│   └── skills/
│       ├── vacuum-rl-report/SKILL.md   # Lab 5 skill: test, train, report (used to solve Lab 4)
│       ├── vacuum-rl-analyzer/SKILL.md # Lab 5 skill: compare hyperparameter results
│       └── vacuum-rl-validator/SKILL.md# Lab 5 skill: validate implementation and tests
├── mini-coding-agent/                  # ── Project 2 ──
│   ├── README.md                       # This file
│   ├── intent.md                       # SDLC stage 1: problem, goal, success criteria
│   ├── spec.md                         # SDLC stage 2: functional and logging requirements
│   ├── plan.md                         # SDLC stage 3: phased implementation and test plan
│   ├── mini_coding_agent.py            # Upstream agent (commit 717cae4) + [Agent Skills] hooks
│   ├── LICENSE-mini-coding-agent       # Upstream Apache-2.0 license
│   ├── skills.py                       # Agent Skills component (discovery, similarity, triggers, log)
│   ├── verify_skills_log.py            # Checks agent_skills.log against spec FR-4; --selfcheck mode
│   ├── skills/                         # Agent-local folder skills
│   │   └── pr-review/skill.md          # Unrelated skill; shows the vacuum skills are skipped off-topic
│   ├── tests/
│   │   ├── test_skills.py              # discovery, similarity, triggers, log, agent loop
│   │   └── test_verify_skills_log.py   # verifier: valid logs pass, tampered records fail
│   ├── agent_skills.log                # (planned) audit log from the Lab 4 demo run
│   └── test-report.md                  # (planned) SDLC stage 5: verification results
├── vacuum/                             # Lab 4 shared 4x4 simulator
│   ├── __init__.py
│   └── environment.py
├── docs/environment_specification.md   # Assumed stochastic model (hidden from agents)
├── scripts/
│   ├── demo.py                         # Scripted baseline (not Q-learning)
│   └── evaluate_mdp_hook.py            # MDP telemetry hook
├── tests/test_environment.py           # Simulator tests
├── strategy_1/                         # Lab 4 context strategy 1: persistent memory
│   ├── CLAUDE.md, README.md
│   ├── context/                        # environment.md, testing.md
│   └── testing/                        # baseline_test, performance_benchmark, test_performance
├── strategy_4/                         # Lab 4 context strategy 4: sub-agent isolation
│   ├── CLAUDE.md, README.md, orchestrator.py
│   ├── context/                        # environment.md, testing.md, research/
│   ├── .claude/                        # constraints.md, settings.json, agents/
│   └── tests/                          # test_ground_truth, test_orchestrator, test_research
└── lab_5/                              # Lab 5 model-free tabular Q-learning
    ├── README.md
    ├── q_learning.py                   # QLearningAgent (reset()/step() only)
    ├── run_experiments.py              # Hyperparameter grid -> CSV + Markdown
    ├── reports/                        # results.csv, report.md
    └── tests/                          # test_q_learning, test_reports
```

## Project status
| SDLC stage | Artifact | Status |
|---|---|---|
| 1. Intent | `intent.md` | Done |
| 2. Specification | `spec.md` | Done |
| 3. Plan | `plan.md` | Done |
| 4. Implementation | `skills.py`, `verify_skills_log.py`, `mini_coding_agent.py`, `skills/pr-review/`, `tests/` | Done |
| 5. Verification | `agent_skills.log`, `test-report.md`, full test run | Not started |
| 6. Delivery | `group_20.txt`, video | Not started (`group_20.txt` still points to the Lab 4 repo) |

All suites currently pass: `mini-coding-agent/tests/` (52), `tests/` (7), `lab_5/tests/`, `strategy_4/tests/` (35), and `strategy_1/testing/`.

## Run
Python 3.10+, standard library only. The agent uses a local Ollama model, as upstream does. The unit tests use upstream's `FakeModelClient`, so they don't need Ollama. Skill flags: `--skills-dir DIR` (repeatable), `--skills-log PATH`, `--skill-threshold 0.30`, and `--no-skills`. Inside the agent, `/skills` lists the discovered skills and the active one.

```bash
# Unit tests for the skills component
python -m unittest discover -s mini-coding-agent/tests -v

# Launch the agent with the repository root as its workspace
python mini-coding-agent/mini_coding_agent.py --cwd . --approval ask

# Example prompt that should trigger the Lab 5 skill
> Use Q-learning to train the vacuum robot to reach the charger in the Lab 4 grid and report the best configuration.
```

Every prompt adds a line to `mini-coding-agent/agent_skills.log`. The example below shows real scores for this prompt against the four current skills, with `matched_terms` shortened:

```json
{"timestamp": "...", "trigger_type": "prompt_similarity", "prompt": "Use Q-learning to train the vacuum robot ...",
 "similarity_check": {"scores": {"vacuum-rl-analyzer": 0.4451, "vacuum-rl-report": 0.5561, "vacuum-rl-validator": 0.2231, "pr-review": 0.0478},
 "matched_terms": {"vacuum-rl-report": ["charger", "lab", "qlearn", "report", "robot", "train", "vacuum"], "...": []},
 "best_skill": "vacuum-rl-report", "best_score": 0.5561, "threshold": 0.3},
 "executed_skill": "vacuum-rl-report", "skill_path": ".claude/skills/vacuum-rl-report/SKILL.md"}
```

### Verifying the log
```bash
python mini-coding-agent/verify_skills_log.py              # check mini-coding-agent/agent_skills.log
python mini-coding-agent/verify_skills_log.py --selfcheck  # offline: real SkillManager, fixed prompts, temp log
```
Exit status: `0` the log is valid, `1` problems were found (each listed with its line number), `2` there is no log or it's empty. Current `--selfcheck` output:

```text
line  trigger              best skill            score  executed             prompt
   1  prompt_similarity    vacuum-rl-report     0.5561  vacuum-rl-report     Use Q-learning to train the vacuum robot to rea...
   2  prompt_similarity    vacuum-rl-analyzer   0.8581  vacuum-rl-analyzer   Which living reward and gamma gave the best res...
   3  prompt_similarity    vacuum-rl-validator  0.7533  vacuum-rl-validator  Validate the Q-learning implementation and test...
   4  prompt_similarity    pr-review               1.0  pr-review            Review this pull request for bugs
   5  prompt_similarity    -                       0.0  -                    Write a binary search function in Python
   6  prompt_similarity    -                       0.0  -                    Fix the typo in README.md
   7  agent_mid_execution  vacuum-rl-report     0.4063  vacuum-rl-report     The Lab 4 task needs the Lab 5 Q-learning exper...
   8  agent_mid_execution  pr-review            0.3333  -                    Requesting a skill that does not exist
OK: every record has the required fields and is internally consistent.
```
Line 8 is the agent asking for a skill that doesn't exist. Nothing runs, even though `pr-review` has the top score: a mid-task request runs only the skill that was named.

## Constraints carried over from Lab 4 and Lab 5
- The learner talks to the simulator only through `env.reset()` and `env.step(action)`. Neither the agent nor the skill may read the transition or reward tables or any other simulator internals.
- Q-learning code stays in `lab_5/`. The skill runs that code; it does not reimplement it.
- No third-party Python dependencies.

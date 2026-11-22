# Intent: Agent Skills Component for `rasbt/mini-coding-agent`

## 1. Problem Statement
The `rasbt/mini-coding-agent` harness provides a lightweight local coding agent built around six core architectural components:
1. Live repository context collection (workspace snapshot, layout, instructions, git state)
2. Stable prompt shaping and prefix cache reuse
3. Structured tools with input validation and approval gates (`ask`, `auto`, `never`)
4. Context reduction and output clipping/deduplication
5. Durable JSON session transcripts and distilled working memory (`/memory`, `--resume`)
6. Bounded sub-agent delegation

However, it lacks an **Agent Skills Component** capable of discovering modular, folder-based skills (e.g., `skills/<skill-name>/skill.md`), matching user prompts or mid-execution task needs to relevant skill instructions, injecting those instructions into the agent's context, and maintaining an audit trail of skill activations.

## 2. Project Goal
Extend `mini_coding_agent.py` with a dedicated **Agent Skills Component** (`skills.py`) and apply it to our CS440 Vacuum Robot Reinforcement Learning domain:
- **Dynamic Skill Discovery:** Automatically detect folder-based skills (such as `skills/vacuum-rl-optimizer/skill.md` or `skills/pr-review/skill.md`).
- **Dual Triggering:** Trigger `skill.md` instructions both (a) when an incoming user prompt matches a skill via similarity checks, and (b) mid-execution when the coding agent explicitly invokes or needs a specific skill during a multi-step task.
- **Cross-Lab Integration (Lab 5 → Lab 4):** Use the tabular Q-learning skill created in Lab 5 (`lab_5/q_learning.py` and `lab_5/run_experiments.py`) to evaluate, optimize, and solve the 4x4 vacuum robot environment tasks from Lab 4 (`vacuum/`, `strategy_1/`, `strategy_4/`) without exposing hidden transition ($T$) or reward ($R$) tables.
- **Observability & Auditability:** Log every prompt, similarity check score, candidate comparison, and executed skill into `agent_skills.log`.

## 3. Success Criteria
- `SkillManager` discovers all valid `skills/*/skill.md` folders automatically at startup.
- Both prompt-level similarity matching and mid-execution tool/agent skill requests load the exact `skill.md` instructions.
- `agent_skills.log` records structured entries containing timestamp, user prompt/trigger source, similarity score(s), and executed skill name.
- The mini coding agent successfully applies the Lab 5 Q-learning skill to solve Lab 4 tasks while passing all unit tests (`tests/` and `lab_5/tests/`).

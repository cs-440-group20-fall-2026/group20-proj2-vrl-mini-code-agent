# Execution Plan: Agent Skills Component & Lab 4/5 Integration

All Project 2 code lives in `mini-coding-agent/`. The agent runs with the repository root as its workspace (`--cwd .`), so it can reach `vacuum/`, `lab_5/`, and `.claude/skills/`.

## Phase 1: SDLC & Repository Setup ✅
- **Deliverables:** `intent.md`, `spec.md`, `plan.md`
- **Tasks:**
  1. Write the SDLC documents in `mini-coding-agent/`.
  2. Use the existing Lab 5 skill, `.claude/skills/vacuum-rl-report/SKILL.md`, in place rather than a copy. Discovery covers `.claude/skills/` and accepts both `SKILL.md` and `skill.md`.

## Phase 2: Implement Agent Skills Component (`skills.py`) ✅
- **Deliverables:** `mini-coding-agent/skills.py`
- **Tasks:**
  1. `SkillManager.discover()`: register `<dir>/<name>/skill.md|SKILL.md` and parse the frontmatter.
  2. `compute_similarity(prompt, skill)`: IDF-weighted token coverage plus a skill-name phrase match.
  3. `match_and_trigger(prompt)`: prompt-level activation at threshold 0.30.
  4. `execute_skill_by_name(name, reason)`: mid-execution activation.
  5. JSON-lines audit log to `agent_skills.log` recording the prompt, the similarity check, and the executed skill (spec FR-4).

## Phase 3: Wire Component into `mini_coding_agent.py` ✅
- **Deliverables:** `mini-coding-agent/mini_coding_agent.py`, vendored from upstream commit `717cae4` with `LICENSE-mini-coding-agent`
- **Tasks:**
  1. Build a `SkillManager` in `build_agent()`, list the skills in the prompt prefix and the welcome banner, and add a `/skills` command.
  2. Run `match_and_trigger(user_input)` at the start of `ask()` and inject the instructions as an `Active skill` prompt section.
  3. Register the `load_skill` tool for mid-execution requests.
  4. Add CLI flags `--skills-dir`, `--skills-log`, `--skill-threshold`, and `--no-skills`.
  5. Write `mini-coding-agent/tests/test_skills.py`, covering discovery, similarity, the threshold boundary, both triggers, log fields, and agent integration through `FakeModelClient`.

## Phase 4: Second Skill (non-match evidence) ✅
- **Deliverables:** `mini-coding-agent/skills/pr-review/skill.md`
- **Tasks:** Add an unrelated skill so the log shows the similarity check choosing between unrelated skills and not triggering on off-topic prompts.

## Phase 5: Solve Lab 4 Using Lab 5 Skill & Verify
- **Deliverables:** `agent_skills.log`, `test-report.md`
- **Tasks:**
  1. With Ollama running (`qwen3.5:4b` by default), run `python mini-coding-agent/mini_coding_agent.py --cwd . --max-steps 10` and prompt it to solve Lab 4 with Q-learning.
  2. Confirm the log shows a `prompt_similarity` entry with `executed_skill: vacuum-rl-report`, and that the agent runs the skill's test and experiment commands. `run_shell` caps timeouts at 120 s, so the run may need `--quick`.
  3. Check the reported best configuration against `lab_5/reports/report.md`. Don't quote numbers the run did not produce.
  4. Run every suite: `mini-coding-agent/tests/`, `tests/`, `lab_5/tests/`, `strategy_1/testing/`, and `strategy_4/tests/`.
  5. Record the results in `test-report.md` (SDLC verification stage).

## Phase 6: Documentation & Canvas Submission
- **Deliverables:** `README.md` (root and `mini-coding-agent/`), `group_20.txt`, 3-minute group video
- **Tasks:**
  1. Keep the file tree and run commands in the READMEs accurate, and link Project 2 from the root README.
  2. Point `group_20.txt` at this repository and the private video URL.
  3. Record a ≤3-minute presentation with all 3 members on camera covering the SDLC documents, `skills.py`, a live run, and `agent_skills.log`.

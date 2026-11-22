# Execution Plan: Agent Skills Component & Lab 4/5 Integration

## Phase 1: SDLC & Repository Setup
- **Deliverables:** `intent.md`, `spec.md`, `plan.md`, `skills/vacuum-rl-optimizer/skill.md`
- **Tasks:**
  1. Establish SDLC tracking documents in the repository root.
  2. Create the `skills/` directory structure and port the Lab 5 Q-learning evaluation workflow into `skills/vacuum-rl-optimizer/skill.md`.

## Phase 2: Implement Agent Skills Component (`skills.py`)
- **Deliverables:** `skills.py`
- **Tasks:**
  1. Build `SkillManager` to recursively discover `skills/*/skill.md` files and store metadata + markdown instructions.
  2. Implement `compute_similarity(prompt, skill)` combining exact phrase checks, token Jaccard/overlap ratios, and keyword matching.
  3. Implement `match_and_trigger(prompt, threshold=0.3)` for automatic prompt-level activation.
  4. Implement `execute_skill_by_name(skill_name, reason)` so the coding agent can request a skill dynamically mid-execution.
  5. Configure JSON-line audit logging to `agent_skills.log` capturing every prompt, similarity check breakdown, and executed skill.

## Phase 3: Wire Component into `mini_coding_agent.py`
- **Deliverables:** Updated `mini_coding_agent.py`
- **Tasks:**
  1. Initialize `SkillManager` during workspace snapshot collection and list available skills in the system prompt summary.
  2. Run `skill_manager.match_and_trigger(user_input)` at the start of each user turn and inject matched `skill.md` instructions into the turn context.
  3. Register a `load_skill` tool in the agent's structured tool registry so the LLM can invoke a skill mid-execution when needed.

## Phase 4: Solve Lab 4 Using Lab 5 Skill & Verify Tests
- **Deliverables:** `agent_skills.log`, verified test suite outputs
- **Tasks:**
  1. Launch `mini_coding_agent.py` (with Ollama running `qwen3.5:4b`) and prompt it to solve/optimize Lab 4 vacuum navigation using the Lab 5 Q-learning skill.
  2. Verify the agent triggers `skills/vacuum-rl-optimizer/skill.md`, runs `lab_5.run_experiments` (confirming optimal configuration: `living_reward=-0.04, gamma=0.99, alpha=0.1, epsilon=0.3` achieving `100.0%` charger success and `0.0%` trap rate), and validates Lab 4 environment constraints.
  3. Run all unit tests (`tests/test_environment.py`, `lab_5/tests/test_q_learning.py`, `lab_5/tests/test_reports.py`, `strategy_1/testing/`, `strategy_4/tests/`).
  4. Inspect `agent_skills.log` to confirm prompts, similarity scores, and executed skills are logged accurately.

## Phase 5: Documentation & Canvas Submission
- **Deliverables:** `README.md`, `group_20.txt`, 3-minute group video
- **Tasks:**
  1. Document the complete file tree, component architecture, and CLI execution commands in `README.md`.
  2. Add repository links and the private video URL to `group_20.txt`.
  3. Record a ≤3-minute presentation with all 3 members on camera (professional background, equal speaking time) covering SDLC decisions, `skills.py` implementation, live execution, and `agent_skills.log`.

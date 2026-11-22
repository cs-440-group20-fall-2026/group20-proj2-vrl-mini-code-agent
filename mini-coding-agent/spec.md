# Specification: Agent Skills Component

## 1. System Architecture Integration
The Agent Skills Component (`skills.py`) plugs into `mini_coding_agent.py` alongside the existing six components without breaking standard library compatibility or Ollama `/api/generate` communication:
- **Workspace Snapshot & Prompt Prefix:** Discovered skill names and descriptions are registered in the workspace metadata so the model knows which skills exist without bloating the static prompt prefix.
- **Pre-Turn Prompt Hook:** Before sending a user turn to Ollama, `SkillManager.match_and_trigger(prompt)` computes similarity scores against registered skills and injects matched `skill.md` instructions into the turn state.
- **Mid-Execution Tool Hook:** A structured tool (`use_skill` / `load_skill`) allows the agent to request and execute a specific `skill.md` during its `<tool>...</tool>` reasoning loop when a subtask requires specialized domain instructions.

## 2. Functional Requirements

### FR-1: Folder Skill Discovery
- Scan `skills/` (and support `skill/` alias if present) for subdirectories containing a `skill.md` file.
- Parse each `skill.md` to extract its skill identifier (folder name), title/objective, keywords, and full markdown instructions.

### FR-2: Similarity Check & Thresholding
- Compute a normalized similarity score in $[0.0, 1.0]$ between the incoming prompt (or execution query) and each registered skill using token overlap, n-gram/phrase matching, and keyword weighting.
- Configurable confidence threshold (default `0.30`). If the highest-scoring skill meets or exceeds the threshold, select it for execution.

### FR-3: Instruction Execution & Context Injection
- When triggered by prompt similarity or mid-execution request, return the full `skill.md` instructions to the agent so it executes the workflow step-by-step using its structured tools (file read/edit, shell commands under approval gates).

### FR-4: Mandatory Audit Logging (`agent_skills.log`)
Every skill evaluation—whether triggered by a user prompt or invoked mid-execution—must append a structured log entry to `agent_skills.log` containing:
- `timestamp`: ISO-8601 timestamp
- `trigger_type`: `"prompt_similarity"` or `"agent_mid_execution"`
- `prompt`: The exact user prompt or agent query evaluated
- `similarity_check`: Dictionary of `{skill_name: score}` plus `best_skill`, `best_score`, and `threshold`
- `executed_skill`: Name of the triggered skill (or `null` if none met the threshold)
- `skill_path`: Relative path to the executed `skill.md` (or `null`)

### FR-5: Domain Constraints (Lab 5 Skill solving Lab 4)
- The `vacuum-rl-optimizer` skill instructs the agent to solve Lab 4's 4x4 grid (`Start (0,0)`, `Obstacle (1,1)`, `Trap (3,1) = -1`, `Charger (3,3) = +10`) using Lab 5's model-free tabular Q-learning (`lab_5/q_learning.py`, `lab_5/run_experiments.py`).
- Strict black-box boundary: the learner interacts only via `env.reset()` and `env.step(action)` and never reads internal transition ($T$) or reward ($R$) tables.

## 3. Non-Functional Requirements
- **Zero External Python Dependencies:** Uses only Python 3.10+ standard library (`pathlib`, `json`, `logging`, `re`, `datetime`, `difflib`) to match `rasbt/mini-coding-agent`.
- **Deterministic & Auditable:** All skill checks are persisted cleanly to `agent_skills.log` for inspection and grading.

# Specification: Agent Skills Component

## 1. System Architecture Integration
The Agent Skills Component (`mini-coding-agent/skills.py`) plugs into the vendored `mini-coding-agent/mini_coding_agent.py` alongside the six existing components. It keeps standard-library-only compatibility and the Ollama `/api/generate` client. Every change to the upstream file is marked `[Agent Skills]`.
- **Prompt prefix:** the names and descriptions of discovered skills are listed in a `Skills:` section of the static prefix. The full instructions are not included, so the prefix stays small and cache-stable.
- **Pre-turn prompt hook:** in `MiniAgent.ask()`, before the first model call, `SkillManager.match_and_trigger(prompt)` scores the prompt against every skill. A matching skill's instructions go into an `Active skill` prompt section.
- **Mid-execution tool hook:** a structured `load_skill(name, reason)` tool (safe, no approval needed) lets the model request a skill from inside its `<tool>...</tool>` loop.
- **Active skill persistence:** the active skill is stored in `session["active_skill"]`, outside the clipped transcript, so the model sees every step for the whole turn. It survives `--resume`, stays active through follow-up prompts that match no skill, and is cleared by `/reset`.

## 2. Functional Requirements

### FR-1: Folder Skill Discovery
- Scan these directories, relative to the workspace root, in order: `.claude/skills/`, `mini-coding-agent/skills/`, `skills/`, `skill/`. Then scan the agent's own `skills/` folder and any `--skills-dir` arguments.
- A skill is a subfolder containing `skill.md` or `SKILL.md`. Folders without one, and directories that don't exist, are ignored.
- Read optional `---` frontmatter: `name` (default: the folder name), `description` (default: the first body paragraph), and `keywords` (comma list). The frontmatter is removed from the instructions.
- If two skills have the same name, the first directory in scan order wins.

### FR-2: Similarity Check & Thresholding
- Tokenize the prompt: lowercase, drop stopwords and one-character tokens, apply light suffix stemming, and normalize `Q-learning`/`q learning` to one token.
- A skill's vocabulary is the tokens of its name, description, and keywords.
- **Score** = the IDF-weighted share of the prompt's tokens that appear in the skill's vocabulary. IDF is computed across all registered skills as `ln(1 + N / df)`. Words that every skill shares (such as *vacuum*) count less than words distinctive to one skill (such as *train*). The score is in [0.0, 1.0].
- **Phrase match:** if the prompt contains the skill's name, either `vacuum-rl-report` or `vacuum rl report`, the score is 0.95.
- **Threshold:** the default is `0.30` and can be changed with `--skill-threshold`. The highest-scoring skill is executed if its score is greater than or equal to the threshold. Ties go to the alphabetically first name. If every score is 0, `best_skill` is `null`.

### FR-3: Instruction Execution & Context Injection
- When a skill is triggered, by prompt similarity or by `load_skill`, its rendered instructions (header, path, and body, with `$ARGUMENTS` blanked) are placed in the `Active skill` section of every model prompt for the rest of the turn.
- The agent carries out the steps with its existing tools, under the existing approval gates. Skills never bypass `run_shell` or `write_file` approval.
- An unknown skill name in `load_skill` returns a tool error that lists the available skills.

### FR-4: Mandatory Audit Logging (`agent_skills.log`)
Every evaluation, whether or not a skill runs, appends one JSON line to `mini-coding-agent/agent_skills.log` (configurable with `--skills-log`):
- `timestamp`: ISO-8601 UTC
- `trigger_type`: `"prompt_similarity"` or `"agent_mid_execution"`
- `prompt`: the user prompt, or the agent's `reason` for a mid-execution request
- `similarity_check`: `{scores: {skill: score}, matched_terms: {skill: [tokens]}, best_skill, best_score, threshold}`
- `executed_skill`: the triggered skill's name, or `null`
- `skill_path`: the workspace-relative path to its `skill.md`, or `null`
- `requested_skill`: only for mid-execution requests; the name the agent asked for

**Verification (`verify_skills_log.py`).** A log is valid when every line is a JSON object with the fields above and these rules hold:
- `timestamp` parses as ISO-8601, and every score and the `threshold` are numbers in [0, 1].
- `best_score` is the highest score, and `best_skill` has it. If all scores are 0, both are `null`/0.
- Prompt trigger: `executed_skill` is `best_skill` when `best_score ≥ threshold`, otherwise `null`.
- Mid-execution trigger: `executed_skill` is `requested_skill` if that skill exists, otherwise `null`.
- `skill_path` is set exactly when `executed_skill` is, and points to an existing file under the workspace root.

### FR-1 parsing details
- Skill files are read as UTF-8 with an optional BOM. `keywords` may be a comma list, an inline `[a, b]` list, or a YAML block list (`- item`).
- A skill-name phrase match must sit on word boundaries, so `pr review` doesn't match inside `appr reviewer`.

### FR-5: Domain Constraints (Lab 5 Skill solving Lab 4)
- The skill used is the actual Lab 5 skill, `.claude/skills/vacuum-rl-report/SKILL.md`, which is discovered in place without being copied. It instructs the agent to run the Lab 5 tests and `python -m lab_5.run_experiments`, then summarize charger success, trap rate, mean reward, and mean steps on the Lab 4 grid (start `(0,0)`, obstacle `(1,1)`, trap `(3,1) = -1`, charger `(3,3) = +10`).
- Strict black-box boundary: the learner uses only `env.reset()` and `env.step(action)` and never reads the hidden transition ($T$) or reward ($R$) tables.

## 3. Non-Functional Requirements
- **No external Python dependencies:** Python 3.10+ standard library only (`pathlib`, `json`, `math`, `re`, `datetime`). Tests use `unittest`.
- **Deterministic & auditable:** the same prompt always gives the same scores. Tests inject a fixed clock and write logs to temporary directories.
- **Upstream-compatible:** with `--no-skills`, or with no skills found, the agent behaves like upstream: no `load_skill` tool, no `Skills:` section, no log writes.

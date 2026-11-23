# Test Report: Agent Skills Component (SDLC Stage 5: Verification)

This report checks the Agent Skills component against `spec.md`. It covers the unit tests and three live runs of the agent on a local Ollama model, before and after fixes. In the main run, the agent solves Lab 4 with the Lab 5 skill.

**Result:** every requirement is met. After four fixes to the vendored agent (§4), the live agent solved Lab 4 with the Lab 5 skill. Its reported best configuration matches the committed report exactly, and the live `agent_skills.log` passes verification.

## 1. Environment
| Item | Value |
|---|---|
| Date | 2026-11-22 |
| Code | branch `project-2/skills-log-verification` (base `8150d19`, plus the fixes in §4) |
| OS / Python | Windows 10 Home 19045, Python 3.11 |
| Model server | Ollama 0.40.17, model `qwen3.5:4b`, 100% GPU (RTX 3070 Laptop, 8 GB, NVIDIA driver 621.24) |
| Context window | 8,192 tokens. The default 4,096 is too small: the first agent prompt is 2,174 tokens and later prompts can reach about 7,000 |
| Agent flags | `--cwd . --model qwen3.5:4b --max-new-tokens 600 --ollama-timeout 300` |

## 2. Requirements traceability
| Spec | Requirement | Evidence | Result |
|---|---|---|---|
| FR-1 | Find `skills/<name>/skill.md` (and `.claude/skills/*/SKILL.md`) | Unit tests `DiscoveryTests`; the live banner lists all 4 skills | ✅ |
| FR-2 | Similarity check with a 0.30 threshold | `SimilarityTests`, `test_threshold_boundary`; live log lines 1–3 and 5 | ✅ |
| FR-3 | Run the skill's instructions: prompt trigger and mid-execution trigger | Run A followed `vacuum-rl-report`; Run C loaded `vacuum-rl-validator` with `load_skill` and ran its command | ✅ |
| FR-4 | Log the prompt, the similarity check, and the executed skill | Live `agent_skills.log`, 6 records, verifier exit 0 (§5) | ✅ |
| FR-5 | The Lab 5 skill solves Lab 4 through `reset()`/`step()` only | Run A ran `lab_5` tests and experiments; its answer matches `lab_5/reports/report.md` | ✅ |
| NFR | Standard library only; deterministic | No third-party imports; the experiment rerun reproduced the committed reports byte for byte | ✅ |

## 3. Unit tests
```bash
python -m unittest discover -s mini-coding-agent/tests -v   # 59 tests, OK
python -m unittest discover -s tests                        # OK (Lab 4 simulator)
python -m unittest discover -s lab_5/tests -t .             # OK (Lab 5 Q-learning)
cd strategy_4 && PYTHONPATH=.. python -m unittest discover -s tests   # OK
```
| Suite | Tests | Covers |
|---|---|---|
| `test_skills.py` | 42 | discovery and frontmatter parsing, similarity, threshold, both triggers, log fields, the agent loop through `FakeModelClient`, live-run regressions |
| `test_verify_skills_log.py` | 17 | valid logs pass; each kind of tampered record fails with the right message |

The upstream pytest suite was not run, because pytest isn't a project dependency.

## 4. Live runs

### 4.1 First run: found four defects
The agent picked the right skill, but **Run A never produced an answer**.

The agent ran the Lab 5 tests, then read `lab_5/reports/report.md` seven times until it reached the 10-step limit. Causes and fixes (marked `[Group 20 fix]` in `mini_coding_agent.py`):

| # | Defect | Cause | Fix | Regression test |
|---|---|---|---|---|
| 1 | Read loop, no final answer | The upstream transcript cut every recent tool result to 900 characters. The report's "Best configuration" section starts at character 3,669 of the `read_file` output, so the model never saw it. The final transcript cut also dropped the *newest* text | Keep the newest tool result whole (≤ 4,000 chars) and keep the newest end of an over-long transcript | `test_latest_read_of_report_shows_best_configuration`, `test_long_transcript_keeps_newest_items`, `test_older_tool_output_is_still_clipped` |
| 2 | `UnicodeEncodeError` crash (Run B) | Windows redirected stdout is cp1252, and the model wrote "log₂" | Switch stdout/stderr to UTF-8 at startup | `test_main_switches_stdout_to_utf8` |
| 3 | Wasted steps reloading the active skill | The model called `load_skill` on the skill that was already active, and each call re-logged it | Reloading the active skill returns "already active, do the next step" and logs nothing | `test_reloading_active_skill_is_a_no_op` |
| 4 | Tool calls with empty arguments | The upstream XML parser ignored `<name>`, `<reason>`, `<start>`, `<end>`, `<timeout>` tags | Parse those tags too | `test_xml_load_skill_keeps_name_and_reason`, `test_xml_read_file_keeps_line_range` |

All 7 regression tests fail on the original code and pass after the fix.

Timing for the skill's commands: `run_experiments --quick` took 0.69 s and the full grid took 10.9 s. Both fit easily within the agent's 120 s `run_shell` limit.

### 4.2 Rerun after the fixes
**Run A: prompt trigger, Lab 4 solved with the Lab 5 skill** (`--approval auto --max-steps 10`, 29 s)

> Solve the Lab 4 vacuum robot task: use Q-learning to train the vacuum robot to reach the charger, then report the best configuration with its charger success rate and trap rate.

1. The similarity check activated `vacuum-rl-report` with a score of **0.6157**. The runner-up, `vacuum-rl-analyzer`, scored 0.3082; the threshold is 0.30.
2. The tool calls were:
   - `load_skill(vacuum-rl-report)`, which was answered "already active" (fix 3);
   - `run_shell python -m unittest discover -s lab_5/tests -t . -v`, exit 0;
   - `run_shell python -m lab_5.run_experiments` (the full grid), exit 0;
   - `read_file {}`, an argument error that the model recovered from;
   - `read_file lab_5/reports/report.md`.
3. Final answer: *"Living reward: -0.04, Gamma: 0.99, Alpha: 0.1, Epsilon: 0.3. Charger success rate: 100.0%. Trap rate: 0.0%. Mean reward: 9.727. Mean steps: 7.82."*

This matches the "Best configuration" line in `lab_5/reports/report.md` exactly: *"Living reward -0.04, gamma 0.99, alpha 0.1, epsilon 0.3: 100.0% charger success, 0.0% trap rate, mean reward 9.727, mean steps 7.82."* The regenerated `report.md` and `results.csv` were identical to the committed files.

**Run B: no match** (`--approval never --max-steps 3`, 27 s)

The prompt was *"Write a binary search function in Python and explain its complexity."* The best score was 0.1429, below the threshold, so no skill ran. The model's attempt to write a file was blocked by `--approval never` as expected. It then answered in text, and there was no crash (fix 2).

**Run C: mid-execution trigger** (`--approval auto --max-steps 8`, 7 s)

The prompt asks the agent to pick and load the right skill for checking that the Q-learner only uses `reset()`/`step()`. The prompt scored 0.1362, below the threshold, so no skill was injected. The model then called **`load_skill(vacuum-rl-validator)`** itself, which was logged as `agent_mid_execution`. It followed the skill by running `python -m unittest discover -s lab_5/tests -v`: exit 0, 25 tests, OK.

An earlier attempt with `--approval never --max-steps 4` also loaded the skill. That attempt stopped when its `run_shell` was denied, and its log lines are records 3–4.

## 5. Audit log verification
The live log is committed as `mini-coding-agent/agent_skills.log`.

```text
$ python mini-coding-agent/verify_skills_log.py mini-coding-agent/agent_skills.log --root .
line  trigger              best skill            score  executed             prompt
   1  prompt_similarity    vacuum-rl-report     0.6157  vacuum-rl-report     Solve the Lab 4 vacuum robot task: use Q-learni...
   2  prompt_similarity    vacuum-rl-analyzer   0.1429  -                    Write a binary search function in Python and ex...
   3  prompt_similarity    vacuum-rl-report     0.1362  -                    Before changing anything, figure out which of y...
   4  agent_mid_execution  vacuum-rl-validator  0.3476  vacuum-rl-validator  This skill validates the vacuum robot Q-learnin...
   5  prompt_similarity    vacuum-rl-report     0.1362  -                    Before changing anything, figure out which of y...
   6  agent_mid_execution  vacuum-rl-validator  0.3214  vacuum-rl-validator  This skill validates the vacuum robot Q-learnin...
Records: 6  (agent_mid_execution: 2, prompt_similarity: 4)
OK: every record has the required fields and is internally consistent.
```
Exit status: 0. Each record has the prompt, the score for every skill, the matched terms, the threshold, the executed skill, and its path.

## 6. Known limitations
- **The 4B model doesn't follow every step.** In Run A it skipped the skill's second test command (`python -m unittest discover -s tests -v`). In Run C its final answer was only "Done." instead of the summary the validator skill asks for. Each run also made one `read_file {}` call with empty arguments and recovered. Raw model output isn't saved, so the cause of that call is unconfirmed.
- **Mid-execution `best_skill` can differ from `executed_skill`.** The scores measure the model's stated *reason*, but the skill that runs is the one it *named*. This is intended (spec FR-4) and the verifier accepts it.
- **Child agents don't get skills.** `delegate` builds a read-only child agent without the skill manager, which keeps sub-agents bounded.
- **One machine and one model.** Results come from one laptop and `qwen3.5:4b`. Other models may score and follow skills differently.

## 7. Reproduce
```bash
# 1. Ollama with an 8k context (port 11435 leaves the default server untouched)
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_CONTEXT_LENGTH=8192 ollama serve &
# 2. Run A (writes mini-coding-agent/agent_skills.log)
python mini-coding-agent/mini_coding_agent.py --cwd . --host http://127.0.0.1:11435 --model qwen3.5:4b \
  --max-new-tokens 600 --approval auto --max-steps 10 \
  "Solve the Lab 4 vacuum robot task: use Q-learning to train the vacuum robot to reach the charger, then report the best configuration with its charger success rate and trap rate."
# 3. Verify the log
python mini-coding-agent/verify_skills_log.py
```
`--approval auto` lets the model run shell commands without asking. Use `ask` to approve each command yourself.

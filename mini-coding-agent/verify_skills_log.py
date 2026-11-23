"""Verify an Agent Skills audit log (``agent_skills.log``) against spec FR-4.

Checks every JSON line for the required fields and checks that they agree with each other:
- every score is in [0, 1] and ``best_skill``/``best_score`` match the highest score;
- a prompt trigger executed the best skill if and only if it met the threshold;
- a mid-execution trigger executed the requested skill if and only if it exists;
- ``skill_path`` is set exactly when a skill ran, and the file exists.

Usage (from the repository root):
    python mini-coding-agent/verify_skills_log.py                      # verify mini-coding-agent/agent_skills.log
    python mini-coding-agent/verify_skills_log.py path/to/log --root .
    python mini-coding-agent/verify_skills_log.py --selfcheck          # write a log offline, then verify it

Exit status: 0 = valid, 1 = problems found, 2 = log missing or empty.
Standard library only.
"""

import argparse
import json
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))

from skills import DEFAULT_SKILL_DIRS, TRIGGER_MID_EXECUTION, TRIGGER_PROMPT, SkillManager  # noqa: E402

DEFAULT_LOG = AGENT_DIR / "agent_skills.log"
REQUIRED_FIELDS = ("timestamp", "trigger_type", "prompt", "similarity_check", "executed_skill", "skill_path")
CHECK_FIELDS = ("scores", "best_skill", "best_score", "threshold")
TOLERANCE = 1e-9

# Prompts for --selfcheck: the Lab 4 demo prompt, one per other skill, and off-topic prompts.
SELF_CHECK_PROMPTS = (
    "Use Q-learning to train the vacuum robot to reach the charger in the Lab 4 grid and report the best configuration.",
    "Which living reward and gamma gave the best results? Explain the tradeoffs.",
    "Validate the Q-learning implementation and test coverage",
    "Review this pull request for bugs",
    "Write a binary search function in Python",
    "Fix the typo in README.md",
)
SELF_CHECK_MID_EXECUTION = (
    ("vacuum-rl-report", "The Lab 4 task needs the Lab 5 Q-learning experiments run and summarized"),
    ("no-such-skill", "Requesting a skill that does not exist"),
)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_record(record, root=None):
    """Return a list of problems with one parsed log record (empty list = valid)."""
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    problems = [f"missing field '{field}'" for field in REQUIRED_FIELDS if field not in record]
    if problems:
        return problems

    trigger = record["trigger_type"]
    if trigger not in (TRIGGER_PROMPT, TRIGGER_MID_EXECUTION):
        problems.append(f"unknown trigger_type {trigger!r}")
    try:
        datetime.fromisoformat(str(record["timestamp"]))
    except ValueError:
        problems.append(f"timestamp {record['timestamp']!r} is not ISO-8601")
    if not isinstance(record["prompt"], str):
        problems.append("prompt is not a string")

    check = record["similarity_check"]
    if not isinstance(check, dict):
        return problems + ["similarity_check is not an object"]
    missing = [f"similarity_check missing '{field}'" for field in CHECK_FIELDS if field not in check]
    if missing:
        return problems + missing

    scores, threshold = check["scores"], check["threshold"]
    if not isinstance(scores, dict):
        return problems + ["similarity_check.scores is not an object"]
    for name, score in scores.items():
        if not is_number(score) or not 0.0 <= score <= 1.0:
            problems.append(f"score for {name!r} is {score!r}, not a number in [0, 1]")
    if not is_number(threshold) or not 0.0 <= threshold <= 1.0:
        problems.append(f"threshold {threshold!r} is not a number in [0, 1]")
    if problems:
        return problems

    top = max(scores.values(), default=0.0)
    best_skill, best_score = check["best_skill"], check["best_score"]
    if top > 0:
        if not is_number(best_score) or abs(best_score - top) > TOLERANCE:
            problems.append(f"best_score {best_score!r} is not the highest score {top}")
        if best_skill not in scores or abs(scores[best_skill] - top) > TOLERANCE:
            problems.append(f"best_skill {best_skill!r} does not have the highest score")
    elif best_skill is not None or best_score != 0:
        problems.append("all scores are 0 but best_skill/best_score are set")

    executed = record["executed_skill"]
    if trigger == TRIGGER_PROMPT:
        expected = best_skill if top > 0 and is_number(best_score) and best_score >= threshold else None
        if executed != expected:
            problems.append(
                f"executed_skill {executed!r} but expected {expected!r} "
                f"(best_score {best_score} vs threshold {threshold})"
            )
    elif trigger == TRIGGER_MID_EXECUTION:
        if "requested_skill" not in record:
            problems.append("mid-execution record missing 'requested_skill'")
        else:
            requested = record["requested_skill"]
            expected = requested if requested in scores else None
            if executed != expected:
                problems.append(f"executed_skill {executed!r} but requested {requested!r} (expected {expected!r})")

    if executed is not None and executed not in scores:
        problems.append(f"executed_skill {executed!r} is not one of the scored skills")
    path = record["skill_path"]
    if (executed is None) != (path is None):
        problems.append("skill_path must be set exactly when executed_skill is set")
    elif path is not None and root is not None and not (Path(root) / path).is_file():
        problems.append(f"skill_path {path!r} does not exist under {root}")
    return problems


def verify_log(log_path, root=None):
    """Parse and check every line. Returns (records, problems), problems as (line_number, message)."""
    records, problems = [], []
    lines = Path(log_path).read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append((number, f"invalid JSON: {exc.msg}"))
            continue
        records.append((number, record))
        problems.extend((number, message) for message in check_record(record, root))
    return records, problems


def clip(text, limit):
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def render_report(log_path, records, problems):
    lines = [f"Log: {log_path}", ""]
    header = f"{'line':>4}  {'trigger':<19}  {'best skill':<19}  {'score':>6}  {'executed':<19}  prompt"
    lines += [header, "-" * len(header)]
    for number, record in records:
        if not isinstance(record, dict):
            continue
        check = record.get("similarity_check") or {}
        score = check.get("best_score")
        lines.append(
            f"{number:>4}  {clip(record.get('trigger_type'), 19):<19}  {clip(check.get('best_skill') or '-', 19):<19}  "
            f"{score if is_number(score) else '-':>6}  {clip(record.get('executed_skill') or '-', 19):<19}  "
            f"{clip(record.get('prompt', ''), 50)}"
        )
    triggers = Counter(r.get("trigger_type") for _, r in records if isinstance(r, dict))
    executed = Counter(r.get("executed_skill") or "(none)" for _, r in records if isinstance(r, dict))
    lines += [
        "",
        f"Records: {len(records)}  ("
        + ", ".join(f"{name}: {count}" for name, count in sorted(triggers.items(), key=lambda i: str(i[0])))
        + ")",
        "Executed: " + ", ".join(f"{name}: {count}" for name, count in sorted(executed.items())),
    ]
    if problems:
        lines += ["", f"FAIL: {len(problems)} problem(s)"] + [f"  line {n}: {message}" for n, message in problems]
    else:
        lines += ["", "OK: every record has the required fields and is internally consistent."]
    return "\n".join(lines)


def run_selfcheck(log_path, root):
    """Run the real SkillManager over fixed prompts, writing a fresh log to ``log_path``."""
    log_path = Path(log_path)
    if log_path.exists():
        log_path.unlink()
    manager = SkillManager(root, skill_dirs=[*DEFAULT_SKILL_DIRS, AGENT_DIR / "skills"], log_path=log_path)
    for prompt in SELF_CHECK_PROMPTS:
        manager.match_and_trigger(prompt)
    for name, reason in SELF_CHECK_MID_EXECUTION:
        manager.execute_skill_by_name(name, reason)
    return log_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify an Agent Skills audit log (spec FR-4).")
    parser.add_argument("log", nargs="?", default=None, help=f"Log to verify (default: {DEFAULT_LOG}).")
    parser.add_argument("--root", default=str(AGENT_DIR.parent), help="Workspace root that skill_path is relative to.")
    parser.add_argument("--selfcheck", action="store_true", help="Write a log offline from fixed prompts, then verify it.")
    parser.add_argument("--out", default=None, help="Where --selfcheck writes its log (default: a temp file).")
    args = parser.parse_args(argv)

    if args.selfcheck:
        out = args.out or Path(tempfile.gettempdir()) / "agent_skills.selfcheck.log"
        log_path = run_selfcheck(out, args.root)
    else:
        log_path = Path(args.log) if args.log else DEFAULT_LOG

    if not log_path.is_file() or not log_path.read_text(encoding="utf-8").strip():
        print(f"No log entries at {log_path}. Run the agent first, or use --selfcheck.", file=sys.stderr)
        return 2
    records, problems = verify_log(log_path, args.root)
    print(render_report(log_path, records, problems))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

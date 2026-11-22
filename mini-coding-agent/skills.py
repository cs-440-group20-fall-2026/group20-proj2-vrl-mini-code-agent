"""Agent Skills component for the mini coding agent (CS440 Project 2, Group 20).

This is the seventh component added to ``rasbt/mini-coding-agent``. It:

1. discovers folder skills: ``<skills dir>/<skill-name>/skill.md`` (or ``SKILL.md``);
2. scores a prompt against every registered skill (the similarity check);
3. activates the best skill when its score meets the threshold (prompt trigger), or
   when the agent asks for a skill by name mid-execution (``load_skill`` tool);
4. appends one JSON line per evaluation to an audit log recording the prompt, the
   similarity check, and the executed skill.

Standard library only.
"""

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SKILL_DIRS = (".claude/skills", "mini-coding-agent/skills", "skills", "skill")
SKILL_FILE_NAMES = ("skill.md", "SKILL.md")
DEFAULT_THRESHOLD = 0.30
NAME_MATCH_SCORE = 0.95
TRIGGER_PROMPT = "prompt_similarity"
TRIGGER_MID_EXECUTION = "agent_mid_execution"

STOPWORDS = frozenset(
    """
    a about after all also an and any are as at be been before but by can could do does
    for from get give had has have how i if in into is it its just let me my need no not
    now of on once only or our out please run should so some than that the their them
    then there these this those to up us use used using want was we what when where which
    while who why will with would you your
    """.split()
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def stem(token):
    """Very small suffix stripper so 'reports'/'report', 'training'/'train' match."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text):
    """Lowercase content tokens with stopwords removed and light stemming."""
    text = str(text).lower()
    text = re.sub(r"\bq[\s_-]?learn", "qlearn", text)  # q-learning / q learning -> qlearning
    tokens = []
    for raw in re.findall(r"[a-z0-9]+", text):
        if len(raw) < 2 or raw in STOPWORDS:
            continue
        tokens.append(stem(raw))
    return tokens


def parse_frontmatter(text):
    """Return (metadata, body) for a markdown file with optional ``---`` frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            break
    else:
        return {}, text
    metadata = {}
    for line in lines[1:end]:
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")
    return metadata, "\n".join(lines[end + 1:]).lstrip("\n")


def first_paragraph(body):
    """First non-heading paragraph of a markdown body, used when no description exists."""
    paragraph = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("#"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return " ".join(paragraph)


class Skill:
    def __init__(self, name, description, keywords, path, body):
        self.name = name
        self.description = description
        self.keywords = keywords
        self.path = Path(path)
        self.body = body
        self.vocabulary = set(tokenize(" ".join([name.replace("-", " "), description, " ".join(keywords)])))

    @classmethod
    def from_file(cls, path):
        path = Path(path)
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        name = metadata.get("name") or path.parent.name
        description = metadata.get("description") or first_paragraph(body)
        raw_keywords = metadata.get("keywords", "").strip("[]")
        keywords = [word.strip().strip('"').strip("'") for word in raw_keywords.split(",") if word.strip()]
        return cls(name=name, description=description, keywords=keywords, path=path, body=body)


class SkillActivation:
    """A skill selected for execution plus the log record that explains why."""

    def __init__(self, skill, trigger_type, record):
        self.skill = skill
        self.trigger_type = trigger_type
        self.record = record

    @property
    def score(self):
        return self.record["similarity_check"]["scores"].get(self.skill.name, 0.0)


class SkillManager:
    def __init__(self, workspace_root, skill_dirs=None, log_path=None, threshold=DEFAULT_THRESHOLD, clock=utc_now):
        self.workspace_root = Path(workspace_root).resolve()
        dirs = DEFAULT_SKILL_DIRS if skill_dirs is None else skill_dirs
        self.skill_dirs = []
        for entry in dirs:
            path = Path(entry)
            path = (path if path.is_absolute() else self.workspace_root / path).resolve()
            if path not in self.skill_dirs:
                self.skill_dirs.append(path)
        self.log_path = Path(log_path) if log_path else None
        self.threshold = float(threshold)
        self.clock = clock
        self.skills = {}
        self.discover()

    # ---- discovery -------------------------------------------------------
    def discover(self):
        """Register every ``<dir>/<name>/skill.md``. The first directory wins on a name clash."""
        self.skills = {}
        for root in self.skill_dirs:
            if not root.is_dir():
                continue
            for folder in sorted(item for item in root.iterdir() if item.is_dir()):
                skill_file = next((folder / n for n in SKILL_FILE_NAMES if (folder / n).is_file()), None)
                if skill_file is None:
                    continue
                skill = Skill.from_file(skill_file)
                self.skills.setdefault(skill.name, skill)
        return list(self.skills.values())

    def relative_path(self, path):
        try:
            return Path(path).resolve().relative_to(self.workspace_root).as_posix()
        except ValueError:
            return Path(path).as_posix()

    def summary(self):
        """One line per skill for the agent's prompt prefix."""
        return [f"{skill.name}: {skill.description}" for skill in self.skills.values()]

    # ---- similarity check ------------------------------------------------
    def idf(self, token):
        """Smoothed inverse document frequency of a token across registered skills."""
        count = len(self.skills)
        df = sum(1 for skill in self.skills.values() if token in skill.vocabulary)
        return math.log(1 + count / max(df, 1))

    def compute_similarity(self, prompt, skill):
        """Score in [0, 1]: IDF-weighted share of the prompt's content words found in the skill.

        Words that appear in every skill (e.g. 'vacuum') count less than words that are
        distinctive to one skill (e.g. 'train'). Naming the skill outright scores at least
        NAME_MATCH_SCORE.
        """
        lowered = str(prompt).lower()
        if skill.name.lower() in lowered or skill.name.lower().replace("-", " ") in lowered:
            return NAME_MATCH_SCORE, sorted(skill.vocabulary & set(tokenize(prompt)))
        prompt_tokens = set(tokenize(prompt))
        if not prompt_tokens:
            return 0.0, []
        matched = sorted(prompt_tokens & skill.vocabulary)
        total = sum(self.idf(token) for token in prompt_tokens)
        hit = sum(self.idf(token) for token in matched)
        return (round(hit / total, 4) if total else 0.0), matched

    def similarity_check(self, prompt):
        scores, matched = {}, {}
        for name, skill in self.skills.items():
            scores[name], matched[name] = self.compute_similarity(prompt, skill)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        best_skill, best_score = ranked[0] if ranked and ranked[0][1] > 0 else (None, 0.0)
        return {
            "scores": scores,
            "matched_terms": matched,
            "best_skill": best_skill,
            "best_score": best_score,
            "threshold": self.threshold,
        }

    # ---- triggers --------------------------------------------------------
    def match_and_trigger(self, prompt):
        """Prompt trigger: activate the best skill if it meets the threshold, and log the check."""
        check = self.similarity_check(prompt)
        skill = None
        if check["best_skill"] is not None and check["best_score"] >= self.threshold:
            skill = self.skills[check["best_skill"]]
        record = self.log(TRIGGER_PROMPT, prompt, check, skill)
        return SkillActivation(skill, TRIGGER_PROMPT, record) if skill else None

    def execute_skill_by_name(self, skill_name, reason=""):
        """Mid-execution trigger: the agent asked for ``skill_name``. Always logged."""
        query = str(reason).strip() or str(skill_name)
        check = self.similarity_check(query)
        skill = self.skills.get(str(skill_name).strip())
        record = self.log(TRIGGER_MID_EXECUTION, query, check, skill, requested_skill=skill_name)
        return SkillActivation(skill, TRIGGER_MID_EXECUTION, record) if skill else None

    def render_instructions(self, skill):
        """The instructions the agent must follow, with Claude-style $ARGUMENTS left blank."""
        body = skill.body.replace("$ARGUMENTS", "").strip()
        return f"Skill: {skill.name} ({self.relative_path(skill.path)})\n\n{body}"

    # ---- audit log -------------------------------------------------------
    def log(self, trigger_type, prompt, check, skill, requested_skill=None):
        record = {
            "timestamp": self.clock(),
            "trigger_type": trigger_type,
            "prompt": prompt,
            "similarity_check": check,
            "executed_skill": skill.name if skill else None,
            "skill_path": self.relative_path(skill.path) if skill else None,
        }
        if requested_skill is not None:
            record["requested_skill"] = requested_skill
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

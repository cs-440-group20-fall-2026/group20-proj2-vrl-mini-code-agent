"""Tests for the Agent Skills component and its integration with the mini coding agent.

Run from the repository root:
    python -m unittest discover -s mini-coding-agent/tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_DIR.parent
sys.path.insert(0, str(AGENT_DIR))

from mini_coding_agent import FakeModelClient, MiniAgent, SessionStore, WorkspaceContext  # noqa: E402
from skills import (  # noqa: E402
    NAME_MATCH_SCORE,
    TRIGGER_MID_EXECUTION,
    TRIGGER_PROMPT,
    SkillManager,
    tokenize,
)

FIXED_TIME = "2026-11-22T00:00:00+00:00"
REQUIRED_LOG_FIELDS = {"timestamp", "trigger_type", "prompt", "similarity_check", "executed_skill", "skill_path"}
LAB4_PROMPT = "Use Q-learning to train the vacuum robot to reach the charger in the Lab 4 grid and report the best configuration."


def write_skill(root, folder, text, filename="skill.md"):
    path = Path(root) / folder
    path.mkdir(parents=True, exist_ok=True)
    (path / filename).write_text(text, encoding="utf-8")
    return path / filename


TRAIN_SKILL = """---
name: grid-trainer
description: Train a gridworld robot with Q-learning and report charger success.
---

# Grid Trainer

1. Run `python -m lab_5.run_experiments $ARGUMENTS`.
2. Summarize the report.
"""

REVIEW_SKILL = """---
name: pr-review
description: Review a pull request diff for bugs, style issues, and missing tests.
---

# PR Review

Read the diff and list findings.
"""


class SkillTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.log_path = self.root / "agent_skills.log"
        write_skill(self.root / "skills", "grid-trainer", TRAIN_SKILL)
        write_skill(self.root / "skills", "pr-review", REVIEW_SKILL, filename="SKILL.md")

    def tearDown(self):
        self.tmp.cleanup()

    def manager(self, **kwargs):
        kwargs.setdefault("skill_dirs", ["skills"])
        kwargs.setdefault("log_path", self.log_path)
        kwargs.setdefault("clock", lambda: FIXED_TIME)
        return SkillManager(self.root, **kwargs)

    def log_records(self):
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]


class DiscoveryTests(SkillTestCase):
    def test_discovers_skill_md_and_SKILL_md(self):
        self.assertEqual(sorted(self.manager().skills), ["grid-trainer", "pr-review"])

    def test_ignores_folders_without_skill_file_and_missing_dirs(self):
        (self.root / "skills" / "empty-folder").mkdir()
        (self.root / "skills" / "notes").mkdir()
        (self.root / "skills" / "notes" / "README.md").write_text("not a skill", encoding="utf-8")
        manager = self.manager(skill_dirs=["skills", "does-not-exist"])
        self.assertEqual(sorted(manager.skills), ["grid-trainer", "pr-review"])

    def test_frontmatter_is_parsed_and_stripped_from_body(self):
        skill = self.manager().skills["grid-trainer"]
        self.assertEqual(skill.description, "Train a gridworld robot with Q-learning and report charger success.")
        self.assertTrue(skill.body.startswith("# Grid Trainer"))

    def test_folder_name_and_first_paragraph_used_without_frontmatter(self):
        write_skill(self.root / "skills", "lint-fixer", "# Lint Fixer\n\nFix flake8 warnings in changed files.\n")
        skill = self.manager().skills["lint-fixer"]
        self.assertEqual(skill.description, "Fix flake8 warnings in changed files.")

    def test_frontmatter_survives_utf8_bom(self):
        path = self.root / "skills" / "bom-skill"
        path.mkdir()
        (path / "skill.md").write_bytes("﻿---\nname: bom-skill\ndescription: Saved by a Windows editor.\n---\n# Body\n".encode("utf-8"))
        skill = self.manager().skills["bom-skill"]
        self.assertEqual(skill.description, "Saved by a Windows editor.")
        self.assertTrue(skill.body.startswith("# Body"))

    def test_yaml_list_keywords(self):
        write_skill(
            self.root / "skills", "deployer",
            "---\nname: deployer\ndescription: Ship it.\nkeywords:\n  - kubernetes\n  - helm chart\n---\nBody\n",
        )
        skill = self.manager().skills["deployer"]
        self.assertEqual(skill.keywords, ["kubernetes", "helm chart"])
        self.assertIn("kubernet", skill.vocabulary)

    def test_inline_list_keywords(self):
        write_skill(self.root / "skills", "lister", "---\nname: lister\ndescription: x\nkeywords: [alpha, \"beta\"]\n---\n")
        self.assertEqual(self.manager().skills["lister"].keywords, ["alpha", "beta"])

    def test_first_directory_wins_on_name_clash(self):
        write_skill(self.root / "other", "grid-trainer", "---\nname: grid-trainer\ndescription: shadow copy\n---\n")
        manager = self.manager(skill_dirs=["skills", "other"])
        self.assertIn("gridworld", manager.skills["grid-trainer"].description)

    def test_repository_discovers_lab5_skill(self):
        manager = SkillManager(REPO_ROOT, log_path=None)
        self.assertIn("vacuum-rl-report", manager.skills)
        self.assertEqual(
            manager.relative_path(manager.skills["vacuum-rl-report"].path),
            ".claude/skills/vacuum-rl-report/SKILL.md",
        )

    def test_repository_discovers_agent_local_pr_review_skill(self):
        manager = SkillManager(REPO_ROOT, log_path=None)
        self.assertEqual(
            manager.relative_path(manager.skills["pr-review"].path),
            "mini-coding-agent/skills/pr-review/skill.md",
        )


class SimilarityTests(SkillTestCase):
    def test_tokenize_normalizes_q_learning_variants(self):
        self.assertEqual(tokenize("Q-learning"), tokenize("q learning"))
        self.assertIn("qlearn", tokenize("Q_learning agent"))

    def test_scores_are_bounded(self):
        manager = self.manager()
        for prompt in ["", "train the robot", "review pull request", "grid-trainer", "zzz"]:
            for score in manager.similarity_check(prompt)["scores"].values():
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)

    def test_relevant_skill_ranks_first(self):
        manager = self.manager()
        self.assertEqual(manager.similarity_check("train the robot with Q-learning")["best_skill"], "grid-trainer")
        self.assertEqual(manager.similarity_check("review my pull request for bugs")["best_skill"], "pr-review")

    def test_unrelated_prompt_has_no_best_skill(self):
        check = self.manager().similarity_check("write a binary search function")
        self.assertIsNone(check["best_skill"])
        self.assertEqual(check["best_score"], 0.0)

    def test_naming_the_skill_scores_name_match(self):
        manager = self.manager()
        self.assertEqual(manager.similarity_check("please use grid-trainer")["scores"]["grid-trainer"], NAME_MATCH_SCORE)
        self.assertEqual(manager.similarity_check("run the pr review skill")["scores"]["pr-review"], NAME_MATCH_SCORE)

    def test_name_match_requires_word_boundaries(self):
        score = self.manager().similarity_check("the appr reviewer approved it")["scores"]["pr-review"]
        self.assertLess(score, NAME_MATCH_SCORE)

    def test_similarity_is_deterministic(self):
        manager = self.manager()
        self.assertEqual(manager.similarity_check(LAB4_PROMPT), manager.similarity_check(LAB4_PROMPT))

    def test_lab4_prompt_selects_lab5_report_skill_in_repository(self):
        manager = SkillManager(REPO_ROOT, log_path=None)
        check = manager.similarity_check(LAB4_PROMPT)
        self.assertEqual(check["best_skill"], "vacuum-rl-report")
        self.assertGreaterEqual(check["best_score"], manager.threshold)
        self.assertLess(check["scores"]["pr-review"], manager.threshold)

    def test_repository_prompts_route_to_expected_skill(self):
        manager = SkillManager(REPO_ROOT, log_path=None)
        expected = {
            "Review this pull request for bugs": "pr-review",
            "Can you code review the changes on my branch?": "pr-review",
            "Which living reward and gamma gave the best results? Explain the tradeoffs.": "vacuum-rl-analyzer",
            "Validate the Q-learning implementation and test coverage": "vacuum-rl-validator",
            "Regenerate the Lab 5 reports": "vacuum-rl-report",
            "Write a binary search function in Python": None,
        }
        for prompt, skill_name in expected.items():
            with self.subTest(prompt=prompt):
                activation = manager.match_and_trigger(prompt)
                self.assertEqual(activation.skill.name if activation else None, skill_name)


class TriggerAndLogTests(SkillTestCase):
    def test_threshold_boundary(self):
        prompt = "train the robot"
        score = self.manager().similarity_check(prompt)["scores"]["grid-trainer"]
        self.assertIsNotNone(self.manager(threshold=score).match_and_trigger(prompt))
        self.assertIsNone(self.manager(threshold=score + 0.0001).match_and_trigger(prompt))

    def test_prompt_trigger_logs_prompt_check_and_executed_skill(self):
        activation = self.manager().match_and_trigger("train the robot with Q-learning")
        self.assertEqual(activation.skill.name, "grid-trainer")
        [record] = self.log_records()
        self.assertTrue(REQUIRED_LOG_FIELDS <= set(record))
        self.assertEqual(record["timestamp"], FIXED_TIME)
        self.assertEqual(record["trigger_type"], TRIGGER_PROMPT)
        self.assertEqual(record["prompt"], "train the robot with Q-learning")
        self.assertEqual(set(record["similarity_check"]["scores"]), {"grid-trainer", "pr-review"})
        self.assertEqual(record["similarity_check"]["threshold"], 0.30)
        self.assertEqual(record["executed_skill"], "grid-trainer")
        self.assertEqual(record["skill_path"], "skills/grid-trainer/skill.md")

    def test_non_matching_prompt_is_still_logged(self):
        self.assertIsNone(self.manager().match_and_trigger("write a binary search function"))
        [record] = self.log_records()
        self.assertIsNone(record["executed_skill"])
        self.assertIsNone(record["skill_path"])

    def test_one_log_line_per_evaluation(self):
        manager = self.manager()
        manager.match_and_trigger("train the robot")
        manager.match_and_trigger("hello")
        manager.execute_skill_by_name("pr-review", "check the diff")
        self.assertEqual([r["trigger_type"] for r in self.log_records()], [TRIGGER_PROMPT, TRIGGER_PROMPT, TRIGGER_MID_EXECUTION])

    def test_mid_execution_trigger_logs_request(self):
        activation = self.manager().execute_skill_by_name("pr-review", "need to review the diff")
        self.assertEqual(activation.trigger_type, TRIGGER_MID_EXECUTION)
        [record] = self.log_records()
        self.assertEqual(record["requested_skill"], "pr-review")
        self.assertEqual(record["prompt"], "need to review the diff")
        self.assertEqual(record["executed_skill"], "pr-review")

    def test_unknown_mid_execution_skill_returns_none_and_logs_null(self):
        self.assertIsNone(self.manager().execute_skill_by_name("no-such-skill"))
        [record] = self.log_records()
        self.assertEqual(record["requested_skill"], "no-such-skill")
        self.assertIsNone(record["executed_skill"])

    def test_render_instructions_drops_frontmatter_and_arguments_placeholder(self):
        manager = self.manager()
        text = manager.render_instructions(manager.skills["grid-trainer"])
        self.assertTrue(text.startswith("Skill: grid-trainer (skills/grid-trainer/skill.md)"))
        self.assertNotIn("$ARGUMENTS", text)
        self.assertNotIn("description:", text)
        self.assertIn("python -m lab_5.run_experiments", text)


class AgentIntegrationTests(SkillTestCase):
    def agent(self, outputs, skill_manager="default", workspace_root=None):
        if skill_manager == "default":
            skill_manager = self.manager()
        workspace = WorkspaceContext.build(workspace_root or self.root)
        return MiniAgent(
            model_client=FakeModelClient(outputs),
            workspace=workspace,
            session_store=SessionStore(self.root / ".mini-coding-agent" / "sessions"),
            approval_policy="never",
            skill_manager=skill_manager,
        )

    def test_prompt_trigger_injects_skill_instructions_before_model_call(self):
        agent = self.agent(["<final>done</final>"])
        self.assertEqual(agent.ask("train the robot with Q-learning"), "done")
        prompt = agent.model_client.prompts[0]
        self.assertIn("Active skill (prompt_similarity):", prompt)
        self.assertIn("python -m lab_5.run_experiments", prompt)
        self.assertEqual(agent.session["active_skill"]["name"], "grid-trainer")
        self.assertIn("skill", [item["role"] for item in agent.session["history"]])
        self.assertEqual(self.log_records()[0]["executed_skill"], "grid-trainer")

    def test_no_match_leaves_prompt_without_active_skill(self):
        agent = self.agent(["<final>ok</final>"])
        agent.ask("write a binary search function")
        self.assertNotIn("Active skill (", agent.model_client.prompts[0])
        self.assertIsNone(self.log_records()[0]["executed_skill"])

    def test_prefix_lists_skills_and_load_skill_tool(self):
        agent = self.agent([])
        self.assertIn("load_skill", agent.tools)
        self.assertIn("- grid-trainer: Train a gridworld robot", agent.prefix)

    def test_mid_execution_load_skill(self):
        agent = self.agent([
            '<tool>{"name":"load_skill","args":{"name":"pr-review","reason":"I need to review the diff"}}</tool>',
            "<final>reviewed</final>",
        ])
        self.assertEqual(agent.ask("look at what changed in the branch"), "reviewed")
        self.assertIn("loaded skill pr-review", agent.session["history"][-2]["content"])
        self.assertIn("Active skill (agent_mid_execution):", agent.model_client.prompts[1])
        self.assertEqual([r["trigger_type"] for r in self.log_records()], [TRIGGER_PROMPT, TRIGGER_MID_EXECUTION])
        self.assertEqual(self.log_records()[1]["executed_skill"], "pr-review")

    def test_load_skill_unknown_name_returns_error(self):
        agent = self.agent([])
        result = agent.run_tool("load_skill", {"name": "nope"})
        self.assertIn("unknown skill 'nope'", result)
        self.assertIsNone(agent.session["active_skill"])

    def test_load_skill_requires_name(self):
        self.assertIn("name must not be empty", self.agent([]).run_tool("load_skill", {}))

    def test_without_skill_manager_agent_matches_upstream(self):
        agent = self.agent(["<final>ok</final>"], skill_manager=None)
        self.assertNotIn("load_skill", agent.tools)
        self.assertNotIn("Skills:", agent.prefix)
        agent.ask("train the robot")
        self.assertFalse(self.log_path.exists())

    def test_reset_clears_active_skill(self):
        agent = self.agent(["<final>done</final>"])
        agent.ask("train the robot with Q-learning")
        agent.reset()
        self.assertIsNone(agent.session["active_skill"])

    def test_lab4_prompt_activates_lab5_skill_in_repository(self):
        manager = SkillManager(REPO_ROOT, log_path=self.log_path, clock=lambda: FIXED_TIME)
        agent = self.agent(["<final>done</final>"], skill_manager=manager, workspace_root=REPO_ROOT)
        agent.ask(LAB4_PROMPT)
        self.assertEqual(agent.session["active_skill"]["path"], ".claude/skills/vacuum-rl-report/SKILL.md")
        self.assertIn("env.reset()", agent.model_client.prompts[0])
        self.assertEqual(self.log_records()[0]["executed_skill"], "vacuum-rl-report")


class LiveRunRegressionTests(SkillTestCase):
    """Failures seen in the first live Ollama run (2026-11-22), fixed in mini_coding_agent.py."""

    agent = AgentIntegrationTests.agent

    def test_latest_read_of_report_shows_best_configuration(self):
        manager = SkillManager(REPO_ROOT, log_path=self.log_path)
        agent = self.agent(
            ['<tool>{"name":"read_file","args":{"path":"lab_5/reports/report.md","start":1,"end":200}}</tool>',
             "<final>done</final>"],
            skill_manager=manager, workspace_root=REPO_ROOT,
        )
        agent.ask(LAB4_PROMPT)
        second_prompt = agent.model_client.prompts[1]
        self.assertIn("## Best configuration", second_prompt)
        self.assertIn("100.0% charger success", second_prompt.split("## Best configuration", 1)[1])

    def test_older_tool_output_is_still_clipped(self):
        agent = self.agent([])
        for name in ("first", "second"):
            agent.record({"role": "tool", "name": "search", "args": {"pattern": name}, "content": name * 600, "created_at": "-"})
        text = agent.history_text()
        self.assertIn("second" * 600, text)
        self.assertNotIn("first" * 600, text)

    def test_long_transcript_keeps_newest_items(self):
        from mini_coding_agent import MAX_HISTORY

        agent = self.agent([])
        for index in range(40):
            agent.record({"role": "user", "content": f"message-{index} " + "x" * 800, "created_at": "-"})
        text = agent.history_text()
        self.assertLessEqual(len(text), MAX_HISTORY)
        self.assertTrue(text.startswith("[earlier transcript truncated]"))
        self.assertIn("message-39", text)
        self.assertNotIn("message-0 ", text)

    def test_xml_load_skill_keeps_name_and_reason(self):
        kind, payload = MiniAgent.parse('<tool name="load_skill"><name>pr-review</name><reason>check diff</reason></tool>')
        self.assertEqual(kind, "tool")
        self.assertEqual(payload["args"], {"name": "pr-review", "reason": "check diff"})

    def test_xml_read_file_keeps_line_range(self):
        _, payload = MiniAgent.parse('<tool name="read_file"><path>README.md</path><start>1</start><end>40</end></tool>')
        self.assertEqual(payload["args"], {"path": "README.md", "start": "1", "end": "40"})

    def test_reloading_active_skill_is_a_no_op(self):
        agent = self.agent(["<final>done</final>"])
        agent.ask("train the robot with Q-learning")
        before = len(self.log_records())
        result = agent.run_tool("load_skill", {"name": "grid-trainer"})
        self.assertIn("already active", result)
        self.assertEqual(len(self.log_records()), before)
        self.assertEqual(agent.session["active_skill"]["trigger_type"], TRIGGER_PROMPT)

    def test_main_switches_stdout_to_utf8(self):
        import io
        import mini_coding_agent

        original = sys.stdout, sys.stderr
        sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
        sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
        try:
            with self.assertRaises(SystemExit):
                mini_coding_agent.main(["--help"])
            self.assertEqual(sys.stdout.encoding.lower(), "utf-8")
            print("O(log₂ n)")  # raised UnicodeEncodeError before the fix
        finally:
            sys.stdout, sys.stderr = original


if __name__ == "__main__":
    unittest.main()

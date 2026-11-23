"""Tests for verify_skills_log.py (audit log verification, spec FR-4).

Run from the repository root:
    python -m unittest discover -s mini-coding-agent/tests -v
"""

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_DIR.parent
sys.path.insert(0, str(AGENT_DIR))

import verify_skills_log as verifier  # noqa: E402
from skills import SkillManager  # noqa: E402

LAB4_PROMPT = "Use Q-learning to train the vacuum robot to reach the charger in the Lab 4 grid and report the best configuration."


class VerifierTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "agent_skills.log"
        manager = SkillManager(REPO_ROOT, log_path=None, clock=lambda: "2026-11-22T00:00:00+00:00")
        self.matched = manager.match_and_trigger(LAB4_PROMPT).record
        self.unmatched = manager.log("prompt_similarity", "hello", manager.similarity_check("write a binary search"), None)
        self.mid = manager.execute_skill_by_name("pr-review", "review the diff").record

    def tearDown(self):
        self.tmp.cleanup()

    def problems(self, record):
        return verifier.check_record(record, REPO_ROOT)

    def write_log(self, *records, raw_lines=()):
        lines = [json.dumps(record) for record in records] + list(raw_lines)
        self.log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            code = verifier.main([*args, "--root", str(REPO_ROOT)])
        return code, out.getvalue()


class ValidRecordTests(VerifierTestCase):
    def test_real_records_are_valid(self):
        for record in (self.matched, self.unmatched, self.mid):
            self.assertEqual(self.problems(record), [])

    def test_selfcheck_writes_and_verifies_log(self):
        code, output = self.run_main("--selfcheck", "--out", str(self.log_path))
        self.assertEqual(code, 0, output)
        self.assertIn("OK:", output)
        records, problems = verifier.verify_log(self.log_path, REPO_ROOT)
        self.assertEqual(problems, [])
        self.assertEqual(len(records), len(verifier.SELF_CHECK_PROMPTS) + len(verifier.SELF_CHECK_MID_EXECUTION))
        executed = [record["executed_skill"] for _, record in records]
        self.assertEqual(executed[0], "vacuum-rl-report")
        self.assertIn(None, executed)

    def test_selfcheck_replaces_previous_log(self):
        self.log_path.write_text("not json\n", encoding="utf-8")
        code, _ = self.run_main("--selfcheck", "--out", str(self.log_path))
        self.assertEqual(code, 0)


class InvalidRecordTests(VerifierTestCase):
    def tampered(self, record, change):
        record = copy.deepcopy(record)
        change(record)
        return self.problems(record)

    def assertProblem(self, problems, fragment):
        self.assertTrue(any(fragment in p for p in problems), f"{fragment!r} not in {problems}")

    def test_missing_field(self):
        self.assertProblem(self.tampered(self.matched, lambda r: r.pop("executed_skill")), "missing field 'executed_skill'")

    def test_unknown_trigger_type(self):
        self.assertProblem(self.tampered(self.matched, lambda r: r.update(trigger_type="guess")), "unknown trigger_type")

    def test_bad_timestamp(self):
        self.assertProblem(self.tampered(self.matched, lambda r: r.update(timestamp="yesterday")), "ISO-8601")

    def test_score_out_of_range(self):
        def change(r):
            r["similarity_check"]["scores"]["pr-review"] = 1.5
        self.assertProblem(self.tampered(self.matched, change), "not a number in [0, 1]")

    def test_best_skill_not_highest(self):
        def change(r):
            r["similarity_check"]["best_skill"] = "vacuum-rl-validator"
        self.assertProblem(self.tampered(self.matched, change), "does not have the highest score")

    def test_executed_below_threshold(self):
        def change(r):
            r["similarity_check"]["threshold"] = 0.99
        self.assertProblem(self.tampered(self.matched, change), "expected None")

    def test_not_executed_above_threshold(self):
        def change(r):
            r.update(executed_skill=None, skill_path=None)
        self.assertProblem(self.tampered(self.matched, change), "expected 'vacuum-rl-report'")

    def test_mid_execution_requires_requested_skill(self):
        self.assertProblem(self.tampered(self.mid, lambda r: r.pop("requested_skill")), "missing 'requested_skill'")

    def test_mid_execution_must_run_requested_skill(self):
        self.assertProblem(self.tampered(self.mid, lambda r: r.update(executed_skill="vacuum-rl-report")), "but requested")

    def test_skill_path_must_exist(self):
        self.assertProblem(
            self.tampered(self.matched, lambda r: r.update(skill_path="skills/ghost/skill.md")), "does not exist"
        )

    def test_skill_path_set_without_executed_skill(self):
        self.assertProblem(
            self.tampered(self.unmatched, lambda r: r.update(skill_path="x.md")), "set exactly when executed_skill"
        )


class LogFileTests(VerifierTestCase):
    def test_invalid_json_line_is_reported_with_line_number(self):
        self.write_log(self.matched, raw_lines=["{not json"])
        _, problems = verifier.verify_log(self.log_path, REPO_ROOT)
        self.assertEqual(problems[0][0], 2)
        self.assertIn("invalid JSON", problems[0][1])

    def test_main_exit_codes(self):
        self.write_log(self.matched, self.unmatched, self.mid)
        self.assertEqual(self.run_main(str(self.log_path))[0], 0)
        broken = copy.deepcopy(self.matched)
        broken["similarity_check"]["threshold"] = 0.99
        self.write_log(self.matched, broken)
        code, output = self.run_main(str(self.log_path))
        self.assertEqual(code, 1)
        self.assertIn("line 2:", output)
        self.assertEqual(self.run_main(str(Path(self.tmp.name) / "missing.log"))[0], 2)

    def test_agent_written_log_verifies(self):
        """A log written by the real agent loop (FakeModelClient) passes verification."""
        from mini_coding_agent import FakeModelClient, MiniAgent, SessionStore, WorkspaceContext

        manager = SkillManager(REPO_ROOT, log_path=self.log_path)
        agent = MiniAgent(
            model_client=FakeModelClient([
                "<final>done</final>",
                '<tool>{"name":"load_skill","args":{"name":"vacuum-rl-validator","reason":"check reset/step only"}}</tool>',
                "<final>validated</final>",
            ]),
            workspace=WorkspaceContext.build(REPO_ROOT),
            session_store=SessionStore(Path(self.tmp.name) / "sessions"),
            approval_policy="never",
            skill_manager=manager,
        )
        agent.ask(LAB4_PROMPT)
        agent.ask("hello there")
        records, problems = verifier.verify_log(self.log_path, REPO_ROOT)
        self.assertEqual(problems, [])
        self.assertEqual(
            [r["trigger_type"] for _, r in records],
            ["prompt_similarity", "prompt_similarity", "agent_mid_execution"],
        )


if __name__ == "__main__":
    unittest.main()

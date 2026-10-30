"""Strategy 4 checks: sub-agent config is wired correctly, the pipeline hands off only the brief,
and a learner only needs reset()/step()."""
import json
import re
import unittest
from pathlib import Path
from unittest import mock
from vacuum.environment import VacuumEnvironment, CHARGER
import orchestrator
from orchestrator import REVIEWERS, PIPELINE, build_command, build_brief, gate, parse_report

STRATEGY = Path(__file__).resolve().parents[1]
AGENTS = sorted((STRATEGY / '.claude' / 'agents').glob('*.md'))
CONSTRAINTS = STRATEGY / '.claude' / 'constraints.md'
SCHEMA = STRATEGY / '.claude' / 'agents' / 'report.schema.json'
READ_ONLY = {'Read', 'Grep', 'Glob'}
ALLOWED_TOOLS = {'research-implementer': READ_ONLY | {'Edit', 'Write'},
                 'research-verifier': READ_ONLY | {'Bash'}}


def parse_agent(path):
    _, frontmatter, body = path.read_text().split('---', 2)
    fields = dict(line.split(':', 1) for line in frontmatter.strip().splitlines())
    return {k.strip(): v.strip() for k, v in fields.items()}, body


def report(agent, *statuses):
    return {'agent': agent,
            'findings': [{'status': s, 'evidence': f'x.py:{i}', 'note': f'{s} note {i}'}
                         for i, s in enumerate(statuses)]}


def fake_spawn(replies):
    """Stand-in for orchestrator.spawn: records (agent, task) and returns canned reports, no Claude call."""
    calls = []

    def spawn(name, task):
        calls.append((name, task))
        return json.dumps({orchestrator.RESULT_KEY: replies.get(name, report(name, 'PASS'))})
    return spawn, calls


class AgentView:
    """What a learner is handed: reset() and step(), nothing else."""
    __slots__ = ('reset', 'step')

    def __init__(self, env):
        self.reset = env.reset
        self.step = env.step


class TestOrchestratorConfig(unittest.TestCase):
    def test_agents_exist(self):
        self.assertEqual([p.stem for p in AGENTS], sorted([*REVIEWERS, *PIPELINE, orchestrator.VERIFIER]))

    def test_frontmatter(self):
        for path in AGENTS:
            fields, _ = parse_agent(path)
            self.assertEqual(fields['name'], path.stem)
            self.assertTrue(fields['description'])
            tools = {t.strip() for t in fields['tools'].split(',')}
            self.assertLessEqual(tools, ALLOWED_TOOLS.get(path.stem, READ_ONLY), path.name)

    def test_scoped_paths_exist(self):
        texts = {path.name: parse_agent(path)[1] for path in AGENTS}
        texts[CONSTRAINTS.name] = CONSTRAINTS.read_text()
        for name, text in texts.items():
            for ref in re.findall(r'`([^`]*/[^`]*)`', text):
                if ref == f'{STRATEGY.name}/':  # the scope declaration itself
                    continue
                self.assertTrue((STRATEGY / ref).exists(), f'{name}: {ref}')

    def test_agents_read_constraints(self):
        self.assertIn(f'Stay inside `{STRATEGY.name}/`', CONSTRAINTS.read_text())
        for path in AGENTS:
            _, body = parse_agent(path)
            self.assertIn('Read `.claude/constraints.md` first', body, path.name)

    def test_schema_lists_each_agent(self):
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(sorted(schema['properties']['agent']['enum']), [p.stem for p in AGENTS])

    def test_orchestrator_routes_to_each_agent(self):
        memory = (STRATEGY / 'CLAUDE.md').read_text()
        for path in AGENTS:
            self.assertIn(path.stem, memory)

    def test_orchestrator_spawns_each_agent(self):
        for path in AGENTS:
            command = build_command(path.stem)
            self.assertEqual(command[command.index('--agent') + 1], path.stem)
            self.assertIn('--json-schema', command)

    def test_only_implementer_may_edit_context(self):
        command = build_command('research-implementer')
        self.assertEqual(command[command.index('--allowedTools') + 1], 'Edit(context/research/**)')
        for name in [*REVIEWERS, 'researcher']:
            self.assertNotIn('--allowedTools', build_command(name), name)

    def test_verifier_may_only_run_unittest(self):
        command = build_command(orchestrator.VERIFIER)
        self.assertEqual(command[command.index('--allowedTools') + 1], 'Bash(python3 -m unittest *)')

    def test_testing_md_defines_research_verification(self):
        testing = (STRATEGY / 'context' / 'testing.md').read_text()
        self.assertIn('## Research verification', testing)
        self.assertIn('python3 -m unittest', testing)

    def test_prompt_carries_constraints(self):
        self.assertTrue(orchestrator.build_prompt('task').startswith(CONSTRAINTS.read_text()))


class TestPipeline(unittest.TestCase):
    def test_gate(self):
        self.assertTrue(gate(report('researcher', 'INFO', 'PASS')))
        self.assertFalse(gate(report('researcher', 'INFO', 'FAIL')))
        self.assertFalse(gate(report('researcher', 'INFO', 'UNKNOWN')))
        self.assertFalse(gate(report('researcher', 'PASS')))

    def test_brief_carries_only_info(self):
        brief = build_brief('q', report('researcher', 'INFO', 'PASS', 'INFO'))
        self.assertIn('INFO note 0 (x.py:0)', brief)
        self.assertIn('INFO note 2 (x.py:2)', brief)
        self.assertNotIn('PASS note', brief)

    def test_parse_report_rejects_wrong_agent(self):
        stdout = json.dumps({orchestrator.RESULT_KEY: report('test-reviewer', 'PASS')})
        with self.assertRaises(ValueError):
            parse_report(stdout, 'researcher')

    def test_parse_report_accepts_string_result(self):
        stdout = json.dumps({orchestrator.RESULT_KEY: json.dumps(report('researcher', 'INFO'))})
        self.assertEqual(parse_report(stdout, 'researcher')['agent'], 'researcher')

    def test_gate_stop_spawns_nothing_else(self):
        spawn, calls = fake_spawn({'researcher': report('researcher', 'INFO', 'UNKNOWN')})
        with mock.patch.object(orchestrator, 'spawn', spawn):
            reports = orchestrator.pipeline('q')
        self.assertEqual([name for name, _ in calls], ['researcher'])
        self.assertEqual(len(reports), 1)

    def test_verifier_always_runs_after_implementer(self):
        spawn, calls = fake_spawn({
            'researcher': report('researcher', 'INFO'),
            'research-implementer': report('research-implementer', 'FAIL'),
        })
        with mock.patch.object(orchestrator, 'spawn', spawn):
            orchestrator.pipeline('q')
        self.assertEqual([name for name, _ in calls], [*PIPELINE, orchestrator.VERIFIER])

    def test_implementer_gets_only_the_brief(self):
        research = report('researcher', 'INFO', 'PASS')
        spawn, calls = fake_spawn({'researcher': research})
        with mock.patch.object(orchestrator, 'spawn', spawn):
            orchestrator.pipeline('q')
        self.assertEqual(dict(calls)['research-implementer'], build_brief('q', research))


class TestAgentIsolation(unittest.TestCase):
    def test_no_public_model_attributes(self):
        public = {k for k in vars(VacuumEnvironment()) if not k.startswith('_')}
        self.assertEqual(public, {'state', 'terminated'})

    def test_learner_reaches_charger_with_only_reset_step(self):
        view = AgentView(VacuumEnvironment(intended_probability=1))
        state = view.reset()
        for _ in range(10):
            result = view.step('Right' if state[1] < 3 else 'Down')
            state = result.state
            if result.terminated:
                break
        self.assertEqual(state, CHARGER)
        with self.assertRaises(AttributeError):
            view._intended_probability


if __name__ == '__main__':
    unittest.main()

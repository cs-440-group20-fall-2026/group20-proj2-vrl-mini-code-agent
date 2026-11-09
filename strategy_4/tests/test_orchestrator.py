"""Strategy 4 checks: sub-agent config is wired correctly, the pipeline hands off only the brief,
and a learner only needs reset()/step()."""
import json
import re
import tempfile
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

    def test_verbose_command_streams(self):
        quiet, loud = build_command('researcher'), build_command('researcher', verbose=True)
        self.assertEqual(quiet[quiet.index('--output-format') + 1], 'json')
        self.assertEqual(loud[loud.index('--output-format') + 1], 'stream-json')
        self.assertIn('--verbose', loud)  # the CLI requires it for stream-json

    def test_describe_stream_events(self):
        tool = {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': f'{STRATEGY}/context/testing.md'}}]}}
        self.assertEqual(orchestrator.describe(tool), ['  -> Read context/testing.md'])
        done = {'type': 'result', 'total_cost_usd': 0.1, 'num_turns': 3,
                'permission_denials': [{'tool_name': 'Bash', 'tool_input': {'command': 'cat x'}}]}
        self.assertEqual(orchestrator.describe(done),
                         ['  done: $0.100, 3 turns, 1 denied', '  !! denied Bash cat x'])
        self.assertEqual(orchestrator.describe({'type': 'system'}), [])

    def test_verbose_flag_before_or_after_subcommand(self):
        for argv, expected in [(['pipeline', 'q'], False), (['-v', 'pipeline', 'q'], True),
                               (['pipeline', 'q', '--verbose'], True), (['review', '-v'], True)]:
            with mock.patch.object(orchestrator, 'pipeline', return_value=[]), \
                 mock.patch.object(orchestrator, 'run', return_value={'agent': 'x', 'findings': []}), \
                 mock.patch('sys.argv', ['orchestrator.py', *argv]), mock.patch('sys.stdout'):
                orchestrator.main()
            self.assertEqual(orchestrator.VERBOSE, expected, argv)
        orchestrator.VERBOSE = False

    def test_prompt_carries_constraints(self):
        self.assertTrue(orchestrator.build_prompt('task').startswith(CONSTRAINTS.read_text()))
        self.assertIn(SCHEMA.read_text(), orchestrator.build_prompt('task'))


class TestPipeline(unittest.TestCase):
    def test_gate(self):
        self.assertTrue(gate(report('researcher', 'INFO', 'PASS')))
        self.assertFalse(gate(report('researcher', 'INFO', 'FAIL')))
        self.assertTrue(gate(report('researcher', 'INFO', 'UNKNOWN')))  # open questions travel on
        self.assertFalse(gate(report('researcher', 'UNKNOWN')))  # a decline has no INFO
        self.assertFalse(gate(report('researcher', 'PASS')))

    def test_brief_carries_only_info(self):
        brief = build_brief('q', report('researcher', 'INFO', 'PASS', 'INFO'))
        self.assertIn('INFO note 0 (x.py:0)', brief)
        self.assertIn('INFO note 2 (x.py:2)', brief)
        self.assertNotIn('PASS note', brief)

    def test_brief_records_open_questions(self):
        brief = build_brief('q', report('researcher', 'INFO', 'UNKNOWN', 'FAIL'))
        _, questions = brief.split('Open questions')
        self.assertIn('UNKNOWN note 1 (x.py:1)', questions)
        self.assertNotIn('FAIL note', brief)
        self.assertNotIn('Open questions', build_brief('q', report('researcher', 'INFO')))

    def test_brief_asks_for_code_and_tests(self):
        brief = build_brief('q', report('researcher', 'INFO'))
        self.assertIn('Python module', brief)
        self.assertIn('test_*.py', brief)

    def test_guard_skips_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / '__pycache__').mkdir()
            (Path(tmp) / '__pycache__' / 'runner.pyc').write_bytes(b'\xff\xfe bytecode')
            (Path(tmp) / 'runner.py').write_text('policy = None\n')
            with mock.patch.object(orchestrator, 'RESEARCH', Path(tmp)):
                self.assertEqual(orchestrator.research_docs(), 'policy = None\n')

    def test_guard_catches_q_learning_terms(self):
        for text in ['Use Q-learning', 'a q table', 'Q(s, a)', 'Bellman backup', 'value iteration',
                     'TD error', 'temporal difference', 'SARSA', 'learning rate 0.1', 'no Qlearning here']:
            self.assertTrue(orchestrator.q_learning_hits(text), text)
        for text in ['raw counts N(s,a)', 'uniform-random policy', 'undiscounted return', 'state (3,3)',
                     'freq-table of visits', 'freq values per state', 'Iraq tables']:
            self.assertFalse(orchestrator.q_learning_hits(text), text)

    def test_parse_report_rejects_wrong_agent(self):
        stdout = json.dumps({orchestrator.RESULT_KEY: report('test-reviewer', 'PASS')})
        with self.assertRaises(ValueError):
            parse_report(stdout, 'researcher')

    def test_parse_report_accepts_string_result(self):
        stdout = json.dumps({orchestrator.RESULT_KEY: json.dumps(report('researcher', 'INFO'))})
        self.assertEqual(parse_report(stdout, 'researcher')['agent'], 'researcher')

    def test_parse_report_accepts_fenced_result(self):
        fenced = '```json\n' + json.dumps(report('researcher', 'INFO')) + '\n```'
        stdout = json.dumps({orchestrator.RESULT_KEY: fenced})
        self.assertEqual(parse_report(stdout, 'researcher')['agent'], 'researcher')

    def test_parse_report_rejects_malformed_finding(self):
        bad = report('researcher', 'INFO')
        bad['findings'][0]['status'] = 'MAYBE'
        with self.assertRaises(ValueError):
            parse_report(json.dumps({orchestrator.RESULT_KEY: bad}), 'researcher')

    def test_parse_report_rejects_missing_findings(self):
        stdout = json.dumps({orchestrator.RESULT_KEY: {'agent': 'researcher'}})
        with self.assertRaises(ValueError):
            parse_report(stdout, 'researcher')

    def test_gate_stop_spawns_nothing_else(self):
        spawn, calls = fake_spawn({'researcher': report('researcher', 'UNKNOWN')})
        with mock.patch.object(orchestrator, 'spawn', spawn):
            reports = orchestrator.pipeline('q')
        self.assertEqual([name for name, _ in calls], ['researcher'])
        self.assertEqual(len(reports), 1)

    def test_q_learning_research_never_reaches_implementer(self):
        research = report('researcher', 'INFO')
        research['findings'][0]['note'] = 'Store a Q-table and apply a Bellman update.'
        spawn, calls = fake_spawn({'researcher': research})
        with mock.patch.object(orchestrator, 'spawn', spawn):
            reports = orchestrator.pipeline('q')
        self.assertEqual([name for name, _ in calls], ['researcher'])
        self.assertEqual(reports[-1]['agent'], orchestrator.GUARD)

    def test_q_learning_in_docs_is_flagged_and_verifier_still_runs(self):
        spawn, calls = fake_spawn({'researcher': report('researcher', 'INFO')})
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'plan.md').write_text('Later: value iteration.')
            with mock.patch.object(orchestrator, 'spawn', spawn), mock.patch.object(orchestrator, 'RESEARCH', Path(tmp)):
                reports = orchestrator.pipeline('q')
        self.assertIn(orchestrator.GUARD, [r['agent'] for r in reports])
        self.assertEqual([name for name, _ in calls], [*PIPELINE, orchestrator.VERIFIER])

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

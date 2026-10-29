"""Strategy 4 checks: sub-agent config is wired correctly, and a learner only needs reset()/step()."""
import re
import unittest
from pathlib import Path
from vacuum.environment import VacuumEnvironment, CHARGER
from orchestrator import AGENTS as SPAWNABLE, build_command

STRATEGY = Path(__file__).resolve().parents[1]
AGENTS = sorted((STRATEGY / '.claude' / 'agents').glob('*.md'))
ALLOWED_TOOLS = {'Read', 'Grep', 'Glob'}


def parse_agent(path):
    _, frontmatter, body = path.read_text().split('---', 2)
    fields = dict(line.split(':', 1) for line in frontmatter.strip().splitlines())
    return {k.strip(): v.strip() for k, v in fields.items()}, body


class AgentView:
    """What a learner is handed: reset() and step(), nothing else."""
    __slots__ = ('reset', 'step')

    def __init__(self, env):
        self.reset = env.reset
        self.step = env.step


class TestOrchestratorConfig(unittest.TestCase):
    def test_agents_exist(self):
        self.assertEqual([p.stem for p in AGENTS], ['environment-reviewer', 'test-reviewer'])

    def test_frontmatter(self):
        for path in AGENTS:
            fields, _ = parse_agent(path)
            self.assertEqual(fields['name'], path.stem)
            self.assertTrue(fields['description'])
            tools = {t.strip() for t in fields['tools'].split(',')}
            self.assertLessEqual(tools, ALLOWED_TOOLS, path.name)

    def test_scoped_paths_exist(self):
        for path in AGENTS:
            _, body = parse_agent(path)
            for ref in re.findall(r'`([^`]*/[^`]*)`', body):
                if ref == f'{STRATEGY.name}/':  # the scope declaration itself
                    continue
                self.assertTrue((STRATEGY / ref).exists(), f'{path.name}: {ref}')

    def test_agents_declare_scope(self):
        for path in AGENTS:
            _, body = parse_agent(path)
            self.assertIn(f'Stay inside `{STRATEGY.name}/`', body, path.name)

    def test_orchestrator_routes_to_each_agent(self):
        memory = (STRATEGY / 'CLAUDE.md').read_text()
        for path in AGENTS:
            self.assertIn(path.stem, memory)

    def test_orchestrator_spawns_each_agent(self):
        self.assertEqual(sorted(SPAWNABLE), [p.stem for p in AGENTS])
        for name, task in SPAWNABLE.items():
            command = build_command(name, task)
            self.assertEqual(command[command.index('--agent') + 1], name)


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

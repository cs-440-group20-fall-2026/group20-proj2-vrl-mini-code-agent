import csv
import tempfile
import unittest
from pathlib import Path

from vacuum.environment import CHARGER, TRAP
from lab_5.q_learning import EpisodeRecord, QLearningConfig
from lab_5.run_experiments import (
    CSV_COLUMNS, classify_outcome, format_policy_grid, main, render_markdown,
    run_experiments, summarize_episodes, write_csv, write_markdown,
)

SMALL_GRID = {'living_reward': [-0.04, -2.0], 'gamma': [0.9], 'alpha': [0.5], 'epsilon': [0.2]}
SMALL_BASE = QLearningConfig(train_episodes=100, eval_episodes=20)


class TestMetrics(unittest.TestCase):
    def test_classify_outcome(self):
        self.assertEqual(classify_outcome(EpisodeRecord(10, 6, True, CHARGER)), 'charger')
        self.assertEqual(classify_outcome(EpisodeRecord(-1, 4, True, TRAP)), 'trap')
        self.assertEqual(classify_outcome(EpisodeRecord(-4, 100, False, (0, 0))), 'timeout')

    def test_summarize_episodes(self):
        records = [EpisodeRecord(10.0, 6, True, CHARGER), EpisodeRecord(9.0, 8, True, CHARGER),
                   EpisodeRecord(-1.0, 4, True, TRAP), EpisodeRecord(-2.0, 50, False, (0, 0))]
        summary = summarize_episodes(records)
        self.assertEqual(summary['charger_success_rate'], 0.5)
        self.assertEqual(summary['trap_rate'], 0.25)
        self.assertEqual(summary['timeout_rate'], 0.25)
        self.assertEqual(summary['mean_reward'], 4.0)
        self.assertEqual(summary['mean_steps'], 17.0)

    def test_summarize_empty(self):
        self.assertEqual(summarize_episodes([])['charger_success_rate'], 0.0)


class TestReportGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.policies = run_experiments(SMALL_GRID, SMALL_BASE, seeds=[0, 1])

    def test_rows_have_all_columns_and_valid_rates(self):
        self.assertEqual(len(self.rows), 2)
        for row in self.rows:
            self.assertEqual(set(CSV_COLUMNS) - set(row), set())
            total = row['charger_success_rate'] + row['trap_rate'] + row['timeout_rate']
            self.assertAlmostEqual(total, 1.0)

    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_csv(self.rows, Path(tmp) / 'nested' / 'results.csv')
            with path.open(newline='', encoding='utf-8') as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, CSV_COLUMNS)
                parsed = list(reader)
        self.assertEqual(len(parsed), 2)
        self.assertAlmostEqual(float(parsed[0]['charger_success_rate']),
                               self.rows[0]['charger_success_rate'], places=4)
        self.assertEqual(parsed[0]['seeds'], '0 1')

    def test_markdown_contains_required_metrics(self):
        text = render_markdown(self.rows, SMALL_BASE, [0, 1], self.policies)
        for heading in ('Charger success', 'Trap rate', 'Mean reward', 'Mean steps',
                        '## Best configuration'):
            self.assertIn(heading, text)
        self.assertEqual(text.count('\n| -'), 2)  # one table row per config
        self.assertIn('reset()', text)

    def test_reports_are_reproducible(self):
        rows_again, policies_again = run_experiments(SMALL_GRID, SMALL_BASE, seeds=[0, 1])
        self.assertEqual(rows_again, self.rows)
        self.assertEqual(render_markdown(rows_again, SMALL_BASE, [0, 1], policies_again),
                         render_markdown(self.rows, SMALL_BASE, [0, 1], self.policies))

    def test_policy_grid_marks_special_cells(self):
        grid = format_policy_grid({(0, 0): 'Right', (0, 1): 'Down'}).splitlines()
        self.assertEqual(len(grid), 4)
        self.assertEqual(grid[0].split()[:2], ['>', 'v'])
        self.assertEqual(grid[1].split()[1], 'X')
        self.assertEqual(grid[3].split()[1], 'T')
        self.assertEqual(grid[3].split()[3], 'C')

    def test_write_markdown_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = write_markdown(self.rows, SMALL_BASE, [0, 1], Path(tmp) / 'r.md')
            self.assertTrue(md.read_text(encoding='utf-8').startswith('# Lab 5'))
            main(['--quick', '--seeds', '0', '--train-episodes', '50',
                  '--eval-episodes', '10', '--output-dir', tmp])
            self.assertTrue((Path(tmp) / 'results.csv').exists())
            self.assertTrue((Path(tmp) / 'report.md').exists())


if __name__ == '__main__':
    unittest.main()

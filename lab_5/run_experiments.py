"""Run seeded Q-learning experiments and write CSV + Markdown reports.

Usage (from the repository root):

    python -m lab_5.run_experiments                 # full grid, 3 seeds
    python -m lab_5.run_experiments --quick         # small grid for a fast check
    python -m lab_5.run_experiments --seeds 0 1 2 3 4 --train-episodes 5000

Outputs ``results.csv`` and ``report.md`` in ``lab_5/reports/`` (or --output-dir).
Outcome labels (charger / trap / timeout) are computed here, by the experiment
harness, from the public CHARGER/TRAP constants. The learner never uses them.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import statistics
from dataclasses import replace
from pathlib import Path

from vacuum.environment import ACTIONS, CHARGER, OBSTACLE, START, TRAP
from lab_5.q_learning import EVALUATION_SEED_OFFSET, QLearningConfig, run_trial

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / 'reports'
GRID_SIZE = 4

FULL_GRID = {
    'living_reward': [0.0, -0.04, -0.4, -2.0, -6.0],
    'gamma': [0.9, 0.99],
    'alpha': [0.1, 0.5],
    'epsilon': [0.1, 0.3],
}
QUICK_GRID = {
    'living_reward': [-0.04, -2.0],
    'gamma': [0.9],
    'alpha': [0.5],
    'epsilon': [0.2],
}

CSV_COLUMNS = [
    'living_reward', 'gamma', 'alpha', 'epsilon', 'seeds', 'train_episodes',
    'eval_episodes', 'charger_success_rate', 'trap_rate', 'timeout_rate',
    'mean_reward', 'mean_steps', 'train_charger_rate',
]
ARROWS = {'Up': '^', 'Right': '>', 'Down': 'v', 'Left': '<'}


def classify_outcome(record):
    """Harness-side label for an episode: 'charger', 'trap', or 'timeout'."""
    if record.terminated and record.final_state == CHARGER:
        return 'charger'
    if record.terminated and record.final_state == TRAP:
        return 'trap'
    return 'timeout'


def summarize_episodes(records):
    """Charger/trap/timeout rates plus mean reward and mean steps."""
    count = len(records)
    if count == 0:
        return {'charger_success_rate': 0.0, 'trap_rate': 0.0, 'timeout_rate': 0.0,
                'mean_reward': 0.0, 'mean_steps': 0.0}
    outcomes = [classify_outcome(record) for record in records]
    return {
        'charger_success_rate': outcomes.count('charger') / count,
        'trap_rate': outcomes.count('trap') / count,
        'timeout_rate': outcomes.count('timeout') / count,
        'mean_reward': statistics.fmean(record.total_reward for record in records),
        'mean_steps': statistics.fmean(record.steps for record in records),
    }


def build_configs(grid, base):
    keys = list(grid)
    for values in itertools.product(*(grid[key] for key in keys)):
        yield replace(base, **dict(zip(keys, values)))


def run_config(config, seeds):
    """Train/evaluate one hyperparameter setting over several seeds; pool results."""
    evaluation, training, trials = [], [], []
    for seed in seeds:
        trial = run_trial(replace(config, seed=seed))
        evaluation.extend(trial.evaluation)
        training.extend(trial.training)
        trials.append(trial)
    row = {
        'living_reward': config.living_reward, 'gamma': config.gamma,
        'alpha': config.alpha, 'epsilon': config.epsilon,
        'seeds': ' '.join(str(seed) for seed in seeds),
        'train_episodes': config.train_episodes, 'eval_episodes': config.eval_episodes,
    }
    row.update(summarize_episodes(evaluation))
    row['train_charger_rate'] = summarize_episodes(training)['charger_success_rate']
    return row, trials


def run_experiments(grid, base, seeds):
    rows, policies = [], []
    for config in build_configs(grid, base):
        row, trials = run_config(config, seeds)
        rows.append(row)
        policies.append(trials[0].agent.greedy_policy())
    return rows, policies


def format_policy_grid(policy):
    """Render a greedy policy as a 4x4 text grid (harness-side display only)."""
    lines = []
    for row in range(GRID_SIZE):
        cells = []
        for col in range(GRID_SIZE):
            cell = (row, col)
            if cell == OBSTACLE:
                cells.append('X')
            elif cell == CHARGER:
                cells.append('C')
            elif cell == TRAP:
                cells.append('T')
            else:
                cells.append(ARROWS.get(policy.get(cell), '.'))
        lines.append(' '.join(cells))
    return '\n'.join(lines)


def best_row_index(rows):
    return max(range(len(rows)),
               key=lambda i: (rows[i]['charger_success_rate'], rows[i]['mean_reward']))


def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row[key]) for key in CSV_COLUMNS})
    return path


def _csv_value(value):
    return f'{value:.4f}' if isinstance(value, float) else value


def render_markdown(rows, base, seeds, policies=None):
    lines = [
        '# Lab 5 Q-Learning Report',
        '',
        'Tabular Q-learning on the 4x4 vacuum environment. The learner interacts only '
        'through `reset()` and `step()`; transition and reward tables are never exposed.',
        '',
        '## Setup',
        '',
        f'- Seeds: {", ".join(str(seed) for seed in seeds)} '
        f'(evaluation environment seed = training seed + {EVALUATION_SEED_OFFSET})',
        f'- Training episodes per seed: {base.train_episodes} (epsilon-greedy, '
        f'decay {base.epsilon_decay}, min {base.min_epsilon})',
        f'- Evaluation episodes per seed: {base.eval_episodes} (greedy, no learning)',
        f'- Max steps per episode: {base.max_steps} (episodes that hit the cap count as timeouts)',
        f'- Intended-move probability (simulator setting): {base.intended_probability}',
        '',
        '## Results (evaluation episodes)',
        '',
        '| Living reward | Gamma | Alpha | Epsilon | Charger success | Trap rate '
        '| Timeout rate | Mean reward | Mean steps |',
        '|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for row in rows:
        lines.append(
            f"| {row['living_reward']:g} | {row['gamma']:g} | {row['alpha']:g} "
            f"| {row['epsilon']:g} | {row['charger_success_rate']:.1%} "
            f"| {row['trap_rate']:.1%} | {row['timeout_rate']:.1%} "
            f"| {row['mean_reward']:.3f} | {row['mean_steps']:.2f} |")
    if rows:
        best = best_row_index(rows)
        row = rows[best]
        lines += [
            '',
            '## Best configuration',
            '',
            f"Living reward {row['living_reward']:g}, gamma {row['gamma']:g}, "
            f"alpha {row['alpha']:g}, epsilon {row['epsilon']:g}: "
            f"{row['charger_success_rate']:.1%} charger success, "
            f"{row['trap_rate']:.1%} trap rate, mean reward {row['mean_reward']:.3f}, "
            f"mean steps {row['mean_steps']:.2f}.",
        ]
        if policies:
            lines += [
                '',
                f'Greedy policy learned with seed {seeds[0]} '
                f'(`^ > v <` = {", ".join(ACTIONS)}; X obstacle, T trap, C charger, '
                f'. unvisited; start {START}):',
                '',
                '```',
                format_policy_grid(policies[best]),
                '```',
            ]
    lines += [
        '',
        '## Notes',
        '',
        '- Success, trap and timeout labels are assigned by the experiment harness, not the learner.',
        '- Compare trap rates across living-reward rows. From the start, the shortest trap '
        'path is 4 moves and the shortest charger path is 6, so (ignoring slips) ending in '
        'the trap only pays off once the living reward drops below about -5.5.',
        '',
    ]
    return '\n'.join(lines)


def write_markdown(rows, base, seeds, path, policies=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(rows, base, seeds, policies), encoding='utf-8')
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Run Lab 5 Q-learning experiments.')
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2])
    parser.add_argument('--train-episodes', type=int, default=2000)
    parser.add_argument('--eval-episodes', type=int, default=500)
    parser.add_argument('--max-steps', type=int, default=100)
    parser.add_argument('--epsilon-decay', type=float, default=1.0)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--quick', action='store_true', help='run a small 2-config grid')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    base = QLearningConfig(train_episodes=args.train_episodes,
                           eval_episodes=args.eval_episodes,
                           max_steps=args.max_steps, epsilon_decay=args.epsilon_decay)
    grid = QUICK_GRID if args.quick else FULL_GRID
    rows, policies = run_experiments(grid, base, args.seeds)
    csv_path = write_csv(rows, args.output_dir / 'results.csv')
    md_path = write_markdown(rows, base, args.seeds, args.output_dir / 'report.md', policies)
    print(f'Wrote {csv_path}')
    print(f'Wrote {md_path}')
    return rows


if __name__ == '__main__':
    main()

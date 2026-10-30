"""Strategy 4 spawn point: runs each sub-agent in its own Claude Code process (fresh context, no shared history).

Run from strategy_4/:  python orchestrator.py [agent ...]
"""
import argparse
import subprocess
from pathlib import Path

STRATEGY = Path(__file__).resolve().parent
VACUUM = STRATEGY.parent / 'vacuum'  # only directory allowed outside strategy_4/ (read-only)

# agent name -> the only task it receives
AGENTS = {
    'environment-reviewer': 'Check grid, terminal-state rules, and that no agent is handed T or R tables.',
    'test-reviewer': 'Check tests/ for missing edge cases and nondeterministic assertions.',
}


def build_command(name, task):
    return [
        'claude',
        '--print',
        task,
        '--agent',
        name,
        '--add-dir',
        str(VACUUM)
    ]


def spawn(name, task):
    command = build_command(name, task)

    print(f"\nLaunching: {name}", flush=True)

    result = subprocess.run(
        command,
        cwd=STRATEGY,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False
    )

    if result.returncode != 0:
        print(f"\nAgent '{name}' failed.")
        print(f"Exit code: {result.returncode}")
        print(f"STDERR:\n{result.stderr}")
        print(f"STDOUT:\n{result.stdout}")

        raise RuntimeError(
            f"Claude Code agent '{name}' failed."
        )

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('agents', nargs='*', help=f'default: all ({", ".join(AGENTS)})')
    names = parser.parse_args().agents or list(AGENTS)
    unknown = set(names) - set(AGENTS)
    if unknown:
        parser.error(f'unknown agent(s): {", ".join(sorted(unknown))}')
    for name in names:
        print(f'## {name}\n{spawn(name, AGENTS[name])}\n')


if __name__ == '__main__':
    main()

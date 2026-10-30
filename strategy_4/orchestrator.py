"""Strategy 4 spawn point: runs each sub-agent in its own Claude Code process (fresh context, no shared history).

Run from strategy_4/:
  python orchestrator.py                      review with every reviewer
  python orchestrator.py review [agent ...]   review with the named reviewers
  python orchestrator.py pipeline "question"  researcher -> research-implementer -> research-verifier
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

STRATEGY = Path(__file__).resolve().parent
VACUUM = STRATEGY.parent / 'vacuum'  # only directory allowed outside strategy_4/ (read-only)
CONSTRAINTS = STRATEGY / '.claude' / 'constraints.md'  # shared rules, prepended to every task
SCHEMA = STRATEGY / '.claude' / 'agents' / 'report.schema.json'  # shared output contract
RESEARCH = STRATEGY / 'context' / 'research'  # the only place the implementer may write

# reviewer name -> the only task it receives
REVIEWERS = {
    'environment-reviewer': 'Check grid, terminal-state rules, and that no learner is handed T or R tables.',
    'test-reviewer': 'Check tests/ for missing edge cases and nondeterministic assertions.',
}
# pipeline agents get their task from the question, then from the researcher's brief
PIPELINE = ('researcher', 'research-implementer')
VERIFIER = 'research-verifier'  # always runs after the implementer; its tests are defined in context/testing.md
VERIFY_TASK = 'Review context/research/ docs against the environment and shared constraints, '\
              'then run the research verification tests defined in context/testing.md.'

# extra CLI flags per agent; editors and the verifier get an allowlist, everyone else stays read-only
FLAGS = {
    'research-implementer': ['--allowedTools', 'Edit(context/research/**)'],
    VERIFIER: ['--allowedTools', 'Bash(python3 -m unittest *)'],
}

STATUSES = ('PASS', 'FAIL', 'UNKNOWN', 'INFO')
BLOCKING = {'FAIL'}  # a FAIL stops the pipeline; UNKNOWN rows travel on as open questions

# Q-learning is a later lab: these terms may not appear in research findings or research docs, even negated
FORBIDDEN = re.compile(
    r'\bq[- ]?learning|\bq[- ]?tables?|\bq[- ]?values?|\bq\s*\(\s*s|bellman|value[- ]iteration|policy[- ]iteration'
    r'|temporal[- ]difference|\btd\s*(?:\(|error|target|update)|\bsarsa\b|learning[- ]rate',
    re.IGNORECASE)
GUARD = 'q-learning-guard'  # label for the orchestrator's own (non-LLM) findings
RESULT_KEY = 'result'  # confirmed on the first real run: the report arrives as a (possibly fenced) string


def build_command(name):
    # the prompt goes over stdin: --add-dir and --allowedTools are variadic and would swallow it
    return ['claude', '-p', '--agent', name, '--add-dir', str(VACUUM), *FLAGS.get(name, []),
            '--output-format', 'json', '--json-schema', SCHEMA.read_text()]


def build_prompt(task):
    # the schema itself goes in the prompt: agents improvise key names when they only see its path
    return (f'{CONSTRAINTS.read_text()}\n## Output schema\n```json\n{SCHEMA.read_text()}```\n'
            'Use exactly these keys; `evidence` is one string, not a list.\n'
            f'\n## Task\n{task}\n')


def spawn(name, task):
    # cwd=strategy_4 so Claude Code finds .claude/agents; PYTHONPATH lets tests import ../vacuum
    env = {**os.environ, 'PYTHONPATH': str(STRATEGY.parent)}
    result = subprocess.run(build_command(name), input=build_prompt(task), cwd=STRATEGY, env=env,
                            capture_output=True, text=True, check=True)
    return result.stdout


def parse_report(stdout, name):
    report = json.loads(stdout)[RESULT_KEY]
    if isinstance(report, str):
        # agents may wrap the JSON in a ```json fence; keep only the outermost object
        report = json.loads(report[report.index('{'):report.rindex('}') + 1])
    # --json-schema isn't enforced on this path, so check the shape here
    if report.get('agent') != name:
        raise ValueError(f'expected a report from {name}, got {report.get("agent")}')
    if not isinstance(report.get('findings'), list):
        raise ValueError(f'{name}: report has no findings list')
    for finding in report['findings']:
        if set(finding) != {'status', 'evidence', 'note'} or finding['status'] not in STATUSES:
            raise ValueError(f'{name}: malformed finding {finding}')
    return report


def run(name, task):
    return parse_report(spawn(name, task), name)


def gate(report):
    statuses = {f['status'] for f in report['findings']}
    return 'INFO' in statuses and not statuses & BLOCKING


def build_brief(question, report):
    # only INFO and UNKNOWN rows cross over; the researcher's context never reaches the implementer
    def rows(status):
        return [f'- {f["note"]} ({f["evidence"]})' for f in report['findings'] if f['status'] == status]
    brief = f'Implement this brief in context/research/.\nQuestion: {question}\n' + '\n'.join(rows('INFO'))
    if questions := rows('UNKNOWN'):
        brief += '\n\nOpen questions (record them as open; do not answer them):\n' + '\n'.join(questions)
    return brief


def q_learning_hits(text):
    return sorted({m.group(0).lower() for m in FORBIDDEN.finditer(text)})


def guard(evidence, text):
    # deterministic Q-learning check: returns a FAIL report, or None when the text is clean
    hits = q_learning_hits(text)
    if not hits:
        return None
    return {'agent': GUARD, 'findings': [{'status': 'FAIL', 'evidence': evidence,
                                          'note': f'Q-learning terms are forbidden in this lab: {", ".join(hits)}'}]}


def research_docs():
    return '\n'.join(p.read_text() for p in sorted(RESEARCH.rglob('*')) if p.is_file())


def pipeline(question):
    research = run('researcher', question)
    blocked = guard('researcher findings', '\n'.join(f['note'] for f in research['findings']))
    if blocked:
        return [research, blocked]
    if not gate(research):
        return [research]
    reports = [research, run('research-implementer', build_brief(question, research))]
    if leaked := guard('context/research/', research_docs()):
        reports.append(leaked)
    return reports + [run(VERIFIER, VERIFY_TASK)]


def print_tally(reports):
    for report in reports:
        counts = {s: 0 for s in STATUSES}
        for finding in report['findings']:
            counts[finding['status']] += 1
        print(f'## {report["agent"]}: ' + ' / '.join(f'{n} {s}' for s, n in counts.items()))
        for finding in report['findings']:
            if finding['status'] != 'PASS':
                print(f'- {finding["status"]} {finding["evidence"]}: {finding["note"]}')
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command')  # optional: no subcommand = review with every reviewer
    review = commands.add_parser('review', help='run reviewers (default: all)')
    review.add_argument('agents', nargs='*', help=f'default: all ({", ".join(REVIEWERS)})')
    pipe = commands.add_parser('pipeline', help='researcher -> research-implementer -> research-verifier')
    pipe.add_argument('question')
    args = parser.parse_args()

    if args.command == 'pipeline':
        reports = pipeline(args.question)
    else:
        names = getattr(args, 'agents', None) or list(REVIEWERS)
        unknown = set(names) - set(REVIEWERS)
        if unknown:
            review.error(f'unknown reviewer(s): {", ".join(sorted(unknown))}')
        reports = [run(name, REVIEWERS[name]) for name in names]
    print_tally(reports)


if __name__ == '__main__':
    main()

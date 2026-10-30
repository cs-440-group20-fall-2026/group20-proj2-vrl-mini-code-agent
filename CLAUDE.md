# Project Memory - Vacuum Robot Reinforcement Learning Lab

## Goal
Maintain a 4x4 vacuum robot simulator that exposes observations and feedback but does not provide transition or reward tables to the agent. Q-learning is reserved for a later lab.

## Environment
Start (0,0); obstacle X (1,1); trap -1 (3,1); charger +10 (3,3). Four cardinal actions. The simulator may use hidden stochastic transitions; do not let an agent inspect simulator internals.

## Coding rules
- Python standard library only; use descriptive names and deterministic seeds in tests.
- Keep environment behavior separate from agent policy.
- Test boundaries, obstacle, terminal states, and repeatability.
- Never claim the scripted demonstration is Q-learning.
- Do not add a Q-learning implementation unless a later assignment requests it.

## Context loading
Consult `.claude/context/environment.md` for environment changes and `.claude/context/testing.md` for test changes. Read only the task-relevant file.

## Delegation
For strategy 4, use `.claude/agents/environment-reviewer.md` and `.claude/agents/test-reviewer.md`. Delegate focused reviews and return concise findings, not full conversation history.

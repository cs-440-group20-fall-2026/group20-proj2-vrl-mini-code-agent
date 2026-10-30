# Strategy 1 - Persistent Memory Architecture

## Role & Objective
You are the primary assistant operating under a persistent memory architecture. Maintain project consistency, architecture standards, and code quality by leveraging hierarchical memory tiers and dynamic context imports.

## Scope & Boundaries
- Work only inside this directory (`strategy_1/`); its subdirectories (`context/`, `testing/`) are included.
- Paths are relative to `strategy_1/`.
- Only exception: `../vacuum/` may be read and imported, never edited.
- Do not read or edit anything else outside `strategy_1/`.

## Memory Architecture & Hierarchy
- **Project Memory (`strategy_1/CLAUDE.md`):** Base architecture, coding standards, and business rules shared via version control.
- **User Memory (`~/.claude/CLAUDE.md`):** Personal user preferences and shortcuts (ignored by version control; local to user sessions).
- **Dynamic Imports (`context/`):** Specialized files loaded on-demand to keep active token windows clean.

## Dynamic Imports (Active Context)
Consult the following context files when executing tasks:
- `@context/environment.md` — Grid coordinates, boundaries, blocking rules, and terminal states.
- `@context/testing.md` — Test suite execution guidelines and multi-run performance benchmark rules.

## Execution Rules
- **Context Before Action:** Check relevant context files before modifying code components or running test suites.
- **Performance Tracking:** Ensure testing scripts added to `testing/` include multi-run performance metrics (e.g., success rates and multi-episode reward tracking).
- **Integrity:** Keep baseline assertions intact unless explicitly directed by task requirements. Do not implement Q-learning.

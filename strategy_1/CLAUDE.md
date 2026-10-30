# Strategy 1 - Persistent Memory Architecture

## Role & Objective
You are the primary agent operating under a persistent memory architecture. Maintain project consistency, architecture standards, and code quality by leveraging hierarchical memory tiers and dynamic context imports.

## Scope & Boundaries
- Work primarily within the project memory structure (`strategy_1/` and its subdirectories).
- **Project Memory:** `strategy_1/CLAUDE.md` defines base instructions and architecture shared via version control.
- **User Memory:** Local configurations and shortcuts are handled outside version control and apply globally/locally to user sessions.
- **Dynamic Imports:** Context files in `strategy_1/context/` are loaded on-demand based on environment triggers or query requirements.

## Memory Hierarchy & Loading
### Always Active:
Project instructions, core coding standards, and error-handling patterns defined in project-level memory.

### On-Demand Loading:
- Reference `strategy_1/context/environment.md` for build, path, and tooling rules. 
- Reference `strategy_1/context/testing.md` for test suite execution and multi-run performance benchmark rules.

## Execution Rules
- **Context Before Action:** Check relevant context files before modifying code components or running test suites.
- **Performance Tracking:** Ensure any testing scripts added to `strategy_1/tests/` include multi-run performance metrics (e.g., latency and execution time tracking).
- **Integrity:** Keep baseline assertions intact unless explicitly directed by task requirements.

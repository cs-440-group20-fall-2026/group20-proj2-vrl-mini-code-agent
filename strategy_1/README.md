# Strategy 1 - Write (Persistent Memory Architecture)

Source: CS440 Agentic AI Context Engineering slides

The repository's root `CLAUDE.md` is project-level persistent memory, version-controlled and available across sessions. It stores architecture, coding standards, and constraints. Focused files under `.claude/context/` store additional details that can be read when relevant. This mirrors the lecture's project memory plus dynamic imports. User-level memory (`~/.claude/CLAUDE.md`) is intentionally not commited because it is personal to each developer.

## Demonstration
1. Open this repositroy in Claude Code.
2. Ask: "Read CLAUDE.md and explain the vacuum environment constraints."
3. Ask: "Review boundary handling using the environment context file; do not add Q-learning."
4. Show that the assistant can use the same project rules across tasks without repeating the original prompt.

This is file-based persistent context; no automatic context-switcher hook is configured. Task-relevant context files are referenced from CLAUDE.md and can be read on demand.

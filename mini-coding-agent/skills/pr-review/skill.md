---
name: pr-review
description: Review a pull request or branch diff for bugs, broken project rules, and missing tests, then report findings without editing code. Use when asked to review a PR, code review changes, or check what changed on a branch.
keywords: pull request, PR, code review, diff, branch, changes, findings
---

# PR Review

Review the current branch's changes against `main` and report findings. This skill is
read-only: do not call `write_file` or `patch_file`, and do not commit, push, or merge.

## Steps
1. **Find the change set.** Run:
   ```bash
   git diff --stat main...HEAD
   git log --oneline main..HEAD
   ```
   If the diff is empty, say so and stop.
2. **Read the project rules** in `CLAUDE.md` at the repository root before judging the code.
3. **Read each changed file** with `read_file`, focusing on the changed lines
   (`git diff main...HEAD -- <path>` shows them).
4. **Check for:**
   - correctness bugs: wrong conditions, off-by-one errors, unhandled empty input, exceptions that escape;
   - broken project rules from `CLAUDE.md` (e.g. third-party imports, an agent reading simulator internals,
     Q-learning code outside `lab_5/`);
   - new behavior without a test, or tests that cannot fail;
   - docs (`README.md`, `spec.md`) that no longer match the code.
5. **Run the tests** that cover the changed files and quote any failure verbatim.
6. **Report** at most 10 findings, most severe first, each as
   `path:line - problem - why it matters`. If there are none, say "No findings" and list what you checked.
   Do not invent findings to fill the list.

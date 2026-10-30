# Environment Context (environment-reviewer)

## Scope
Scope: `strategy_4/` and its subdirectories only; paths are relative to it.
Only exception: `../vacuum/environment.py` is read-only.

## Grid
Grid coordinates are (row, column), zero-indexed.
Start (0,0), X (1,1), trap (3,1), charger (3,3).

## Moves and episodes
Invalid moves stay in place.
Reaching trap or charger terminates the episode.

## What the learner may see
The simulator holds movement probabilities and reward rules privately.
An eventual learner should interact via `reset()` and `step()` rather than access them.

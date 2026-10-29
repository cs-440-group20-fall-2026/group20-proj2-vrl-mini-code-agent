# Environment Context (environment-reviewer)
Scope: `strategy_4/` and its subdirectories only; paths are relative to it.
Only exception: `../vacuum/environment.py` is read-only.

Grid coordinates are (row, column), zero-indexed.
Start (0,0), X (1,1), trap (3,1), charger (3,3).
Invalid moves stay in place.
Reaching trap or charger terminates the episode.
The simulator holds movement probabilities and reward rules privately; an eventual learner should interact via reset()/step() rather than access them.

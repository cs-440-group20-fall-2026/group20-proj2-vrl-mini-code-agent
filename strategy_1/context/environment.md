# Environment Context

## Scope
- **Scope:** `strategy_1/` and its subdirectories only; paths are relative to it.
- **Read-only Exception:** `../vacuum/environment.py` may be imported and read, but never edited.

## Grid Layout
- Grid coordinates are `(row, column)`, zero-indexed (`4x4` grid layout).
- **Start:** `(0,0)`
- **Obstacle (`X`):** `(1,1)` — impassable; blocks movement.
- **Trap (`-1`):** `(3,1)` — terminal state.
- **Charging Station (`10`):** `(3,3)` — terminal state / goal.

## Moves and Episodes
- **Actions:** Up, Right, Down, Left.
- **Boundary & Obstacle Handling:** Invalid moves (hitting grid boundaries or obstacles) cause the agent to stay in its current place.
- **Episode Termination:** Reaching the trap or the charging station terminates the episode.

## Model Separation & Observability
- The simulator holds movement probabilities ($T$) and reward rules ($R$) privately. 
- Future learning agents must interact exclusively through standard `reset()` and `step()` interfaces rather than directly inspecting internal simulator tables.

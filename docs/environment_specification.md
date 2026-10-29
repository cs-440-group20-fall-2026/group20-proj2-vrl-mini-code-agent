# Environment Specification

```
S  0  0  0
0  X  0  0
0  0  0  0
0 -1  0 10
```

- Start: (0,0)
- Obstacle: (1,1); cannot enter
- Trap: (3,1); terminal
- Charging station: (3,3); terminal
- Actions: Up, Right, Down, Left

The lab states that T and R are not known to the learner. The simulator therefore privately samples outcomes and returns observed next state, reward, and terminal flag. For a runnable demonstration, this starter simulator **assumes** the previous lab's 80% intended/10% sideways movement model, living reward -0.04, charger +10, trap -1. These assumptions are not specified by the new lab; change them if your instructor gives new rules. The eventual Q-learning agent should not read these internals. 

No Q-learning implementation is included in this submission.

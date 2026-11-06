# Lab 5 Q-Learning Report

Tabular Q-learning on the 4x4 vacuum environment. The learner interacts only through `reset()` and `step()`; transition and reward tables are never exposed.

## Setup

- Seeds: 0, 1, 2 (evaluation environment seed = training seed + 10000)
- Training episodes per seed: 2000 (epsilon-greedy, decay 1.0, min 0.01)
- Evaluation episodes per seed: 500 (greedy, no learning)
- Max steps per episode: 100 (episodes that hit the cap count as timeouts)
- Intended-move probability (simulator setting): 0.8

## Results (evaluation episodes)

| Living reward | Gamma | Alpha | Epsilon | Charger success | Trap rate | Timeout rate | Mean reward | Mean steps |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.9 | 0.1 | 0.1 | 94.9% | 5.1% | 0.0% | 9.443 | 8.12 |
| 0 | 0.9 | 0.1 | 0.3 | 98.4% | 1.6% | 0.0% | 9.824 | 7.58 |
| 0 | 0.9 | 0.5 | 0.1 | 98.9% | 1.1% | 0.0% | 9.883 | 11.38 |
| 0 | 0.9 | 0.5 | 0.3 | 98.1% | 1.9% | 0.0% | 9.787 | 11.89 |
| 0 | 0.99 | 0.1 | 0.1 | 94.9% | 5.1% | 0.0% | 9.443 | 8.12 |
| 0 | 0.99 | 0.1 | 0.3 | 99.9% | 0.1% | 0.0% | 9.993 | 8.23 |
| 0 | 0.99 | 0.5 | 0.1 | 99.9% | 0.1% | 0.0% | 9.985 | 11.00 |
| 0 | 0.99 | 0.5 | 0.3 | 99.8% | 0.2% | 0.0% | 9.978 | 8.61 |
| -0.04 | 0.9 | 0.1 | 0.1 | 94.5% | 5.5% | 0.0% | 9.117 | 7.85 |
| -0.04 | 0.9 | 0.1 | 0.3 | 98.7% | 1.3% | 0.0% | 9.598 | 7.56 |
| -0.04 | 0.9 | 0.5 | 0.1 | 98.5% | 1.5% | 0.0% | 9.569 | 7.74 |
| -0.04 | 0.9 | 0.5 | 0.3 | 95.5% | 4.5% | 0.0% | 9.203 | 8.65 |
| -0.04 | 0.99 | 0.1 | 0.1 | 99.4% | 0.6% | 0.0% | 9.658 | 7.89 |
| -0.04 | 0.99 | 0.1 | 0.3 | 100.0% | 0.0% | 0.0% | 9.727 | 7.82 |
| -0.04 | 0.99 | 0.5 | 0.1 | 100.0% | 0.0% | 0.0% | 9.713 | 8.16 |
| -0.04 | 0.99 | 0.5 | 0.3 | 100.0% | 0.0% | 0.0% | 9.712 | 8.20 |
| -0.4 | 0.9 | 0.1 | 0.1 | 98.4% | 1.6% | 0.0% | 7.219 | 7.51 |
| -0.4 | 0.9 | 0.1 | 0.3 | 97.9% | 2.1% | 0.0% | 7.174 | 7.50 |
| -0.4 | 0.9 | 0.5 | 0.1 | 100.0% | 0.0% | 0.0% | 7.228 | 7.93 |
| -0.4 | 0.9 | 0.5 | 0.3 | 98.6% | 1.4% | 0.0% | 6.978 | 8.17 |
| -0.4 | 0.99 | 0.1 | 0.1 | 98.9% | 1.1% | 0.0% | 7.130 | 7.88 |
| -0.4 | 0.99 | 0.1 | 0.3 | 100.0% | 0.0% | 0.0% | 7.269 | 7.83 |
| -0.4 | 0.99 | 0.5 | 0.1 | 99.7% | 0.3% | 0.0% | 7.267 | 7.76 |
| -0.4 | 0.99 | 0.5 | 0.3 | 99.5% | 0.5% | 0.0% | 7.206 | 7.84 |
| -2 | 0.9 | 0.1 | 0.1 | 92.7% | 7.3% | 0.0% | -3.260 | 7.23 |
| -2 | 0.9 | 0.1 | 0.3 | 97.5% | 2.5% | 0.0% | -3.269 | 7.50 |
| -2 | 0.9 | 0.5 | 0.1 | 93.5% | 6.5% | 0.0% | -3.644 | 7.46 |
| -2 | 0.9 | 0.5 | 0.3 | 94.9% | 5.1% | 0.0% | -9.151 | 10.29 |
| -2 | 0.99 | 0.1 | 0.1 | 91.6% | 8.4% | 0.0% | -3.489 | 7.28 |
| -2 | 0.99 | 0.1 | 0.3 | 97.6% | 2.4% | 0.0% | -3.311 | 7.52 |
| -2 | 0.99 | 0.5 | 0.1 | 98.2% | 1.8% | 0.0% | -3.345 | 7.57 |
| -2 | 0.99 | 0.5 | 0.3 | 97.6% | 2.4% | 0.0% | -3.281 | 7.51 |
| -6 | 0.9 | 0.1 | 0.1 | 10.2% | 89.8% | 0.0% | -24.830 | 5.16 |
| -6 | 0.9 | 0.1 | 0.3 | 18.4% | 81.6% | 0.0% | -25.084 | 5.35 |
| -6 | 0.9 | 0.5 | 0.1 | 38.9% | 61.1% | 0.0% | -26.241 | 5.92 |
| -6 | 0.9 | 0.5 | 0.3 | 17.1% | 82.9% | 0.0% | -24.887 | 5.30 |
| -6 | 0.99 | 0.1 | 0.1 | 16.2% | 83.8% | 0.0% | -25.162 | 5.32 |
| -6 | 0.99 | 0.1 | 0.3 | 12.2% | 87.8% | 0.0% | -25.066 | 5.23 |
| -6 | 0.99 | 0.5 | 0.1 | 12.8% | 87.2% | 0.0% | -24.968 | 5.23 |
| -6 | 0.99 | 0.5 | 0.3 | 43.3% | 56.7% | 0.0% | -26.461 | 6.04 |

## Best configuration

Living reward -0.04, gamma 0.99, alpha 0.1, epsilon 0.3: 100.0% charger success, 0.0% trap rate, mean reward 9.727, mean steps 7.82.

Greedy policy learned with seed 0 (`^ > v <` = Up, Right, Down, Left; X obstacle, T trap, C charger, . unvisited; start (0, 0)):

```
> > v v
^ X v v
> ^ > v
^ T > C
```

## Notes

- Success, trap and timeout labels are assigned by the experiment harness, not the learner.
- Compare trap rates across living-reward rows. From the start, the shortest trap path is 4 moves and the shortest charger path is 6, so (ignoring slips) ending in the trap only pays off once the living reward drops below about -5.5.

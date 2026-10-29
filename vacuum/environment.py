"""4x4 vacuum rechard environment. Agent observes outcomes, not T or R tables.."""
from dataclasses import dataclass
import random

GRID = ((0,0,0,0), (0,'X',0,0), (0,0,0,0),(0,-1,0,10))
START = (0,0)
CHARGER = (3,3)
TRAP = (3,1)
OBSTACLE = (1,1)
ACTIONS = ('Up', 'Right', 'Down', 'Left')
DELTAS = {'Up': (-1,0), 'Right': (0,1), 'Down': (1,0), 'Left': (0, -1)}

@dataclass(frozen=True)
class StepResult:
    state: tuple[int, int]
    reward: float
    terminated: bool
    actual_action: str

class VacuumEnvironment:
    """A simulator with private movement/reward rules; no agent-facing model API."""
    def __init__(self, seed=42, intended_probability=0.8, living_reward=-0.04):
        if not 0 <= intended_probability <= 1:
            raise ValueError('intended_probability must be between 0 and 1')
        self._rng = random.Random(seed)
        self._intended_probability = intended_probability
        self._living_reward = living_reward
        self.reset()

    def reset(self):
        self.state = START
        self.terminated = False
        return self.state

    def step(self, action):
        if action not in ACTIONS:
            raise ValueError(f'Unknown action: {action}')
        if self.terminated:
            raise RuntimeError('Episode ended; call reset() before stepping')
        index = ACTIONS.index(action)
        side_probability = (1 - self._intended_probability) / 2
        actual = self._rng.choices(
            [action, ACTIONS[(index - 1) % 4], ACTIONS[(index + 1) % 4]],
            weights=[self._intended_probability, side_probability, side_probability], k=1
        )[0]
        dr, dc = DELTAS[actual]
        row, col = self.state[0] + dr, self.state[1] + dc
        if 0 <= row < 4 and 0 <= col < 4 and GRID[row][col] != 'X':
            self.state = (row, col)
        self.terminated = self.state in (CHARGER, TRAP)
        reward = 10.0 if self.state == CHARGER else -1.0 if self.state == TRAP else self._living_reward
        return StepResult(self.state, reward, self.terminated, actual)

    def render(self):
        for row in range(4):
            print(' '.join('V' if (row, col) == self.state else
                            'S' if (row, col) == START else
                            str(GRID[row][col]) for col in range(4)))

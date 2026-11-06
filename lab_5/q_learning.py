"""Model-free tabular Q-learning for the vacuum robot (CS440 Lab 5).

The learner never sees the simulator's transition probabilities or reward
rules. It only calls ``env.reset()`` and ``env.step(action)`` and learns from
the observed ``(next_state, reward, terminated)`` feedback.

Update rule (Watkins Q-learning):

    target = r                                   if the next state is terminal
    target = r + gamma * max_a' Q(s', a')        otherwise
    Q(s, a) <- Q(s, a) + alpha * (target - Q(s, a))
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from vacuum.environment import ACTIONS, VacuumEnvironment

# Offset that keeps evaluation episodes on a different random stream than training.
EVALUATION_SEED_OFFSET = 10_000


@dataclass(frozen=True)
class QLearningConfig:
    """Hyperparameters for one Q-learning trial."""

    alpha: float = 0.1               # learning rate
    gamma: float = 0.9               # discount factor
    epsilon: float = 0.2             # exploration rate for epsilon-greedy
    epsilon_decay: float = 1.0       # multiplicative decay per episode (1.0 = constant)
    min_epsilon: float = 0.01
    living_reward: float = -0.04     # passed to the environment's public constructor
    intended_probability: float = 0.8
    train_episodes: int = 2000
    eval_episodes: int = 500
    max_steps: int = 100             # cap so a looping policy cannot run forever
    seed: int = 0

    def __post_init__(self):
        if not 0 < self.alpha <= 1:
            raise ValueError('alpha must be in (0, 1]')
        if not 0 <= self.gamma <= 1:
            raise ValueError('gamma must be in [0, 1]')
        if not 0 <= self.epsilon <= 1:
            raise ValueError('epsilon must be in [0, 1]')
        if not 0 < self.epsilon_decay <= 1:
            raise ValueError('epsilon_decay must be in (0, 1]')
        if self.max_steps < 1 or self.train_episodes < 0 or self.eval_episodes < 0:
            raise ValueError('episode counts must be non-negative and max_steps >= 1')


@dataclass(frozen=True)
class EpisodeRecord:
    """What happened in one episode, as observed through step() feedback."""

    total_reward: float
    steps: int
    terminated: bool
    final_state: tuple


class QLearningAgent:
    """Tabular Q-learning agent. Holds only its own Q-table, never the model."""

    def __init__(self, alpha, gamma, epsilon, actions=ACTIONS, seed=0, initial_value=0.0):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.actions = tuple(actions)
        self.initial_value = initial_value
        self._rng = random.Random(seed)
        self.q_table: dict[tuple, dict[str, float]] = {}

    def q_values(self, state):
        """Return (creating lazily) the action-value row for a state."""
        if state not in self.q_table:
            self.q_table[state] = {action: self.initial_value for action in self.actions}
        return self.q_table[state]

    def best_value(self, state):
        return max(self.q_values(state).values())

    def greedy_action(self, state):
        """Highest-valued action; ties broken randomly with the seeded RNG."""
        row = self.q_values(state)
        best = max(row.values())
        candidates = [action for action in self.actions if row[action] == best]
        return self._rng.choice(candidates)

    def choose_action(self, state, explore=True):
        """Epsilon-greedy action selection; ``explore=False`` is purely greedy."""
        if explore and self._rng.random() < self.epsilon:
            return self._rng.choice(self.actions)
        return self.greedy_action(state)

    def update(self, state, action, reward, next_state, terminated):
        """Apply one Q-learning update and return the TD error."""
        target = reward if terminated else reward + self.gamma * self.best_value(next_state)
        row = self.q_values(state)
        td_error = target - row[action]
        row[action] += self.alpha * td_error
        return td_error

    def greedy_policy(self):
        """Deterministic greedy policy over visited states (ties -> first in ACTIONS)."""
        policy = {}
        for state, row in self.q_table.items():
            best = max(row.values())
            policy[state] = next(action for action in self.actions if row[action] == best)
        return policy


def run_episode(agent, env, max_steps, learn, explore):
    """Run one episode using only env.reset() and env.step()."""
    state = env.reset()
    total_reward = 0.0
    terminated = False
    steps = 0
    while steps < max_steps and not terminated:
        action = agent.choose_action(state, explore=explore)
        result = env.step(action)
        if learn:
            agent.update(state, action, result.reward, result.state, result.terminated)
        total_reward += result.reward
        state = result.state
        terminated = result.terminated
        steps += 1
    return EpisodeRecord(total_reward, steps, terminated, state)


def train(agent, env, episodes, max_steps, epsilon_decay=1.0, min_epsilon=0.0):
    """Train with epsilon-greedy exploration; returns per-episode records."""
    records = []
    for _ in range(episodes):
        records.append(run_episode(agent, env, max_steps, learn=True, explore=True))
        agent.epsilon = max(min_epsilon, agent.epsilon * epsilon_decay)
    return records


def evaluate(agent, env, episodes, max_steps):
    """Run greedy episodes without learning; the Q-table is not modified."""
    return [run_episode(agent, env, max_steps, learn=False, explore=False)
            for _ in range(episodes)]


@dataclass
class TrialResult:
    config: QLearningConfig
    agent: QLearningAgent
    training: list = field(default_factory=list)
    evaluation: list = field(default_factory=list)


def run_trial(config: QLearningConfig) -> TrialResult:
    """Seeded training on one environment, then evaluation on a separate one."""
    train_env = VacuumEnvironment(seed=config.seed,
                                  intended_probability=config.intended_probability,
                                  living_reward=config.living_reward)
    eval_env = VacuumEnvironment(seed=config.seed + EVALUATION_SEED_OFFSET,
                                 intended_probability=config.intended_probability,
                                 living_reward=config.living_reward)
    agent = QLearningAgent(config.alpha, config.gamma, config.epsilon, seed=config.seed)
    training = train(agent, train_env, config.train_episodes, config.max_steps,
                     config.epsilon_decay, config.min_epsilon)
    evaluation = evaluate(agent, eval_env, config.eval_episodes, config.max_steps)
    return TrialResult(config, agent, training, evaluation)

import unittest

from vacuum.environment import ACTIONS, CHARGER, StepResult, VacuumEnvironment
from lab_5.q_learning import (
    QLearningAgent, QLearningConfig, evaluate, run_episode, run_trial, train,
)


class ResetStepOnlyEnvironment:
    """Fake env exposing only reset()/step(); any other attribute access fails.

    Walks a 1-D corridor 0 -> 1 -> 2 where state 2 is terminal with reward +1.
    """

    def __init__(self):
        self._position = 0

    def reset(self):
        self._position = 0
        return self._position

    def step(self, action):
        if action == 'Right':
            self._position += 1
        terminated = self._position >= 2
        reward = 1.0 if terminated else -0.1
        return StepResult(self._position, reward, terminated, action)

    def __getattr__(self, name):
        raise AssertionError(f'learner accessed simulator attribute {name!r}')


class TestQLearningUpdate(unittest.TestCase):
    def test_nonterminal_update_bootstraps_from_next_state(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.0)
        agent.q_values('next')['Up'] = 2.0
        td_error = agent.update('s', 'Right', -0.04, 'next', terminated=False)
        expected_target = -0.04 + 0.9 * 2.0
        self.assertAlmostEqual(td_error, expected_target)
        self.assertAlmostEqual(agent.q_table['s']['Right'], 0.5 * expected_target)

    def test_repeated_updates_converge_toward_target(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.0)
        for _ in range(60):
            agent.update('s', 'Down', 10.0, CHARGER, terminated=True)
        self.assertAlmostEqual(agent.q_table['s']['Down'], 10.0, places=6)

    def test_other_actions_unchanged(self):
        agent = QLearningAgent(alpha=0.3, gamma=0.9, epsilon=0.0)
        agent.update('s', 'Left', 1.0, 'n', terminated=False)
        for action in ACTIONS:
            if action != 'Left':
                self.assertEqual(agent.q_table['s'][action], 0.0)


class TestTerminalHandling(unittest.TestCase):
    def test_terminal_update_ignores_next_state_values(self):
        agent = QLearningAgent(alpha=1.0, gamma=0.9, epsilon=0.0)
        agent.q_values(CHARGER)['Up'] = 100.0  # must not be bootstrapped
        agent.update((2, 3), 'Down', 10.0, CHARGER, terminated=True)
        self.assertEqual(agent.q_table[(2, 3)]['Down'], 10.0)

    def test_episode_stops_at_terminal_state(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.0, seed=1)
        for action in ACTIONS:
            agent.q_values(0)[action] = 1.0 if action == 'Right' else 0.0
            agent.q_values(1)[action] = 1.0 if action == 'Right' else 0.0
        record = run_episode(agent, ResetStepOnlyEnvironment(), max_steps=50,
                             learn=True, explore=False)
        self.assertTrue(record.terminated)
        self.assertEqual(record.steps, 2)
        self.assertEqual(record.final_state, 2)
        self.assertAlmostEqual(record.total_reward, 0.9)

    def test_no_step_after_termination_in_real_environment(self):
        # The real env raises RuntimeError if stepped after termination.
        env = VacuumEnvironment(seed=3, intended_probability=1.0)
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.5, seed=3)
        records = train(agent, env, episodes=50, max_steps=200)
        self.assertTrue(any(record.terminated for record in records))

    def test_max_steps_caps_episode(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.0, seed=0)
        for state in (0, 1):
            for action in ACTIONS:
                agent.q_values(state)[action] = 1.0 if action == 'Left' else 0.0
        record = run_episode(agent, ResetStepOnlyEnvironment(), max_steps=7,
                             learn=False, explore=False)
        self.assertFalse(record.terminated)
        self.assertEqual(record.steps, 7)


class TestInterfaceAndExploration(unittest.TestCase):
    def test_learner_uses_only_reset_and_step(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, epsilon=0.3, seed=4)
        env = ResetStepOnlyEnvironment()
        train(agent, env, episodes=20, max_steps=20)
        evaluate(agent, env, episodes=5, max_steps=20)  # AssertionError if internals touched

    def test_greedy_evaluation_does_not_change_q_table(self):
        result = run_trial(QLearningConfig(train_episodes=50, eval_episodes=0, seed=2))
        snapshot = {s: dict(row) for s, row in result.agent.q_table.items()}
        evaluate(result.agent, VacuumEnvironment(seed=99), episodes=20, max_steps=50)
        for state, row in snapshot.items():
            self.assertEqual(result.agent.q_table[state], row)

    def test_epsilon_zero_is_greedy_and_epsilon_one_explores(self):
        greedy = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=0.0, seed=0)
        greedy.q_values('s')['Down'] = 5.0
        self.assertTrue(all(greedy.choose_action('s') == 'Down' for _ in range(100)))
        explorer = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=1.0, seed=0)
        explorer.q_values('s')['Down'] = 5.0
        self.assertEqual({explorer.choose_action('s') for _ in range(200)}, set(ACTIONS))

    def test_epsilon_decay_respects_minimum(self):
        agent = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=0.5, seed=0)
        train(agent, VacuumEnvironment(seed=0), episodes=100, max_steps=20,
              epsilon_decay=0.5, min_epsilon=0.05)
        self.assertEqual(agent.epsilon, 0.05)

    def test_invalid_config_rejected(self):
        for bad in ({'alpha': 0}, {'gamma': 1.5}, {'epsilon': -0.1}, {'max_steps': 0}):
            with self.assertRaises(ValueError):
                QLearningConfig(**bad)


class TestReproducibilityAndLivingReward(unittest.TestCase):
    def test_same_seed_same_q_table_and_results(self):
        config = QLearningConfig(train_episodes=200, eval_episodes=50, seed=7)
        first, second = run_trial(config), run_trial(config)
        self.assertEqual(first.agent.q_table, second.agent.q_table)
        self.assertEqual(first.training, second.training)
        self.assertEqual(first.evaluation, second.evaluation)

    def test_different_seeds_differ(self):
        a = run_trial(QLearningConfig(train_episodes=200, eval_episodes=0, seed=1))
        b = run_trial(QLearningConfig(train_episodes=200, eval_episodes=0, seed=2))
        self.assertNotEqual(a.agent.q_table, b.agent.q_table)

    def test_living_reward_default_and_override(self):
        default_env = VacuumEnvironment(seed=0, intended_probability=1.0)
        self.assertEqual(default_env.step('Right').reward, -0.04)
        custom_env = VacuumEnvironment(seed=0, intended_probability=1.0, living_reward=-0.5)
        self.assertEqual(custom_env.step('Right').reward, -0.5)

    def test_trial_learns_to_reach_charger(self):
        config = QLearningConfig(alpha=0.5, gamma=0.9, epsilon=0.2,
                                 train_episodes=1500, eval_episodes=200, seed=0)
        result = run_trial(config)
        reached = sum(1 for r in result.evaluation if r.terminated and r.final_state == CHARGER)
        self.assertGreater(reached / len(result.evaluation), 0.5)


if __name__ == '__main__':
    unittest.main()

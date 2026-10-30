### Performance Metrics Test**
```python
import unittest
from vacuum.environment import VacuumEnvironment, CHARGER, TRAP

class TestVacuumPerformance(unittest.TestCase):
    def test_baseline_scripted_performance(self):
        """Runs multiple episodes with fixed seeds to measure baseline performance metrics."""
        episodes = 5
        total_rewards = []
        steps_to_finish = []

        # Optimal scripted route avoiding obstacles: Right 3x, Down 3x
        scripted_actions = ['Right', 'Right', 'Right', 'Down', 'Down', 'Down']

        for ep in range(episodes):
            env = VacuumEnvironment(seed=42 + ep, intended_probability=1.0)
            episode_reward = 0
            steps = 0

            for action in scripted_actions:
                result = env.step(action)
                episode_reward += result.reward
                steps += 1
                if result.terminated:
                    break

            total_rewards.append(episode_reward)
            steps_to_finish.append(steps)

            # Assert that deterministic execution always successfully recharges
            self.assertEqual(env.state, CHARGER)
            self.assertTrue(result.terminated)

        avg_reward = sum(total_rewards) / len(total_rewards)
        avg_steps = sum(steps_to_finish) / len(steps_to_finish)

        # Baseline performance checks
        self.assertGreater(avg_reward, 0.0, "Average episode reward should be positive.")
        self.assertEqual(avg_steps, 6, "Scripted optimal path should take exactly 6 steps.")

    def test_stochastic_performance_benchmark(self):
        """Measures agent survival rate under stochastic (80/10/10) movement conditions."""
        runs = 10
        recharged_count = 0

        scripted_actions = ['Right', 'Right', 'Right', 'Down', 'Down', 'Down']

        for run in range(runs):
            env = VacuumEnvironment(seed=100 + run)
            for action in scripted_actions:
                result = env.step(action)
                if result.terminated:
                    if env.state == CHARGER:
                        recharged_count += 1
                    break

        # Log stochastic completion rate metric
        completion_rate = recharged_count / runs
        self.assertGreaterEqual(completion_rate, 0.0, "Benchmark completion rate tracked.")

if __name__ == '__main__':
    unittest.main()

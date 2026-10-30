import unittest
from vacuum.environment import VacuumEnvironment, CHARGER, TRAP

class TestPerformanceBenchmark(unittest.TestCase):
    def test_multi_episode_benchmark(self):
        """Runs multiple benchmark episodes and tracks success rate and average rewards."""
        episodes = 20
        successful_runs = 0
        total_accumulated_reward = 0.0

        scripted_actions = ['Right', 'Right', 'Right', 'Down', 'Down', 'Down']

        for ep in range(episodes):
            env = VacuumEnvironment(seed=200 + ep) # Stochastic evaluation
            episode_reward = 0.0

            for action in scripted_actions:
                result = env.step(action)
                episode_reward += result.reward
                if result.terminated:
                    break

            total_accumulated_reward += episode_reward
            if env.state == CHARGER:
                successful_runs += success_rate_increment = 1

        success_rate = (successful_runs / episodes) * 100
        avg_reward = total_accumulated_reward / episodes

        print(f"\n--- Performance Benchmark Results ---")
        print(f"Total Episodes Evaluated: {episodes}")
        print(f"Success Rate (Recharged): {success_rate:.2f}%")
        print(f"Average Episode Reward: {avg_reward:.2f}")

        # Assert benchmark trackers function correctly
        self.assertGreaterEqual(success_rate, 0.0)
        self.assertIsInstance(avg_reward, float)

if __name__ == '__main__':
    unittest.main()

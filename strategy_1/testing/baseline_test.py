import unittest
from vacuum.environment import VacuumEnvironment, CHARGER, START

class TestBaselineVacuum(unittest.TestCase):
    def test_scripted_baseline_path(self):
        """Verifies that the hardcoded optimal path successfully reaches the charger."""
        env = VacuumEnvironment(seed=42, intended_probability=1.0)
        
        # Optimal scripted route avoiding the obstacle at (1,1): Right 3x, Down 3x
        scripted_actions = ['Right', 'Right', 'Right', 'Down', 'Down', 'Down']
        
        current_state = env.state
        self.assertEqual(current_state, START)

        for action in scripted_actions:
            result = env.step(action)
            if result.terminated:
                break

        # Confirm successful baseline outcome
        self.assertEqual(env.state, CHARGER)
        self.assertTrue(result.terminated)
        self.assertEqual(result.reward, 10.0)

if __name__ == '__main__':
    unittest.main()

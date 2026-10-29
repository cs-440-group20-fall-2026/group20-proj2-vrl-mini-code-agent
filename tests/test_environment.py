import unittest
from vacuum.environment import VacuumEnvironment, START, CHARGER, TRAP, OBSTACLE, ACTIONS

# TODO: Complete Unit Tests
class TestVacuumEnvironment(unittest.TestCase):
    def test_reset(self):
        env = VacuumEnvironment()
        # moove agent away from start
        env.step('Right')
        state = env.reset() #reset environment
        self.assertEqual(state, START)
        self.assertFalse(env.terminated)

    def test_invalid_action(self):
        with self.assertRaises(ValueError):
            VacuumEnvironment().step('Teleport')

    def test_boundary(self):
        env = VacuumEnvironment(intended_probability=1)
        self.assertEqual(env.step('Up').state, START)

    def test_obstacle(self):
        env = VacuumEnvironment(intended_probability=1)
        env.step('Right')
        self.assertEqual(env.step('Down').state, (0, 1))

    def test_charger_terminal(self):
        # TODO: Complete charger result
        return

    def test_trap_terminal(self):
        #TODO: Complete trap result
        return

    def test_seed_reproducible(self):
        a, b = VacuumEnvironment(seed=12), VacuumEnvironment(seed=12)
        for action in ['Right', 'Right', 'Down', 'Left', 'Down']:
            self.assertEqual(a.step(action), b.step(action))
            if a.terminated:
                break

if __name__ == '__main__':
    unittest.main()

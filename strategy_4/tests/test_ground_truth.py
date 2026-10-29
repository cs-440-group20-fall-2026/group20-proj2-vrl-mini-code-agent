"""Ground truth: one recorded run of the environment, inputs and expected outputs."""
import unittest
from vacuum.environment import VacuumEnvironment

# (input action, expected state, reward, terminated); deterministic with intended_probability=1
GROUND_TRUTH = [
    ('Right', (0, 1), -0.04, False),
    ('Right', (0, 2), -0.04, False),
    ('Right', (0, 3), -0.04, False),
    ('Down',  (1, 3), -0.04, False),
    ('Down',  (2, 3), -0.04, False),
    ('Down',  (3, 3), 10.0,  True),
]


class TestGroundTruth(unittest.TestCase):
    def test_single_run_matches(self):
        env = VacuumEnvironment(intended_probability=1)
        for action, state, reward, terminated in GROUND_TRUTH:
            result = env.step(action)
            self.assertEqual((result.state, result.reward, result.terminated),
                             (state, reward, terminated))


if __name__ == '__main__':
    unittest.main()

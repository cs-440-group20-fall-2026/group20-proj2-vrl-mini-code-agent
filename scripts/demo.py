"""Run a scripted demonstration; NOT a learning agent or optimal policy."""
from vacuum.environment import VacuumEnvironment, CHARGER, TRAP

# Avoid the obstacle by going along the top row, then down the right edge.
SCRIPTED_ACTIONS = ['Right'] * 3 + ['Down'] * 3

def main():
    env = VacuumEnvironment(seed=42)
    print('Vacuum environment demo (scripted actions; Q-learning not implemented)')
    print('Start:', env.state)
    env.render()
    for index, action in enumerate(SCRIPTED_ACTIONS, 1):
        result = env.step(action)
        print(f'Step {index}: intended={action:<5} actual={result.actual_action:<5} '
              f'state={result.state} reward={result.reward:+.2f} done={result.terminated}')
        if result.terminated:
            break
    print('Outcome:', 'recharged' if env.state == CHARGER else
          'trap' if env.state == TRAP else 'unfinished scripted episode')
    print('Final grid:')
    env.render()

if __name__ == '__main__':
    main()

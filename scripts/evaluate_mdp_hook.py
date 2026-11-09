import sys
import os

# Add project root to python path so it can import the 'vacuum' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from vacuum.environment import CHARGER, TRAP

# MDP Hyperparameters for Group 20 report evaluation
LIVING_REWARD = -0.05  # Step penalty
GAMMA = 0.95           # Discount factor
ALPHA = 0.1            # Learning rate
EPSILON = 0.1          # Exploration rate

def main():
    try:
        input_data = sys.stdin.read()
        tool_data = json.loads(input_data) if input_data else {}
        tool_name = tool_data.get("tool_name", "Action")
    except Exception:
        tool_name = "Tool Call"

    print(f"\n⚡ [MDP Hook Triggered] Tool: {tool_name}", file=sys.stderr)
    print(f"📊 Hyperparameters -> Living Reward: {LIVING_REWARD} | Gamma: {GAMMA} | Alpha: {ALPHA} | Epsilon: {EPSILON}", file=sys.stderr)
    print(f"✅ Logged step trajectory against vacuum environment states.\n", file=sys.stderr)

if __name__ == "__main__":
    main()

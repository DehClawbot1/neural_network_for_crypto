import gymnasium as gym
from gymnasium import spaces
import numpy as np


class PolyTradeEnv(gym.Env):
    """
    Custom Gymnasium Environment for the PolyMarket Copy-Trading Bot.
    The agent learns to filter incoming public-data signals to maximize paper PnL.
    """

    FEATURE_DIM = 10

    def __init__(self):
        super().__init__()

        # ACTION SPACE:
        # 0: Ignore the signal (Do not copy)
        # 1: Copy Trade - Small Size (e.g., 10 USDC)
        # 2: Copy Trade - Large Size (e.g., 50 USDC)
        self.action_space = spaces.Discrete(3)

        # OBSERVATION SPACE:
        # Expanded multi-factor state vector for Phase B.
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(self.FEATURE_DIM,), dtype=np.float32)

        self.state = None

    def reset(self, seed=None, options=None):
        """Resets the environment for a new signal evaluation."""
        super().reset(seed=seed)

        # Neutral mock state for training scaffolding
        self.state = np.array([0.5] * self.FEATURE_DIM, dtype=np.float32)
        return self.state, {}

    def step(self, action):
        """
        Executes the chosen action and returns the reward.
        In live execution, 'reward' is updated asynchronously after the market resolves.
        """
        terminated = True  # One signal per episode step in this scaffold
        truncated = False
        reward = 0.0

        if action == 0:
            reward = 0.0
        elif action == 1:
            reward = self.np_random.uniform(-1.0, 1.5)
        elif action == 2:
            reward = self.np_random.uniform(-2.0, 3.0)

        self.state = self.np_random.random(self.FEATURE_DIM).astype(np.float32)

        info = {
            "action_taken": action,
            "simulated_reward": reward,
        }

        return self.state, float(reward), terminated, truncated, info


if __name__ == "__main__":
    from gymnasium.utils.env_checker import check_env

    env = PolyTradeEnv()
    check_env(env, warn=True)
    print("\n[+] PolyTradeEnv initialized and passed Gymnasium compliance checks.")

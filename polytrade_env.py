import gymnasium as gym
from gymnasium import spaces
import numpy as np


class PolyTradeEnv(gym.Env):
    """
    Custom Gymnasium Environment for the PolyMarket Copy-Trading Bot.
    The agent learns to filter incoming social signals to maximize PnL.
    """

    def __init__(self):
        super().__init__()

        # ACTION SPACE:
        # 0: Ignore the signal (Do not copy)
        # 1: Copy Trade - Small Size (e.g., 10 USDC)
        # 2: Copy Trade - Large Size (e.g., 50 USDC)
        self.action_space = spaces.Discrete(3)

        # OBSERVATION SPACE (The "State"):
        # We feed the neural network 4 normalized data points (values between 0 and 1):
        # 1. trader_win_rate: The historical success rate of the copied wallet.
        # 2. normalized_trade_size: How big the whale's bet was relative to their average.
        # 3. current_price: The current PolyMarket odds for the Yes/No token.
        # 4. time_left: Time remaining until the market resolves.
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(4,), dtype=np.float32)

        self.state = None

    def reset(self, seed=None, options=None):
        """Resets the environment for a new signal evaluation."""
        super().reset(seed=seed)

        # Initialize with a neutral mock state (in production, this gets injected by the scraper)
        self.state = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
        return self.state, {}

    def step(self, action):
        """
        Executes the chosen action and returns the reward.
        In live execution, 'reward' is updated asynchronously after the market resolves.
        """
        # For the scaffolding/training phase, we simulate the market resolution
        terminated = True  # We evaluate one signal per episode step
        truncated = False
        reward = 0.0

        if action == 0:
            reward = 0.0  # No risk taken, neutral reward
        elif action == 1:
            # Simulated small trade outcome
            reward = self.np_random.uniform(-1.0, 1.5)
        elif action == 2:
            # Simulated large trade outcome (higher risk/reward)
            reward = self.np_random.uniform(-2.0, 3.0)

        # Transition to next state (mocked)
        self.state = self.np_random.random(4).astype(np.float32)

        info = {
            "action_taken": action,
            "simulated_reward": reward,
        }

        return self.state, float(reward), terminated, truncated, info


if __name__ == "__main__":
    # Quick sanity check to ensure the Gymnasium environment complies with the API
    from gymnasium.utils.env_checker import check_env

    env = PolyTradeEnv()
    check_env(env, warn=True)
    print("\n[+] PolyTradeEnv initialized and passed Gymnasium compliance checks.")

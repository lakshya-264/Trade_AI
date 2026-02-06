"""
Reinforcement Learning Agent Service
RL agent for final trading decisions using ensemble predictions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import random
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DQN(nn.Module):
    """Deep Q-Network for trading decisions"""
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        super(DQN, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, action_size)
        
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return x

class ReplayBuffer:
    """Experience replay buffer for DQN"""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done = map(np.stack, zip(*batch))
        return state, action, reward, next_state, done
    
    def __len__(self):
        return len(self.buffer)

class TradingEnvironment:
    """Trading environment for RL agent"""
    
    def __init__(self, initial_balance: float = 100000.0, transaction_cost: float = 0.001):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0.0  # Current position size
        self.transaction_cost = transaction_cost
        self.current_price = 0.0
        self.portfolio_value = initial_balance
        self.trade_history = []
        
        # State tracking
        self.price_history = deque(maxlen=100)
        self.return_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        
    def reset(self):
        """Reset environment to initial state"""
        self.balance = self.initial_balance
        self.position = 0.0
        self.portfolio_value = self.initial_balance
        self.trade_history = []
        self.price_history.clear()
        self.return_history.clear()
        self.volume_history.clear()
        
        return self.get_state()
    
    def step(self, action: int, price: float, volume: float = 0.0) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return next state, reward, done, info"""
        try:
            # Update price and volume history
            self.current_price = price
            self.price_history.append(price)
            self.volume_history.append(volume)
            
            if len(self.price_history) > 1:
                returns = (price - self.price_history[-2]) / self.price_history[-2]
                self.return_history.append(returns)
            
            # Execute action
            reward = self._execute_action(action, price)
            
            # Update portfolio value
            self.portfolio_value = self.balance + self.position * price
            
            # Check if done (end of episode)
            done = len(self.trade_history) >= 1000  # Max episode length
            
            # Get next state
            next_state = self.get_state()
            
            # Info dictionary
            info = {
                'portfolio_value': self.portfolio_value,
                'balance': self.balance,
                'position': self.position,
                'current_price': price,
                'total_trades': len(self.trade_history)
            }
            
            return next_state, reward, done, info
            
        except Exception as e:
            logger.error(f"Error in trading environment step: {e}")
            return self.get_state(), 0.0, True, {}
    
    def _execute_action(self, action: int, price: float) -> float:
        """Execute trading action and return reward"""
        try:
            # Action mapping: 0=Hold, 1=Buy, 2=Sell
            reward = 0.0
            
            if action == 1:  # Buy
                if self.balance > price * (1 + self.transaction_cost):
                    # Calculate position size (use 10% of balance)
                    max_position_value = self.balance * 0.1
                    position_size = max_position_value / price
                    
                    # Execute buy
                    cost = position_size * price * (1 + self.transaction_cost)
                    if cost <= self.balance:
                        self.balance -= cost
                        self.position += position_size
                        
                        # Record trade
                        self.trade_history.append({
                            'action': 'BUY',
                            'price': price,
                            'quantity': position_size,
                            'cost': cost,
                            'timestamp': datetime.now()
                        })
                        
                        reward = 0.1  # Small positive reward for taking action
            
            elif action == 2:  # Sell
                if self.position > 0:
                    # Execute sell
                    proceeds = self.position * price * (1 - self.transaction_cost)
                    self.balance += proceeds
                    
                    # Record trade
                    self.trade_history.append({
                        'action': 'SELL',
                        'price': price,
                        'quantity': self.position,
                        'proceeds': proceeds,
                        'timestamp': datetime.now()
                    })
                    
                    # Calculate reward based on profit/loss
                    if len(self.trade_history) >= 2:
                        # Find corresponding buy trade
                        buy_trades = [t for t in self.trade_history[:-1] if t['action'] == 'BUY']
                        if buy_trades:
                            last_buy = buy_trades[-1]
                            profit_loss = proceeds - last_buy['cost']
                            reward = profit_loss / last_buy['cost']  # Return as percentage
                    
                    self.position = 0.0
            
            else:  # Hold
                # Small negative reward for inaction to encourage trading
                reward = -0.01
            
            return reward
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return 0.0
    
    def get_state(self) -> np.ndarray:
        """Get current state representation"""
        try:
            state = []
            
            # Portfolio state
            state.append(self.balance / self.initial_balance)  # Normalized balance
            state.append(self.position)  # Current position
            state.append(self.portfolio_value / self.initial_balance)  # Portfolio value ratio
            
            # Price features
            if len(self.price_history) >= 2:
                price_change = (self.price_history[-1] - self.price_history[-2]) / self.price_history[-2]
                state.append(price_change)
            else:
                state.append(0.0)
            
            # Price momentum (last 5 prices)
            if len(self.price_history) >= 5:
                momentum = (self.price_history[-1] - self.price_history[-5]) / self.price_history[-5]
                state.append(momentum)
            else:
                state.append(0.0)
            
            # Volatility (standard deviation of returns)
            if len(self.return_history) >= 10:
                volatility = np.std(list(self.return_history))
                state.append(volatility)
            else:
                state.append(0.0)
            
            # Volume features
            if len(self.volume_history) >= 2:
                volume_change = (self.volume_history[-1] - self.volume_history[-2]) / (self.volume_history[-2] + 1e-8)
                state.append(volume_change)
            else:
                state.append(0.0)
            
            # Technical indicators
            if len(self.price_history) >= 20:
                sma_20 = np.mean(list(self.price_history)[-20:])
                price_sma_ratio = self.price_history[-1] / sma_20
                state.append(price_sma_ratio)
            else:
                state.append(1.0)
            
            # RSI-like indicator
            if len(self.return_history) >= 14:
                returns = list(self.return_history)[-14:]
                gains = [r for r in returns if r > 0]
                losses = [abs(r) for r in returns if r < 0]
                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                rs = avg_gain / (avg_loss + 1e-8)
                rsi = 100 - (100 / (1 + rs))
                state.append(rsi / 100)  # Normalized RSI
            else:
                state.append(0.5)
            
            # Pad state to fixed size
            while len(state) < 20:
                state.append(0.0)
            
            return np.array(state[:20], dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return np.zeros(20, dtype=np.float32)

class ReinforcementLearningAgent:
    """Reinforcement Learning agent for trading decisions"""
    
    def __init__(self, state_size: int = 20, action_size: int = 3, learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        
        # DQN networks
        self.q_network = DQN(state_size, action_size)
        self.target_network = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Training parameters
        self.batch_size = 32
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.gamma = 0.95  # Discount factor
        self.target_update_freq = 100
        
        # Experience replay
        self.memory = ReplayBuffer(capacity=10000)
        
        # Training tracking
        self.training_step = 0
        self.episode_rewards = []
        self.episode_losses = []
        
        # Models directory
        self.models_dir = "models/reinforcement_learning"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Trading environment
        self.env = TradingEnvironment()
        
        # Initialize target network
        self.update_target_network()
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """Choose action using epsilon-greedy policy"""
        try:
            if training and random.random() < self.epsilon:
                return random.randint(0, self.action_size - 1)
            
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.q_network(state_tensor)
                action = q_values.argmax().item()
            
            return action
            
        except Exception as e:
            logger.error(f"Error choosing action: {e}")
            return 0  # Default to hold
    
    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Store experience in replay buffer"""
        try:
            self.memory.push(state, action, reward, next_state, done)
        except Exception as e:
            logger.error(f"Error storing experience: {e}")
    
    def replay(self) -> float:
        """Train the agent on a batch of experiences"""
        try:
            if len(self.memory) < self.batch_size:
                return 0.0
            
            # Sample batch from memory
            states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
            
            # Convert to tensors
            states = torch.FloatTensor(states)
            actions = torch.LongTensor(actions)
            rewards = torch.FloatTensor(rewards)
            next_states = torch.FloatTensor(next_states)
            dones = torch.BoolTensor(dones)
            
            # Current Q values
            current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
            
            # Next Q values from target network
            with torch.no_grad():
                next_q_values = self.target_network(next_states).max(1)[0]
                target_q_values = rewards + (self.gamma * next_q_values * ~dones)
            
            # Compute loss
            loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
            
            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            # Update target network
            self.training_step += 1
            if self.training_step % self.target_update_freq == 0:
                self.update_target_network()
            
            # Decay epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            
            return loss.item()
            
        except Exception as e:
            logger.error(f"Error in replay: {e}")
            return 0.0
    
    def update_target_network(self):
        """Update target network with current network weights"""
        try:
            self.target_network.load_state_dict(self.q_network.state_dict())
        except Exception as e:
            logger.error(f"Error updating target network: {e}")
    
    def train_episode(self, price_data: List[float], volume_data: List[float] = None) -> Dict:
        """Train agent on a single episode"""
        try:
            if volume_data is None:
                volume_data = [0.0] * len(price_data)
            
            # Reset environment
            state = self.env.reset()
            total_reward = 0.0
            losses = []
            
            for i, (price, volume) in enumerate(zip(price_data, volume_data)):
                # Choose action
                action = self.act(state, training=True)
                
                # Execute action
                next_state, reward, done, info = self.env.step(action, price, volume)
                
                # Store experience
                self.remember(state, action, reward, next_state, done)
                
                # Train on batch
                if len(self.memory) >= self.batch_size:
                    loss = self.replay()
                    if loss > 0:
                        losses.append(loss)
                
                # Update state and reward
                state = next_state
                total_reward += reward
                
                if done:
                    break
            
            # Record episode metrics
            self.episode_rewards.append(total_reward)
            if losses:
                self.episode_losses.append(np.mean(losses))
            
            return {
                "episode_reward": total_reward,
                "episode_length": len(price_data),
                "final_portfolio_value": self.env.portfolio_value,
                "total_trades": len(self.env.trade_history),
                "average_loss": np.mean(losses) if losses else 0.0,
                "epsilon": self.epsilon
            }
            
        except Exception as e:
            logger.error(f"Error training episode: {e}")
            return {"error": str(e)}
    
    def train_multiple_episodes(self, episodes: int, price_data: List[float], volume_data: List[float] = None) -> Dict:
        """Train agent on multiple episodes"""
        try:
            training_results = []
            
            for episode in range(episodes):
                result = self.train_episode(price_data, volume_data)
                training_results.append(result)
                
                if episode % 10 == 0:
                    logger.info(f"Episode {episode}: Reward={result.get('episode_reward', 0):.2f}, "
                              f"Portfolio={result.get('final_portfolio_value', 0):.2f}, "
                              f"Epsilon={self.epsilon:.3f}")
            
            # Calculate training statistics
            rewards = [r.get('episode_reward', 0) for r in training_results]
            portfolio_values = [r.get('final_portfolio_value', 0) for r in training_results]
            
            return {
                "episodes_trained": episodes,
                "average_reward": np.mean(rewards),
                "std_reward": np.std(rewards),
                "max_reward": np.max(rewards),
                "min_reward": np.min(rewards),
                "average_portfolio_value": np.mean(portfolio_values),
                "final_epsilon": self.epsilon,
                "training_results": training_results
            }
            
        except Exception as e:
            logger.error(f"Error training multiple episodes: {e}")
            return {"error": str(e)}
    
    def predict_action(self, state: np.ndarray) -> Dict:
        """Predict trading action for given state"""
        try:
            # Get Q-values
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.q_network(state_tensor).squeeze().numpy()
            
            # Choose best action
            action = np.argmax(q_values)
            confidence = q_values[action] / np.sum(q_values) if np.sum(q_values) > 0 else 0.33
            
            # Action mapping
            action_names = {0: "HOLD", 1: "BUY", 2: "SELL"}
            
            return {
                "action": int(action),
                "action_name": action_names[action],
                "q_values": q_values.tolist(),
                "confidence": float(confidence),
                "epsilon": self.epsilon
            }
            
        except Exception as e:
            logger.error(f"Error predicting action: {e}")
            return {"error": str(e)}
    
    def get_trading_recommendation(self, current_data: Dict) -> Dict:
        """Get trading recommendation based on current market data"""
        try:
            # Extract current state from market data
            state = self._extract_state_from_data(current_data)
            
            # Get action prediction
            action_result = self.predict_action(state)
            
            if "error" in action_result:
                return action_result
            
            # Add market context
            recommendation = {
                **action_result,
                "market_data": {
                    "current_price": current_data.get('price', 0),
                    "volume": current_data.get('volume', 0),
                    "timestamp": datetime.now().isoformat()
                },
                "agent_status": {
                    "training_step": self.training_step,
                    "memory_size": len(self.memory),
                    "epsilon": self.epsilon
                }
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error getting trading recommendation: {e}")
            return {"error": str(e)}
    
    def _extract_state_from_data(self, data: Dict) -> np.ndarray:
        """Extract state representation from market data"""
        try:
            # This would extract relevant features from the market data
            # For now, return a mock state
            state = np.random.randn(self.state_size).astype(np.float32)
            return state
        except Exception as e:
            logger.error(f"Error extracting state from data: {e}")
            return np.zeros(self.state_size, dtype=np.float32)
    
    def save_models(self):
        """Save trained models"""
        try:
            # Save Q-network
            torch.save(self.q_network.state_dict(), 
                      os.path.join(self.models_dir, 'q_network.pth'))
            
            # Save target network
            torch.save(self.target_network.state_dict(), 
                      os.path.join(self.models_dir, 'target_network.pth'))
            
            # Save training state
            training_state = {
                'epsilon': self.epsilon,
                'training_step': self.training_step,
                'episode_rewards': self.episode_rewards,
                'episode_losses': self.episode_losses
            }
            
            joblib.dump(training_state, os.path.join(self.models_dir, 'training_state.pkl'))
            
            logger.info("RL agent models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models"""
        try:
            # Load Q-network
            q_network_path = os.path.join(self.models_dir, 'q_network.pth')
            if os.path.exists(q_network_path):
                self.q_network.load_state_dict(torch.load(q_network_path))
                logger.info("Q-network loaded")
            
            # Load target network
            target_network_path = os.path.join(self.models_dir, 'target_network.pth')
            if os.path.exists(target_network_path):
                self.target_network.load_state_dict(torch.load(target_network_path))
                logger.info("Target network loaded")
            
            # Load training state
            training_state_path = os.path.join(self.models_dir, 'training_state.pkl')
            if os.path.exists(training_state_path):
                training_state = joblib.load(training_state_path)
                self.epsilon = training_state.get('epsilon', 0.01)
                self.training_step = training_state.get('training_step', 0)
                self.episode_rewards = training_state.get('episode_rewards', [])
                self.episode_losses = training_state.get('episode_losses', [])
                logger.info("Training state loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_agent_performance(self) -> Dict:
        """Get agent performance statistics"""
        try:
            if not self.episode_rewards:
                return {"error": "No training data available"}
            
            recent_rewards = self.episode_rewards[-100:] if len(self.episode_rewards) >= 100 else self.episode_rewards
            
            return {
                "total_episodes": len(self.episode_rewards),
                "average_reward": np.mean(self.episode_rewards),
                "recent_average_reward": np.mean(recent_rewards),
                "max_reward": np.max(self.episode_rewards),
                "min_reward": np.min(self.episode_rewards),
                "reward_trend": np.polyfit(range(len(recent_rewards)), recent_rewards, 1)[0] if len(recent_rewards) > 1 else 0,
                "current_epsilon": self.epsilon,
                "training_step": self.training_step,
                "memory_size": len(self.memory),
                "average_loss": np.mean(self.episode_losses) if self.episode_losses else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting agent performance: {e}")
            return {"error": str(e)}

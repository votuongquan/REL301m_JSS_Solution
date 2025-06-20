import gymnasium as gym
import JSSEnv
import numpy as np
import pandas as pd
import time
from typing import Dict, List, Tuple, Any, Callable
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from agents import BaseJSSAgent, create_agent


class JSSPerformanceMetrics:
    """Class to handle performance metrics calculation and storage"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.makespans = []
        self.rewards = []
        self.execution_times = []
    
    def add_episode_result(self, makespan: float, reward: float, execution_time: float):
        """Add results from a single episode"""
        self.makespans.append(makespan)
        self.rewards.append(reward)
        self.execution_times.append(execution_time)
    
    def get_summary_stats(self) -> Dict[str, float]:
        """Get summary statistics"""
        if not self.makespans:
            return {}
        
        return {
            'avg_makespan': np.mean(self.makespans),
            'std_makespan': np.std(self.makespans),
            'min_makespan': np.min(self.makespans),
            'max_makespan': np.max(self.makespans),
            'avg_reward': np.mean(self.rewards),
            'std_reward': np.std(self.rewards),
            'avg_execution_time': np.mean(self.execution_times),
            'total_episodes': len(self.makespans),
            'all_makespans': self.makespans.copy(),
            'all_rewards': self.rewards.copy()
        }


class JSSEnvironmentManager:
    """Manages environment creation and episode execution"""
    
    def __init__(self, instance_path: str):
        self.instance_path = instance_path
    
    def create_environment(self) -> gym.Env:
        """Create and return JSS environment"""
        return gym.make('jss-v1', env_config={'instance_path': self.instance_path})
    
    def run_episode(self, agent_function: Callable, env: gym.Env = None) -> Tuple[float, float, float]:
        """
        Run a single episode with the given agent function
        
        Returns:
            Tuple of (makespan, total_reward, execution_time)
        """
        if env is None:
            env = self.create_environment()
        
        # Handle different observation formats
        try:
            obs, _ = env.reset()
        except ValueError:
            obs = env.reset()
        
        done = False
        total_reward = 0
        start_time = time.time()
        
        while not done:
            action = agent_function(env, obs)
            
            # Take action
            step_result = env.step(action)
            if len(step_result) == 5:
                obs, reward, done, truncated, _ = step_result
            else:
                obs, reward, done, _ = step_result
                truncated = False
            
            total_reward += reward
            
            if truncated:
                done = True
        
        execution_time = time.time() - start_time
        makespan = env.current_time_step
        
        return makespan, total_reward, execution_time


class JSSComparisonFramework:
    """
    Improved framework for comparing JSS agents and dispatching rules
    """
    
    def __init__(self, instance_path: str):
        self.instance_path = instance_path
        self.env_manager = JSSEnvironmentManager(instance_path)
        self.results = {}
        
        # Available dispatching rules
        self.dispatching_rules = [
            'SPT', 'FIFO', 'MWR', 'LWR', 'MOR', 'LOR', 'CR'
        ]
    
    def run_agent_evaluation(self, agent: BaseJSSAgent, num_episodes: int = 10) -> Dict[str, float]:
        """Evaluate a custom agent"""
        metrics = JSSPerformanceMetrics()
        
        for episode in range(num_episodes):
            env = self.env_manager.create_environment()
            
            def agent_wrapper(env, obs):
                return agent(env, obs)
            
            makespan, total_reward, execution_time = self.env_manager.run_episode(agent_wrapper, env)
            metrics.add_episode_result(makespan, total_reward, execution_time)
            env.close()
        
        return metrics.get_summary_stats()
    
    def run_dispatching_rule_evaluation(self, rule_name: str, num_episodes: int = 10) -> Dict[str, float]:
        """Evaluate a dispatching rule"""
        from JSSEnv.dispatching import get_rule
        
        metrics = JSSPerformanceMetrics()
        rule = get_rule(rule_name)
        
        for episode in range(num_episodes):
            env = self.env_manager.create_environment()
            
            def rule_wrapper(env, obs):
                return rule(env)
            
            makespan, total_reward, execution_time = self.env_manager.run_episode(rule_wrapper, env)
            metrics.add_episode_result(makespan, total_reward, execution_time)
            env.close()
        
        return metrics.get_summary_stats()
    
    def run_random_baseline(self, num_episodes: int = 10) -> Dict[str, float]:
        """Run random baseline"""
        metrics = JSSPerformanceMetrics()
        
        def random_agent(env, obs):
            if isinstance(obs, dict) and "action_mask" in obs:
                legal_actions = obs["action_mask"]
            else:
                legal_actions = env.get_legal_actions()
            
            legal_actions = np.array(legal_actions)
            if np.sum(legal_actions) == 0:
                return 0
            
            return np.random.choice(
                len(legal_actions), 1, p=(legal_actions / legal_actions.sum())
            )[0]
        
        for episode in range(num_episodes):
            env = self.env_manager.create_environment()
            makespan, total_reward, execution_time = self.env_manager.run_episode(random_agent, env)
            metrics.add_episode_result(makespan, total_reward, execution_time)
            env.close()
        
        return metrics.get_summary_stats()
    
    def run_comprehensive_comparison(self, custom_agents: List[BaseJSSAgent], 
                                   num_episodes: int = 10) -> pd.DataFrame:
        """Run comprehensive comparison of all methods"""
        print("Starting comprehensive comparison...")
        
        # Evaluate custom agents
        for agent in custom_agents:
            print(f"Evaluating {agent.get_name()}...")
            self.results[agent.get_name()] = self.run_agent_evaluation(agent, num_episodes)
        
        # Evaluate dispatching rules
        for rule in self.dispatching_rules:
            print(f"Evaluating {rule} dispatching rule...")
            try:
                self.results[rule] = self.run_dispatching_rule_evaluation(rule, num_episodes)
            except Exception as e:
                print(f"Error running {rule}: {e}")
                continue
        
        # Evaluate random baseline
        print("Evaluating random baseline...")
        self.results['Random'] = self.run_random_baseline(num_episodes)
        
        return self._create_results_dataframe()
    
    def _create_results_dataframe(self) -> pd.DataFrame:
        """Create results DataFrame"""
        df_data = []
        for method, metrics in self.results.items():
            df_data.append({
                'Method': method,
                'Avg_Makespan': metrics['avg_makespan'],
                'Std_Makespan': metrics['std_makespan'],
                'Min_Makespan': metrics['min_makespan'],
                'Max_Makespan': metrics['max_makespan'],
                'Avg_Reward': metrics['avg_reward'],
                'Std_Reward': metrics['std_reward'],
                'Avg_Execution_Time': metrics['avg_execution_time'],
                'Episodes': metrics['total_episodes']
            })
        
        df = pd.DataFrame(df_data)
        return df.sort_values('Avg_Makespan')
    
    def save_results(self, filename: str = "jss_results.csv"):
        """Save detailed results"""
        if not self.results:
            print("No results to save.")
            return
        
        detailed_data = []
        for method, metrics in self.results.items():
            for i, (makespan, reward) in enumerate(zip(metrics['all_makespans'], metrics['all_rewards'])):
                detailed_data.append({
                    'Method': method,
                    'Episode': i + 1,
                    'Makespan': makespan,
                    'Reward': reward
                })
        
        df = pd.DataFrame(detailed_data)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
    
    def create_visualizations(self, save_path: str = None):
        """Create comparison visualizations"""
        if not self.results:
            print("No results to plot.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('JSS Methods Comparison', fontsize=16)
        
        methods = list(self.results.keys())
        avg_makespans = [self.results[method]['avg_makespan'] for method in methods]
        std_makespans = [self.results[method]['std_makespan'] for method in methods]
        avg_rewards = [self.results[method]['avg_reward'] for method in methods]
        avg_times = [self.results[method]['avg_execution_time'] for method in methods]
        
        # Makespan comparison
        axes[0, 0].bar(methods, avg_makespans, yerr=std_makespans, capsize=5)
        axes[0, 0].set_title('Average Makespan (Lower is Better)')
        axes[0, 0].set_ylabel('Makespan')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Reward comparison
        axes[0, 1].bar(methods, avg_rewards)
        axes[0, 1].set_title('Average Reward (Higher is Better)')
        axes[0, 1].set_ylabel('Reward')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Execution time
        axes[1, 0].bar(methods, avg_times)
        axes[1, 0].set_title('Average Execution Time')
        axes[1, 0].set_ylabel('Time (seconds)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Distribution
        makespan_data = []
        makespan_labels = []
        for method in methods:
            makespan_data.extend(self.results[method]['all_makespans'])
            makespan_labels.extend([method] * len(self.results[method]['all_makespans']))
        
        df_box = pd.DataFrame({'Method': makespan_labels, 'Makespan': makespan_data})
        sns.boxplot(data=df_box, x='Method', y='Makespan', ax=axes[1, 1])
        axes[1, 1].set_title('Makespan Distribution')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Visualizations saved to {save_path}")
    
    def print_summary(self):
        """Print comparison summary"""
        if not self.results:
            print("No results to summarize.")
            return
        
        print("\n" + "="*70)
        print("JSS COMPARISON SUMMARY")
        print("="*70)
        
        sorted_methods = sorted(self.results.items(), key=lambda x: x[1]['avg_makespan'])
        
        print(f"{'Rank':<4} {'Method':<20} {'Avg Makespan':<12} {'Min Makespan':<12} {'Avg Reward':<12}")
        print("-" * 70)
        
        for rank, (method, metrics) in enumerate(sorted_methods, 1):
            print(f"{rank:<4} {method:<20} {metrics['avg_makespan']:<12.2f} "
                  f"{metrics['min_makespan']:<12.2f} {metrics['avg_reward']:<12.2f}")
        
        best_method = sorted_methods[0][0]
        best_makespan = sorted_methods[0][1]['avg_makespan']
        
        print(f"\n🏆 Best performing method: {best_method}")
        print(f"📊 Best average makespan: {best_makespan:.2f}")
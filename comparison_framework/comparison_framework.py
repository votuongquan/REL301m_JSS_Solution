import time
import JSSEnv
import numpy as np
import pandas as pd
import seaborn as sns
import gymnasium as gym
from pathlib import Path
import matplotlib.pyplot as plt
from agents import BaseJSSAgent, create_agent
from typing import Dict, List, Tuple, Any, Callable
from advanced_visualizer import AdvancedJSSVisualizer


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
        print(f"💾 Results saved to {filename}")
    
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
        
        print(f"\nBest performing method: {best_method}")
        print(f"Best average makespan: {best_makespan:.2f}")
    
    def create_enhanced_visualizations(self, save_dir: str = "results"):
        """Create enhanced visualizations using the new visualizer"""
        if not self.results:
            print("No results to visualize.")
            return
        
        # Create results directory
        Path(save_dir).mkdir(exist_ok=True)
        
        # Initialize the advanced visualizer
        visualizer = AdvancedJSSVisualizer(self.results, self.instance_path)
        
        # Create comprehensive dashboard
        dashboard_path = Path(save_dir) / "comprehensive_dashboard.png"
        visualizer.create_comprehensive_dashboard(str(dashboard_path))
        
        # Create detailed comparison
        detailed_path = Path(save_dir) / "detailed_comparison.png"
        visualizer.create_detailed_comparison(str(detailed_path))
        
        # Generate performance report
        self._generate_performance_report(save_dir)
            
    def _generate_performance_report(self, save_dir: str):
        """Generate a comprehensive performance report - FIXED UNICODE"""
        report_path = Path(save_dir) / "performance_report.txt"
        
        # Open file with UTF-8 encoding to support Unicode characters
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("JOB SHOP SCHEDULING PERFORMANCE REPORT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Instance: {self.instance_path}\n")
            f.write(f"Total Methods Compared: {len(self.results)}\n\n")
            
            # Performance ranking
            f.write("PERFORMANCE RANKING:\n")
            f.write("-" * 30 + "\n")
            
            sorted_methods = sorted(self.results.items(), 
                                  key=lambda x: x[1]['avg_makespan'])
            
            for i, (method, stats) in enumerate(sorted_methods, 1):
                f.write(f"{i:2d}. {method:<20} Avg: {stats['avg_makespan']:6.1f} "
                       f"(±{stats['std_makespan']:5.1f})\n")
            
            # Best performers analysis - Remove emoji characters
            f.write("\n\nBEST PERFORMERS ANALYSIS:\n")
            f.write("-" * 30 + "\n")
            
            best_method, best_stats = sorted_methods[0]
            f.write(f"CHAMPION: {best_method}\n")  # Removed emoji
            f.write(f"   Average Makespan: {best_stats['avg_makespan']:.1f}\n")
            f.write(f"   Standard Deviation: {best_stats['std_makespan']:.1f}\n")
            f.write(f"   Best Single Result: {best_stats['min_makespan']:.1f}\n")
            f.write(f"   Consistency Score: {best_stats['std_makespan']/best_stats['avg_makespan']*100:.1f}%\n")
            
            # Custom agents analysis
            custom_agents = [m for m in self.results.keys() 
                           if m.startswith(('Hybrid', 'Adaptive'))]
            
            if custom_agents:
                f.write("\n\nCUSTOM AGENTS PERFORMANCE:\n")
                f.write("-" * 30 + "\n")
                
                for agent in custom_agents:
                    stats = self.results[agent]
                    rank = [i for i, (m, _) in enumerate(sorted_methods, 1) if m == agent][0]
                    f.write(f"{agent}:\n")
                    f.write(f"   Rank: #{rank} out of {len(self.results)}\n")
                    f.write(f"   Performance: {stats['avg_makespan']:.1f} ± {stats['std_makespan']:.1f}\n")
                    f.write(f"   Best Result: {stats['min_makespan']:.1f}\n\n")
        
        print(f"📝 Performance report saved to {report_path}")
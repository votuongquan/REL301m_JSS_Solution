"""
Streaming JSS Framework for Real-time Results
Lightweight version without visualization dependencies
"""

import asyncio
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

# Import JSS environment
try:
    import gym
    from JSSEnv.envs.jss_env import JssEnv
except ImportError:
    pass

from .stream_agents import BaseStreamJSSAgent, create_stream_agent, create_dispatching_rule_agent


class StreamPerformanceMetrics:
    """Lightweight performance metrics for streaming"""

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

    def get_current_stats(self) -> Dict[str, float]:
        """Get current statistics"""
        if not self.makespans:
            return {
                'episodes_completed': 0,
                'avg_makespan': 0,
                'best_makespan': 0,
                'worst_makespan': 0,
                'avg_reward': 0,
                'avg_execution_time': 0,
            }

        return {
            'episodes_completed': len(self.makespans),
            'avg_makespan': np.mean(self.makespans),
            'best_makespan': np.min(self.makespans),
            'worst_makespan': np.max(self.makespans),
            'std_makespan': np.std(self.makespans),
            'avg_reward': np.mean(self.rewards),
            'avg_execution_time': np.mean(self.execution_times),
            'all_makespans': self.makespans.copy(),
            'all_rewards': self.rewards.copy(),
        }


class StreamEnvironmentManager:
    """Manages environment creation and episode execution for streaming"""

    def __init__(self, instance_path: str):
        self.instance_path = instance_path

    def create_environment(self):
        """Create and return JSS environment"""
        try:
            return gym.make('jss-v1', env_config={'instance_path': self.instance_path})
        except Exception as e:
            raise RuntimeError(f"Failed to create JSS environment: {e}")

    async def run_episode_stream(self, agent_function: Callable, env = None, 
                                stream_callback: Callable = None) -> Tuple[float, float, float]:
        """
        Run a single episode with streaming callbacks
        
        Args:
            agent_function: Agent function to call for actions
            env: Environment instance (created if None)
            stream_callback: Async callback for streaming updates
        
        Returns:
            Tuple of (makespan, total_reward, execution_time)
        """
        if env is None:
            env = self.create_environment()

        # Reset environment
        try:
            obs = env.reset()
        except ValueError:
            obs = env.reset()[0]

        done = False
        total_reward = 0
        step = 0
        start_time = time.time()

        # Send episode start event
        if stream_callback:
            await stream_callback('step', step=step, action=None, reward=0, done=False, obs=obs)

        while not done:
            # Get action from agent
            action = agent_function(env, obs)
            
            # Take step
            step_result = env.step(action)            
            if len(step_result) == 4:
                obs, reward, done, _ = step_result
            else:
                obs, reward, done = step_result

            total_reward += reward
            step += 1

            # Stream progress
            if stream_callback:
                await stream_callback('step', 
                                    step=step, 
                                    action=action, 
                                    reward=reward, 
                                    done=done, 
                                    obs=obs,
                                    total_reward=total_reward,
                                    current_makespan=getattr(env, 'current_time_step', 0))

            # Add small delay for streaming visibility (can be removed for production)
            if step % 10 == 0:  # Stream every 10 steps
                await asyncio.sleep(0.001)  # Very small delay

        execution_time = time.time() - start_time
        makespan = getattr(env, 'current_time_step', 0)

        return makespan, total_reward, execution_time


class StreamJSSFramework:
    """
    Streaming framework for JSS comparison with real-time results
    """

    def __init__(self, instance_path: str):
        self.instance_path = instance_path
        self.env_manager = StreamEnvironmentManager(instance_path)
        self.results = {}

        # Available dispatching rules
        self.dispatching_rules = ['SPT', 'FIFO', 'MWR', 'LWR', 'MOR', 'LOR', 'CR']

    async def run_agent_evaluation_stream(self, agent: BaseStreamJSSAgent, num_episodes: int = 10,
                                        stream_callback: Callable = None) -> Dict[str, float]:
        """Evaluate a custom agent with streaming"""
        metrics = StreamPerformanceMetrics()
        agent_name = agent.get_name()

        for episode in range(num_episodes):
            # Reset agent state
            agent.reset()
            
            # Send episode start event
            if stream_callback:
                await stream_callback('episode_start', 
                                    episode=episode + 1, 
                                    total_episodes=num_episodes,
                                    agent_name=agent_name)

            # Create episode-specific callback
            async def episode_callback(event_type, **kwargs):
                if stream_callback:
                    await stream_callback('episode_progress',
                                        episode=episode + 1,
                                        agent_name=agent_name,
                                        **kwargs)

            # Run episode
            try:
                makespan, total_reward, execution_time = await self.env_manager.run_episode_stream(
                    agent, None, episode_callback
                )
                
                metrics.add_episode_result(makespan, total_reward, execution_time)

                # Send episode complete event
                if stream_callback:
                    await stream_callback('episode_complete',
                                        episode=episode + 1,
                                        agent_name=agent_name,
                                        makespan=makespan,
                                        total_reward=total_reward,
                                        execution_time=execution_time,
                                        current_stats=metrics.get_current_stats())

            except Exception as e:
                if stream_callback:
                    await stream_callback('error',
                                        episode=episode + 1,
                                        agent_name=agent_name,
                                        error_message=str(e))
                break

        return metrics.get_current_stats()

    async def run_dispatching_rule_evaluation_stream(self, rule_name: str, num_episodes: int = 10,
                                                   stream_callback: Callable = None) -> Dict[str, float]:
        """Evaluate a dispatching rule with streaming"""
        
        # Create rule agent
        rule_agent = create_dispatching_rule_agent(rule_name)
        
        # Run evaluation
        return await self.run_agent_evaluation_stream(rule_agent, num_episodes, stream_callback)

    async def run_random_baseline_stream(self, num_episodes: int = 10,
                                       stream_callback: Callable = None) -> Dict[str, float]:
        """Run random baseline with streaming"""
        
        def random_agent(env, obs):
            if isinstance(obs, dict) and 'action_mask' in obs:
                legal_actions = obs['action_mask']
            else:
                legal_actions = obs
            
            legal_indices = [i for i in range(len(legal_actions)) if legal_actions[i]]
            return np.random.choice(legal_indices) if legal_indices else 0

        # Create wrapper agent
        class RandomAgent(BaseStreamJSSAgent):
            def __init__(self):
                super().__init__('Random')
            
            def __call__(self, env, obs):
                return random_agent(env, obs)

        random_agent_instance = RandomAgent()
        return await self.run_agent_evaluation_stream(random_agent_instance, num_episodes, stream_callback)

    async def run_comprehensive_comparison_stream(self, 
                                                custom_agents: List[BaseStreamJSSAgent],
                                                dispatching_rules: List[str] = None,
                                                num_episodes: int = 10,
                                                include_random: bool = True,
                                                stream_callback: Callable = None) -> Dict[str, Dict]:
        """
        Run comprehensive comparison with streaming
        
        Args:
            custom_agents: List of custom agents to evaluate
            dispatching_rules: List of dispatching rule names to evaluate
            num_episodes: Number of episodes per method
            include_random: Whether to include random baseline
            stream_callback: Callback for streaming events
        
        Returns:
            Dictionary with results for each method
        """
        
        if dispatching_rules is None:
            dispatching_rules = self.dispatching_rules

        all_methods = []
        
        # Add custom agents
        for agent in custom_agents:
            all_methods.append(('agent', agent))
        
        # Add dispatching rules
        for rule in dispatching_rules:
            all_methods.append(('rule', rule))
        
        # Add random baseline
        if include_random:
            all_methods.append(('random', None))

        total_methods = len(all_methods)
        completed_methods = 0

        # Send initial progress
        if stream_callback:
            await stream_callback('comparison_start', 
                                total_methods=total_methods,
                                total_episodes_per_method=num_episodes)

        # Evaluate each method
        for method_type, method_obj in all_methods:
            method_name = None
            
            try:
                if method_type == 'agent':
                    method_name = method_obj.get_name()
                    
                    # Send method start event
                    if stream_callback:
                        await stream_callback('method_start',
                                            method_name=method_name,
                                            method_type='agent',
                                            completed_methods=completed_methods,
                                            total_methods=total_methods)
                    
                    # Create method-specific callback
                    async def method_callback(event_type, **kwargs):
                        if stream_callback:
                            await stream_callback(event_type, **kwargs)
                    
                    results = await self.run_agent_evaluation_stream(method_obj, num_episodes, method_callback)
                    self.results[method_name] = results

                elif method_type == 'rule':
                    method_name = method_obj
                    
                    if stream_callback:
                        await stream_callback('method_start',
                                            method_name=method_name,
                                            method_type='dispatching_rule',
                                            completed_methods=completed_methods,
                                            total_methods=total_methods)
                    
                    async def method_callback(event_type, **kwargs):
                        if stream_callback:
                            await stream_callback(event_type, **kwargs)
                    
                    results = await self.run_dispatching_rule_evaluation_stream(method_obj, num_episodes, method_callback)
                    self.results[method_name] = results

                elif method_type == 'random':
                    method_name = 'Random'
                    
                    if stream_callback:
                        await stream_callback('method_start',
                                            method_name=method_name,
                                            method_type='random',
                                            completed_methods=completed_methods,
                                            total_methods=total_methods)
                    
                    async def method_callback(event_type, **kwargs):
                        if stream_callback:
                            await stream_callback(event_type, **kwargs)
                    
                    results = await self.run_random_baseline_stream(num_episodes, method_callback)
                    self.results[method_name] = results

                completed_methods += 1

                # Send method completion event
                if stream_callback:
                    await stream_callback('method_complete',
                                        method_name=method_name,
                                        results=results,
                                        completed_methods=completed_methods,
                                        total_methods=total_methods)

            except Exception as e:
                # Send error event
                if stream_callback:
                    await stream_callback('error',
                                        method_name=method_name or 'Unknown',
                                        error_message=str(e),
                                        completed_methods=completed_methods,
                                        total_methods=total_methods)
                
                # Continue with next method
                completed_methods += 1
                continue

        # Send comparison completion
        if stream_callback:
            await stream_callback('comparison_complete',
                                results=self.results,
                                total_methods=total_methods)

        return self.results

    def get_results_summary(self) -> Dict:
        """Get summary of results"""
        if not self.results:
            return {}

        summary = {}
        
        # Find best performer
        best_method = None
        best_makespan = float('inf')
        
        for method_name, results in self.results.items():
            avg_makespan = results.get('avg_makespan', float('inf'))
            if avg_makespan < best_makespan:
                best_makespan = avg_makespan
                best_method = method_name
            
            summary[method_name] = {
                'avg_makespan': avg_makespan,
                'best_makespan': results.get('best_makespan', 0),
                'episodes_completed': results.get('episodes_completed', 0),
                'avg_execution_time': results.get('avg_execution_time', 0)
            }

        summary['_meta'] = {
            'best_method': best_method,
            'best_makespan': best_makespan,
            'total_methods': len(self.results)        }

        return summary

    async def test_environment(self) -> bool:
        """Test if environment can be created successfully"""
        try:
            env = self.env_manager.create_environment()
            _ = env.reset()
            env.close()
            return True
        except Exception as e:
            print(f"Environment test failed: {e}")
            return False

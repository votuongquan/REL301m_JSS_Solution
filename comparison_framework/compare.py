"""
Advanced Job Shop Scheduling Comparison
"""

import os
import time
import warnings
import argparse
from agents import create_agent
from comparison_framework import JSSComparisonFramework

warnings.filterwarnings('ignore', category=DeprecationWarning)


def main():
    if not os.path.exists("results"):
        os.makedirs("results")

    parser = argparse.ArgumentParser(
        description='Job Shop Scheduling Comparison Framework')
    parser.add_argument('--instance', type=str, default='dmu16',
                        help='Instance name (default: dmu16)')
    parser.add_argument('--episodes', type=int, default=30,
                        help='Number of episodes to run for each method (default: 30)')

    args = parser.parse_args()

    instance_name = args.instance
    instance_path = "instances/" + instance_name
    num_episodes = args.episodes
    result_path = "results/" + instance_name + \
        time.strftime("_%Y%m%d_%H%M%S") + "/"

    if not os.path.exists(result_path):
        os.makedirs(result_path)

    print("Starting Advanced JSS Comparison")
    print(f"Instance: {instance_path}")
    print(f"Episodes per method: {num_episodes}")

    # Initialize comparison framework
    framework = JSSComparisonFramework(instance_path)

    # Create custom agents
    agents = [
        create_agent("hybrid"),
        create_agent("lookahead"),
    ]

    # Test environment first
    print("\n🔧 Testing environment setup...")
    try:
        test_env = framework.env_manager.create_environment()
        test_obs = test_env.reset()
        print(f"✅ Environment created successfully!")

        # Test agent
        test_agent = agents[0]
        action = test_agent(test_env, test_obs)
        print(f"✅ Agent test successful! Action: {action}")

        test_env.close()

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return

    # Run comprehensive comparison
    print(f"\n🏁 Running comprehensive comparison...")

    try:
        results_df = framework.run_comprehensive_comparison(
            agents, num_episodes)
        # # Display results
        # print("\n📊 COMPARISON RESULTS:")
        # print("="*80)
        # print(results_df.to_string(index=False, float_format='%.2f'))

        # Print detailed summary
        framework.print_summary()

        # Create visualizations
        print("\n✨ Creating visualizations...")
        framework.create_enhanced_visualizations(result_path, agents)

        # Save detailed results
        framework.save_results(result_path + "detailed_results.csv")

        # Performance analysis
        print("\n🎯 PERFORMANCE ANALYSIS:")
        print("="*50)

        # Find best custom agent
        custom_agents = [agent.get_name() for agent in agents]
        custom_results = {name: framework.results[name]
                          for name in custom_agents if name in framework.results}

        if custom_results:
            best_custom = min(custom_results.items(),
                              key=lambda x: x[1]['avg_makespan'])
            print(f"🥇 Best custom agent: {best_custom[0]}")
            print(f"📏 Average makespan: {best_custom[1]['avg_makespan']:.2f}")

            # Compare with best dispatching rule
            rule_results = {name: data for name, data in framework.results.items()
                            if name in framework.dispatching_rules}

            if rule_results:
                best_rule = min(rule_results.items(),
                                key=lambda x: x[1]['avg_makespan'])
                improvement = (best_rule[1]['avg_makespan'] - best_custom[1]
                               ['avg_makespan']) / best_rule[1]['avg_makespan'] * 100

                print(
                    f"🎲 Best dispatching rule: {best_rule[0]} (makespan: {best_rule[1]['avg_makespan']:.2f})")

                if improvement > 0:
                    print(
                        f"🚀 Custom agent improvement: {improvement:.2f}% better than best rule!")
                else:
                    print(
                        f"📉 Custom agent performance: {abs(improvement):.2f}% worse than best rule")

        print("\n✅ Comparison completed successfully!")

    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

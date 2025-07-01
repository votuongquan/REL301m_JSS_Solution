import os
import time
import argparse
from pathlib import Path
from controller_agent import ControllerJSSAgent
from utils import create_gantt_chart, save_schedule_to_csv

import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)


def main():
    if not os.path.exists("results"):
        os.makedirs("results")

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Job Shop Scheduling with Controller Constraints')
    parser.add_argument('--instance', type=str, default='dmu16',
                        help='Instance name (default: dmu16)')
    parser.add_argument('--controller', type=str, default='20p_20m',
                        help='Controller name (default: 20p_20m)')
    parser.add_argument('--num_people', type=int, default=20,
                        help='Number of people (default: 20)')

    args = parser.parse_args()

    # Configuration using parsed arguments
    root_dir = os.path.dirname(os.path.abspath(__file__))
    instances_root = os.path.join(root_dir, "instances")
    controllers_root = os.path.join(root_dir, "controllers")

    instance_name = args.instance
    instance_path = os.path.join(instances_root, instance_name)
    controller_name = args.controller
    controller_path = os.path.join(controllers_root, controller_name + ".txt")
    num_people = args.num_people
    result_path = os.path.join(root_dir, "results", instance_name + "_" +
                              controller_name + time.strftime("_%Y%m%d_%H%M%S") + "/")

    # Create result directory
    Path(result_path).mkdir(exist_ok=True)

    # Initialize agent
    agent = ControllerJSSAgent(instance_path, controller_path, num_people)

    # Run episode
    print("Running JSS with controller constraints...")
    makespan, total_reward, schedule = agent.run_episode()

    # Print results
    print("\nResults:")
    print(f"Makespan: {makespan:.2f}")
    print(f"Total Reward: {total_reward:.2f}")

    # Create Gantt chart
    create_gantt_chart(schedule, f"{result_path}gantt_chart.png")

    # Save detailed schedule
    save_schedule_to_csv(schedule, f"{result_path}schedule.csv")


if __name__ == "__main__":
    main()

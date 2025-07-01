"""
Utility functions for Job Shop Scheduling
"""

from pathlib import Path
from typing import List, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def create_gantt_chart(
	schedule: List[Tuple[int, int, float, float, int]],
	save_path: str = 'results/gantt_chart.png',
):
	"""Create a Gantt chart for the schedule"""
	plt.style.use('seaborn-v0_8-whitegrid')
	sns.set_palette('husl')

	fig, ax = plt.subplots(figsize=(12, 8))

	# Prepare data for Gantt chart
	machines = sorted(list(set(task[1] for task in schedule)))
	colors = sns.color_palette('husl', n_colors=len(set(task[0] for task in schedule)))

	for task in schedule:
		job_id, machine_id, start_time, end_time, person_id = task
		duration = end_time - start_time
		machine_idx = machines.index(machine_id)

		# Plot task bar
		ax.barh(
			machine_idx,
			duration,
			left=start_time,
			height=0.4,
			color=colors[job_id % len(colors)],
			edgecolor='black',
			alpha=0.8,
		)

	# Customize plot
	ax.set_yticks(range(len(machines)))
	ax.set_yticklabels([f'Machine {m}' for m in machines])
	ax.set_xlabel('Time')
	ax.set_ylabel('Machines')
	ax.set_title('JSS Gantt Chart')
	ax.grid(True, alpha=0.3)

	# Add legend
	job_patches = [mpatches.Patch(color=colors[i % len(colors)], label=f'Job {i}') for i in range(len(colors))]
	plt.legend(handles=job_patches, bbox_to_anchor=(1.05, 1), loc='upper left')

	plt.tight_layout()

	# Save the chart
	Path(save_path).parent.mkdir(exist_ok=True)
	plt.savefig(save_path, dpi=300, bbox_inches='tight')
	plt.close()

	print(f'Gantt chart saved to {save_path}')


def save_schedule_to_csv(schedule: List[Tuple[int, int, float, float, int]], save_path: str):
	"""Save the schedule to a CSV file"""
	schedule_df = pd.DataFrame(
		schedule,
		columns=['Job_ID', 'Machine_ID', 'Start_Time', 'End_Time', 'Person_ID'],
	)
	schedule_df.to_csv(save_path, index=False)
	print(f'Detailed schedule saved to {save_path}')

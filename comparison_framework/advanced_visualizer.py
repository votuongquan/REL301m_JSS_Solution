import warnings
from pathlib import Path
from typing import Dict, List

import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)


class AdvancedJSSVisualizer:
	"""Advanced visualization class for JSS comparison results"""

	def __init__(self, results: Dict, instance_name: str = 'JSS Instance'):
		self.results = results
		self.instance_name = instance_name

		# Set style with proper seaborn version handling
		try:
			plt.style.use('seaborn-v0_8-whitegrid')
		except Exception:
			try:
				plt.style.use('seaborn-whitegrid')
			except Exception:
				plt.style.use('default')

		sns.set_palette('husl')

		# Set fonts that are available on Windows
		self._configure_fonts()

		# Define color scheme
		self.colors = {
			'HybridPriorityScoring': '#2E8B57',  # Sea Green
			'AdaptiveLookAhead': '#4169E1',  # Royal Blue
			'SPT': '#FF6347',  # Tomato
			'FIFO': '#FFD700',  # Gold
			'MWR': '#FF69B4',  # Hot Pink
			'LWR': '#20B2AA',  # Light Sea Green
			'MOR': '#9370DB',  # Medium Purple
			'LOR': '#CD853F',  # Peru
			'CR': '#FF4500',  # Orange Red
			'Random': '#A9A9A9',  # Dark Gray
		}

	def _configure_fonts(self):
		"""Configure matplotlib fonts for Windows compatibility"""
		# Get list of available fonts
		available_fonts = [f.name for f in fm.fontManager.ttflist]

		# Priority list of fonts (Windows compatible)
		preferred_fonts = [
			'Segoe UI',  # Windows 10/11 default
			'Calibri',  # Office suite font
			'Arial',  # Classic Windows font
			'Tahoma',  # Windows system font
			'Verdana',  # Web-safe font
			'DejaVu Sans',  # Cross-platform font
			'sans-serif',  # Generic fallback
		]

		# Find the first available font
		selected_font = 'sans-serif'  # Default fallback
		for font in preferred_fonts:
			if font in available_fonts or font == 'sans-serif':
				selected_font = font
				break

		# Configure matplotlib
		plt.rcParams['font.family'] = selected_font
		plt.rcParams['font.sans-serif'] = preferred_fonts
		plt.rcParams['axes.unicode_minus'] = False

		# Suppress font warnings
		import logging

		logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

	def create_comprehensive_dashboard(self, save_path: str = None, figsize=(22, 26)):
		"""Create a comprehensive dashboard with multiple visualizations"""

		# Create figure with custom layout
		fig = plt.figure(figsize=figsize, facecolor='white')
		gs = GridSpec(
			4,
			3,
			height_ratios=[1.2, 1, 1, 0.4],
			width_ratios=[1.2, 1, 1],
			hspace=0.35,
			wspace=0.3,
		)

		# Main title
		fig.suptitle(
			f'Job Shop Scheduling Performance Analysis\n{self.instance_name}',
			fontsize=22,
			fontweight='bold',
			y=0.96,
		)

		# 1. Performance Overview (Top row, spanning 2 columns)
		ax1 = fig.add_subplot(gs[0, :2])
		self._create_performance_overview(ax1)

		# 2. Performance Ranking (Top right)
		ax2 = fig.add_subplot(gs[0, 2])
		self._create_ranking_plot(ax2)

		# 3. Makespan Distribution (Second row, left)
		ax3 = fig.add_subplot(gs[1, 0])
		self._create_violin_plot(ax3)

		# 4. Performance vs Consistency (Second row, center)
		ax4 = fig.add_subplot(gs[1, 1])
		self._create_scatter_plot(ax4)

		# 5. Improvement Analysis (Second row, right)
		ax5 = fig.add_subplot(gs[1, 2])
		self._create_improvement_analysis(ax5)

		# 6. Detailed Statistics Heatmap (Third row, spanning all)
		ax6 = fig.add_subplot(gs[2, :])
		self._create_statistics_heatmap(ax6)

		# 7. Performance Summary Table (Bottom)
		ax7 = fig.add_subplot(gs[3, :])
		self._create_summary_table(ax7)

		# Adjust layout manually to avoid tight_layout issues
		plt.subplots_adjust(top=0.93, bottom=0.05, left=0.08, right=0.95)

		if save_path:
			plt.savefig(
				save_path,
				dpi=300,
				bbox_inches='tight',
				facecolor='white',
				edgecolor='none',
			)
			print(f'📈Comprehensive dashboard saved to {save_path}')

		return fig

	def _create_performance_overview(self, ax):
		"""Create main performance comparison bar chart"""
		methods = list(self.results.keys())
		avg_makespans = [self.results[method]['avg_makespan'] for method in methods]
		std_makespans = [self.results[method]['std_makespan'] for method in methods]

		# Sort by performance
		sorted_data = sorted(zip(methods, avg_makespans, std_makespans), key=lambda x: x[1])
		methods, avg_makespans, std_makespans = zip(*sorted_data)

		# Create bars
		bars = ax.bar(
			range(len(methods)),
			avg_makespans,
			yerr=std_makespans,
			capsize=5,
			alpha=0.8,
			color=[self.colors.get(m, '#696969') for m in methods],
			edgecolor='black',
			linewidth=0.5,
		)

		# Highlight best performers
		for i, bar in enumerate(bars[:3]):  # Top 3
			bar.set_alpha(1.0)
			bar.set_edgecolor('gold')
			bar.set_linewidth(2)

		ax.set_xlabel('Methods', fontsize=12, fontweight='bold')
		ax.set_ylabel('Average Makespan', fontsize=12, fontweight='bold')
		ax.set_title('Performance Comparison (Lower is Better)', fontsize=14, fontweight='bold')
		ax.set_xticks(range(len(methods)))
		ax.set_xticklabels(methods, rotation=45, ha='right')

		# Add value labels on bars
		for i, (bar, val, std) in enumerate(zip(bars, avg_makespans, std_makespans)):
			height = bar.get_height()
			ax.text(
				bar.get_x() + bar.get_width() / 2.0,
				height + std + max(avg_makespans) * 0.02,
				f'{val:.0f}',
				ha='center',
				va='bottom',
				fontweight='bold',
				fontsize=9,
			)

		ax.grid(True, alpha=0.3)

	def _create_ranking_plot(self, ax):
		"""Create ranking visualization"""
		methods = list(self.results.keys())
		avg_makespans = [self.results[method]['avg_makespan'] for method in methods]

		# Sort and rank
		sorted_methods = sorted(zip(methods, avg_makespans), key=lambda x: x[1])

		ranks = list(range(1, len(sorted_methods) + 1))
		method_names = [m[0] for m in sorted_methods]

		# Create horizontal bar chart
		bars = ax.barh(
			ranks,
			[m[1] for m in sorted_methods],
			color=[self.colors.get(m, '#696969') for m in method_names],
			alpha=0.8,
			edgecolor='black',
			linewidth=0.5,
		)

		# Highlight top performers
		for i in range(min(3, len(bars))):
			bars[i].set_alpha(1.0)
			bars[i].set_edgecolor('gold')
			bars[i].set_linewidth(2)

		ax.set_yticks(ranks)
		ax.set_yticklabels([f'{i}. {name}' for i, name in enumerate(method_names, 1)])
		ax.set_xlabel('Average Makespan', fontsize=10, fontweight='bold')
		ax.set_title('Performance Ranking', fontsize=12, fontweight='bold')
		ax.invert_yaxis()

		# Add performance values
		for i, (bar, (method, makespan)) in enumerate(zip(bars, sorted_methods)):
			width = bar.get_width()
			ax.text(
				width + max([m[1] for m in sorted_methods]) * 0.01,
				bar.get_y() + bar.get_height() / 2,
				f'{makespan:.0f}',
				ha='left',
				va='center',
				fontweight='bold',
				fontsize=9,
			)

	def _create_violin_plot(self, ax):
		"""Create violin plot for makespan distribution"""
		# Prepare data for violin plot
		makespan_data = []
		labels = []

		for method in self.results.keys():
			makespans = self.results[method]['all_makespans']
			makespan_data.extend(makespans)
			labels.extend([method] * len(makespans))

		df = pd.DataFrame({'Method': labels, 'Makespan': makespan_data})

		# Create violin plot with seaborn version compatibility
		try:
			# For newer seaborn versions
			sns.violinplot(
				data=df,
				x='Method',
				y='Makespan',
				ax=ax,
				hue='Method',
				palette=[self.colors.get(m, '#696969') for m in df['Method'].unique()],
				legend=False,
			)
		except Exception:
			try:
				# For older seaborn versions
				sns.violinplot(
					data=df,
					x='Method',
					y='Makespan',
					ax=ax,
					palette=[self.colors.get(m, '#696969') for m in df['Method'].unique()],
				)
			except Exception:
				# Ultimate fallback - simple violin plot
				sns.violinplot(data=df, x='Method', y='Makespan', ax=ax)

		ax.set_title('Makespan Distribution', fontsize=12, fontweight='bold')
		ax.set_xlabel('Methods', fontsize=10, fontweight='bold')
		ax.set_ylabel('Makespan', fontsize=10, fontweight='bold')
		ax.tick_params(axis='x', rotation=45)
		ax.grid(True, alpha=0.3)

	def _create_scatter_plot(self, ax):
		"""Create scatter plot of performance vs consistency"""
		methods = list(self.results.keys())
		avg_makespans = [self.results[method]['avg_makespan'] for method in methods]
		std_makespans = [self.results[method]['std_makespan'] for method in methods]

		# Create scatter plot
		for method, avg, std in zip(methods, avg_makespans, std_makespans):
			color = self.colors.get(method, '#696969')
			size = 150 if method.startswith(('Hybrid', 'Adaptive')) else 100
			alpha = 1.0 if method.startswith(('Hybrid', 'Adaptive')) else 0.7

			ax.scatter(
				avg,
				std,
				c=color,
				s=size,
				alpha=alpha,
				edgecolors='black',
				linewidth=1,
				label=method,
			)

		ax.set_xlabel('Average Makespan (Performance)', fontsize=10, fontweight='bold')
		ax.set_ylabel('Standard Deviation (Consistency)', fontsize=10, fontweight='bold')
		ax.set_title(
			'Performance vs Consistency\n(Bottom-left is best)',
			fontsize=12,
			fontweight='bold',
		)

		# Add quadrant lines
		if avg_makespans and std_makespans:
			avg_x = np.mean(avg_makespans)
			avg_y = np.mean(std_makespans)
			ax.axhline(y=avg_y, color='gray', linestyle='--', alpha=0.5)
			ax.axvline(x=avg_x, color='gray', linestyle='--', alpha=0.5)

			# Highlight best quadrant
			ax.fill_betweenx([0, avg_y], 0, avg_x, alpha=0.1, color='green', label='Best Zone')

		ax.grid(True, alpha=0.3)
		# Move legend outside plot area
		ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

	def _create_improvement_analysis(self, ax):
		"""Create improvement analysis chart"""
		# Find best traditional method (excluding custom agents)
		traditional_methods = [m for m in self.results.keys() if not m.startswith(('Hybrid', 'Adaptive')) and m != 'Random']

		if not traditional_methods:
			ax.text(
				0.5,
				0.5,
				'No traditional methods\nfor comparison',
				ha='center',
				va='center',
				transform=ax.transAxes,
				fontsize=12,
			)
			ax.set_title('Improvement Analysis', fontsize=12, fontweight='bold')
			return

		best_traditional = min(traditional_methods, key=lambda x: self.results[x]['avg_makespan'])
		best_traditional_makespan = self.results[best_traditional]['avg_makespan']

		# Calculate improvements
		custom_agents = [m for m in self.results.keys() if m.startswith(('Hybrid', 'Adaptive'))]

		if not custom_agents:
			ax.text(
				0.5,
				0.5,
				'No custom agents\nto analyze',
				ha='center',
				va='center',
				transform=ax.transAxes,
				fontsize=12,
			)
			ax.set_title('Improvement Analysis', fontsize=12, fontweight='bold')
			return

		improvements = []
		agent_names = []

		for agent in custom_agents:
			agent_makespan = self.results[agent]['avg_makespan']
			improvement = ((best_traditional_makespan - agent_makespan) / best_traditional_makespan) * 100
			improvements.append(improvement)
			agent_names.append(agent)

		# Create bar chart
		colors = [self.colors.get(agent, '#696969') for agent in agent_names]
		bars = ax.bar(
			agent_names,
			improvements,
			color=colors,
			alpha=0.8,
			edgecolor='black',
			linewidth=1,
		)

		# Color positive improvements green, negative red
		for bar, imp in zip(bars, improvements):
			if imp > 0:
				bar.set_color('#2E8B57')  # Green for improvement
			else:
				bar.set_color('#DC143C')  # Red for degradation

		ax.set_ylabel('Improvement (%)', fontsize=10, fontweight='bold')
		ax.set_title(
			f'Improvement vs Best Traditional\n({best_traditional})',
			fontsize=12,
			fontweight='bold',
		)
		ax.tick_params(axis='x', rotation=45)

		# Add zero line
		ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

		# Add value labels
		for bar, imp in zip(bars, improvements):
			height = bar.get_height()
			ax.text(
				bar.get_x() + bar.get_width() / 2.0,
				height + (0.5 if height >= 0 else -1),
				f'{imp:.1f}%',
				ha='center',
				va='bottom' if height >= 0 else 'top',
				fontweight='bold',
				fontsize=9,
			)

		ax.grid(True, alpha=0.3)

	def _create_statistics_heatmap(self, ax):
		"""Create statistics heatmap"""
		methods = list(self.results.keys())

		# Prepare data for heatmap
		stats_data = []
		for method in methods:
			stats = self.results[method]
			stats_data.append([
				stats['avg_makespan'],
				stats['std_makespan'],
				stats['min_makespan'],
				stats['max_makespan'],
				stats['avg_execution_time'] * 1000,  # Convert to ms
			])

		stats_df = pd.DataFrame(
			stats_data,
			index=methods,
			columns=[
				'Avg Makespan',
				'Std Makespan',
				'Min Makespan',
				'Max Makespan',
				'Avg Time (ms)',
			],
		)

		# Normalize data for better visualization
		stats_normalized = stats_df.copy()
		for col in stats_df.columns:
			col_min, col_max = stats_df[col].min(), stats_df[col].max()
			if col_max != col_min:
				stats_normalized[col] = (stats_df[col] - col_min) / (col_max - col_min)
			else:
				stats_normalized[col] = 0.5  # If all values are the same

		# Create heatmap
		sns.heatmap(
			stats_normalized,
			annot=stats_df.round(1),
			fmt='g',
			cmap='RdYlGn_r',
			ax=ax,
			cbar_kws={'label': 'Normalized Score'},
		)

		ax.set_title(
			'Performance Statistics Heatmap\n(Darker = Better Performance)',
			fontsize=12,
			fontweight='bold',
		)
		ax.set_ylabel('Methods', fontsize=10, fontweight='bold')
		ax.set_xlabel('Statistics', fontsize=10, fontweight='bold')

	def _create_summary_table(self, ax):
		"""Create summary table"""
		ax.axis('off')

		# Get top performers
		methods = list(self.results.keys())
		sorted_methods = sorted(methods, key=lambda x: self.results[x]['avg_makespan'])

		# Create table data with simple text
		table_data = []
		for i, method in enumerate(sorted_methods[:5]):  # Top 5
			stats = self.results[method]

			# Simple ranking without special characters
			rank_symbols = [
				'WINNER',
				'RUNNER-UP',
				'3RD PLACE',
				'4TH PLACE',
				'5TH PLACE',
			]
			rank_text = rank_symbols[i] if i < len(rank_symbols) else f'{i + 1}TH PLACE'

			table_data.append([
				f'{rank_text}: {method}',
				f'{stats["avg_makespan"]:.0f}',
				f'±{stats["std_makespan"]:.0f}',
				f'{stats["min_makespan"]:.0f}',
				f'{stats["avg_execution_time"] * 1000:.1f}ms',
			])

		# Create table
		table = ax.table(
			cellText=table_data,
			colLabels=[
				'Rank & Method',
				'Avg Makespan',
				'Std Dev',
				'Best Result',
				'Avg Time',
			],
			cellLoc='center',
			loc='center',
			colWidths=[0.35, 0.15, 0.15, 0.15, 0.15],
		)

		table.auto_set_font_size(False)
		table.set_fontsize(10)
		table.scale(1, 2.5)

		# Style the table
		for i in range(len(table_data) + 1):
			for j in range(5):
				cell = table[(i, j)]
				if i == 0:  # Header
					cell.set_facecolor('#4472C4')
					cell.set_text_props(weight='bold', color='white')
				elif i <= 3:  # Top 3
					cell.set_facecolor('#E8F4FD')
				else:
					cell.set_facecolor('#F8F9FA')
				cell.set_edgecolor('white')
				cell.set_linewidth(2)

	def create_detailed_comparison(self, save_path: str = None):
		"""Create detailed comparison charts"""
		fig, axes = plt.subplots(2, 2, figsize=(16, 12))
		fig.suptitle(
			f'Detailed JSS Performance Analysis - {self.instance_name}',
			fontsize=16,
			fontweight='bold',
		)

		# 1. Episode-by-episode performance
		self._create_episode_performance(axes[0, 0])

		# 2. Box plot comparison
		self._create_enhanced_boxplot(axes[0, 1])

		# 3. Cumulative performance
		self._create_cumulative_performance(axes[1, 0])

		# 4. Statistical significance
		self._create_statistical_analysis(axes[1, 1])

		plt.tight_layout()

		if save_path:
			plt.savefig(save_path, dpi=300, bbox_inches='tight')
			print(f'📊 Detailed comparison saved to {save_path}')

		return fig

	def _create_episode_performance(self, ax):
		"""Create episode-by-episode performance chart"""
		for method in self.results.keys():
			makespans = self.results[method]['all_makespans']
			episodes = range(1, len(makespans) + 1)

			color = self.colors.get(method, '#696969')
			alpha = 1.0 if method.startswith(('Hybrid', 'Adaptive')) else 0.6
			linewidth = 2 if method.startswith(('Hybrid', 'Adaptive')) else 1

			ax.plot(
				episodes,
				makespans,
				label=method,
				color=color,
				alpha=alpha,
				linewidth=linewidth,
				marker='o',
				markersize=3,
			)

		ax.set_xlabel('Episode', fontweight='bold')
		ax.set_ylabel('Makespan', fontweight='bold')
		ax.set_title('Episode-by-Episode Performance', fontweight='bold')
		ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
		ax.grid(True, alpha=0.3)

	def _create_enhanced_boxplot(self, ax):
		"""Create enhanced box plot"""
		makespan_data = []
		labels = []

		for method in self.results.keys():
			makespans = self.results[method]['all_makespans']
			makespan_data.extend(makespans)
			labels.extend([method] * len(makespans))

		df = pd.DataFrame({'Method': labels, 'Makespan': makespan_data})

		# Create box plot with version compatibility
		try:
			# For newer seaborn versions
			sns.boxplot(
				data=df,
				x='Method',
				y='Makespan',
				ax=ax,
				hue='Method',
				palette=[self.colors.get(m, '#696969') for m in df['Method'].unique()],
				legend=False,
			)
		except Exception:
			try:
				# For older seaborn versions
				sns.boxplot(
					data=df,
					x='Method',
					y='Makespan',
					ax=ax,
					palette=[self.colors.get(m, '#696969') for m in df['Method'].unique()],
				)
			except Exception:
				# Ultimate fallback
				sns.boxplot(data=df, x='Method', y='Makespan', ax=ax)

		# Highlight custom agents with error handling
		try:
			unique_methods = df['Method'].unique()
			for i, method in enumerate(unique_methods):
				if method.startswith(('Hybrid', 'Adaptive')) and hasattr(ax, 'artists') and i < len(ax.artists):
					ax.artists[i].set_edgecolor('gold')
					ax.artists[i].set_linewidth(2)
		except (IndexError, AttributeError):
			# Skip highlighting if it fails
			pass

		ax.set_title('Makespan Distribution Analysis', fontweight='bold')
		ax.tick_params(axis='x', rotation=45)
		ax.grid(True, alpha=0.3)

	def _create_cumulative_performance(self, ax):
		"""Create cumulative performance chart"""
		for method in self.results.keys():
			makespans = self.results[method]['all_makespans']
			cumulative_avg = np.cumsum(makespans) / np.arange(1, len(makespans) + 1)
			episodes = range(1, len(makespans) + 1)

			color = self.colors.get(method, '#696969')
			alpha = 1.0 if method.startswith(('Hybrid', 'Adaptive')) else 0.6
			linewidth = 2 if method.startswith(('Hybrid', 'Adaptive')) else 1

			ax.plot(
				episodes,
				cumulative_avg,
				label=method,
				color=color,
				alpha=alpha,
				linewidth=linewidth,
			)

		ax.set_xlabel('Episode', fontweight='bold')
		ax.set_ylabel('Cumulative Average Makespan', fontweight='bold')
		ax.set_title('Cumulative Performance Convergence', fontweight='bold')
		ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
		ax.grid(True, alpha=0.3)

	def _create_statistical_analysis(self, ax):
		"""Create statistical analysis visualization"""
		methods = list(self.results.keys())

		# Calculate confidence intervals
		means = []
		ci_lower = []
		ci_upper = []

		for method in methods:
			makespans = np.array(self.results[method]['all_makespans'])
			mean = np.mean(makespans)
			std_err = np.std(makespans) / np.sqrt(len(makespans))
			ci = 1.96 * std_err  # 95% confidence interval

			means.append(mean)
			ci_lower.append(mean - ci)
			ci_upper.append(mean + ci)

		# Create error bar plot
		x_pos = range(len(methods))
		colors = [self.colors.get(m, '#696969') for m in methods]

		bars = ax.bar(
			x_pos,
			means,
			yerr=[
				np.array(means) - np.array(ci_lower),
				np.array(ci_upper) - np.array(means),
			],
			capsize=5,
			color=colors,
			alpha=0.7,
			edgecolor='black',
		)

		# Highlight custom agents
		for i, method in enumerate(methods):
			if method.startswith(('Hybrid', 'Adaptive')):
				bars[i].set_alpha(1.0)
				bars[i].set_edgecolor('gold')
				bars[i].set_linewidth(2)

		ax.set_xticks(x_pos)
		ax.set_xticklabels(methods, rotation=45, ha='right')
		ax.set_ylabel('Average Makespan', fontweight='bold')
		ax.set_title('Statistical Analysis (95% Confidence Intervals)', fontweight='bold')
		ax.grid(True, alpha=0.3)

	def create_gantt_charts_for_agents(self, gantt_data: Dict, save_dir: str = 'results'):
		"""Create Gantt charts for custom agents"""
		from pathlib import Path

		# Create gantt charts directory
		gantt_dir = Path(save_dir) / 'gantt_charts'
		gantt_dir.mkdir(exist_ok=True)

		for agent_name, data in gantt_data.items():
			schedule = data['schedule']
			makespan = data['makespan']

			# Create individual Gantt chart
			self._create_single_gantt_chart(agent_name, schedule, makespan, str(gantt_dir))

		# Create comparison Gantt chart
		if len(gantt_data) > 1:
			self._create_comparison_gantt_chart(gantt_data, str(gantt_dir))

		print(f'🎯 Gantt charts saved to {gantt_dir}')

	def _create_single_gantt_chart(self, agent_name: str, schedule: List, makespan: float, save_dir: str):
		"""Create a single Gantt chart for one agent"""
		if not schedule:
			print(f'Warning: No schedule data for {agent_name}')
			return

		# Apply ControllerJSSAgent styling
		plt.style.use('seaborn-v0_8-whitegrid')
		sns.set_palette('husl')

		fig, ax = plt.subplots(figsize=(12, 8))

		# Get unique machines and jobs
		machines = sorted(list(set(task[1] for task in schedule)))
		jobs = sorted(list(set(task[0] for task in schedule)))

		# Use seaborn husl color palette like ControllerJSSAgent
		colors = sns.color_palette('husl', n_colors=len(jobs))
		job_colors = {job: colors[i % len(colors)] for i, job in enumerate(jobs)}

		# Plot tasks
		for task in schedule:
			job_id, machine_id, start_time, end_time = task
			duration = end_time - start_time
			machine_idx = machines.index(machine_id)

			# Plot task bar with ControllerJSSAgent styling
			ax.barh(
				machine_idx,
				duration,
				left=start_time,
				height=0.4,
				color=job_colors[job_id],
				edgecolor='black',
				alpha=0.8,
			)

		# Customize plot to match ControllerJSSAgent style
		ax.set_yticks(range(len(machines)))
		ax.set_yticklabels([f'Machine {m}' for m in machines])
		ax.set_xlabel('Time')
		ax.set_ylabel('Machines')
		ax.set_title(f'JSS Gantt Chart - {agent_name}\nMakespan: {makespan:.1f}')
		ax.grid(True, alpha=0.3)

		# Add legend using mpatches like ControllerJSSAgent
		job_patches = [mpatches.Patch(color=job_colors[job], label=f'Job {job}') for job in sorted(jobs)]
		plt.legend(handles=job_patches, bbox_to_anchor=(1.05, 1), loc='upper left')

		plt.tight_layout()

		# Save the chart
		filename = f'{agent_name.replace(" ", "_")}_gantt.png'
		filepath = Path(save_dir) / filename
		plt.savefig(filepath, dpi=300, bbox_inches='tight')
		plt.close()

		print(f'📊 Gantt chart for {agent_name} saved to {filepath}')

	def _create_comparison_gantt_chart(self, gantt_data: Dict, save_dir: str):
		"""Create a comparison Gantt chart showing both agents side by side"""
		# Apply ControllerJSSAgent styling
		plt.style.use('seaborn-v0_8-whitegrid')
		sns.set_palette('husl')

		fig, axes = plt.subplots(len(gantt_data), 1, figsize=(12, 6 * len(gantt_data)))

		if len(gantt_data) == 1:
			axes = [axes]  # Make it iterable for single plot

		fig.suptitle('JSS Gantt Chart Comparison - Custom Agents', fontsize=14)

		# Get all unique jobs across all agents for consistent coloring
		all_jobs = set()
		for data in gantt_data.values():
			if data['schedule']:
				all_jobs.update(task[0] for task in data['schedule'])
		all_jobs = sorted(list(all_jobs))

		# Use seaborn husl color palette for consistency
		colors = sns.color_palette('husl', n_colors=len(all_jobs))
		job_colors = {job: colors[i % len(colors)] for i, job in enumerate(all_jobs)}

		for idx, (agent_name, data) in enumerate(gantt_data.items()):
			schedule = data['schedule']
			makespan = data['makespan']
			ax = axes[idx]

			if not schedule:
				ax.text(
					0.5,
					0.5,
					f'No schedule data for {agent_name}',
					ha='center',
					va='center',
					transform=ax.transAxes,
					fontsize=12,
				)
				ax.set_title(f'{agent_name} - No Data')
				continue

			# Get unique machines for this agent
			machines = sorted(list(set(task[1] for task in schedule)))

			# Plot tasks
			for task in schedule:
				job_id, machine_id, start_time, end_time = task
				duration = end_time - start_time
				machine_idx = machines.index(machine_id)

				# Plot task bar with ControllerJSSAgent styling
				ax.barh(
					machine_idx,
					duration,
					left=start_time,
					height=0.4,
					color=job_colors[job_id],
					edgecolor='black',
					alpha=0.8,
				)

			# Customize subplot to match ControllerJSSAgent style
			ax.set_yticks(range(len(machines)))
			ax.set_yticklabels([f'Machine {m}' for m in machines])
			ax.set_ylabel('Machines')
			ax.set_title(f'{agent_name} - Makespan: {makespan:.1f}')
			ax.grid(True, alpha=0.3)

			# Set consistent x-axis limits for comparison
			max_makespan = max(data['makespan'] for data in gantt_data.values())
			ax.set_xlim(0, max_makespan * 1.05)

			# Add legend only to the last subplot using mpatches
			if idx == len(gantt_data) - 1:
				job_patches = [mpatches.Patch(color=job_colors[job], label=f'Job {job}') for job in sorted(all_jobs)]
				ax.legend(handles=job_patches, bbox_to_anchor=(1.05, 1), loc='upper left')

		# Add common x-label to the bottom subplot
		axes[-1].set_xlabel('Time')

		plt.tight_layout()

		# Save the comparison chart
		filepath = Path(save_dir) / 'custom_agents_gantt_comparison.png'
		plt.savefig(filepath, dpi=300, bbox_inches='tight')
		plt.close()

		print(f'📊 Comparison Gantt chart saved to {filepath}')

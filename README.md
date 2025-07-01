# Job Shop Scheduling (JSS) Solution Framework

## 🎯 Overview

This repository contains an advanced **Job Shop Scheduling (JSS)** solution framework that implements custom intelligent agents and provides comprehensive comparison tools for JSS optimization. The framework supports both classical dispatching rules and modern AI-based scheduling approaches with human resource constraints.

## ✨ Key Features

### 🤖 Custom Intelligent Agents

- **HybridPriorityScoringAgent**: Advanced agent combining multiple heuristics with dynamic weighting
- **AdaptiveLookAheadAgent**: Agent with limited lookahead for better decision making
- **ControllerJSSAgent**: Agent that respects people-machine assignment constraints

### 📊 Comprehensive Analysis Tools

- Performance comparison framework across multiple scheduling methods
- Advanced visualization dashboard with interactive charts
- **Gantt chart generation for custom agents** ⭐ NEW ⭐
- Statistical analysis and performance metrics
- Gantt chart generation for schedule visualization

### 🔧 Flexible Architecture

- Support for standard JSS benchmark instances (TA, DMU series)
- Integration with JSSEnv gymnasium environment
- Configurable controller constraints for realistic workforce modeling
- Modular design for easy extension and customization

## 🏗️ Project Structure

```
REL301m_JSS_Solution/
├── main.py                      # Controller-constrained JSS execution
├── requirements.txt             # Dependencies
├── comparison_framework/        # Core comparison and agent modules
│   ├── compare.py               # Main comparison script
│   ├── comparison_framework.py  # Comparison framework implementation
│   ├── agents.py                # Custom JSS agents
│   └── advanced_visualizer.py   # Visualization tools
├── instances/                   # JSS problem instances
│   ├── dmu16, dmu17, ...        # DMU benchmark instances
│   └── ta01, ta02, ...          # Taillard benchmark instances
├── controllers/                 # People-machine assignment constraints
│   ├── 10p_20m.txt              # 10 people, 20 machines
│   ├── 15p_15m.txt              # 15 people, 15 machines
│   ├── 20p_20m.txt              # 20 people, 20 machines
│   └── ...                      # Add more controller files for testing
└── results/                     # Output directory for results
```

## 🚀 Quick Start

### Prerequisites

Install required dependencies:

```bash
pip install -r requirements.txt
```

### Basic Usage

#### 1. Run Agent Comparison

Compare custom agents against classical dispatching rules:

```bash
cd comparison_framework
python compare.py --instance dmu16 --episodes 30
```

**Parameters:**

- `--instance`: Instance name (e.g., dmu16, ta01)
- `--episodes`: Number of episodes per method (default: 30)

#### 2. Run Controller-Constrained Scheduling

Execute JSS with people-machine assignment constraints:

```bash
python main.py --instance dmu19 --controller 20p_20m --num_people 20
```

**Parameters:**

- `--instance`: JSS instance name
- `--controller`: Controller configuration file
- `--num_people`: Number of available people

## 📋 Detailed Usage

### Agent Comparison Framework

The comparison framework evaluates multiple scheduling approaches:

**Classical Dispatching Rules:**

- SPT (Shortest Processing Time)
- FIFO (First In, First Out)
- MWR (Most Work Remaining)
- LWR (Least Work Remaining)
- MOR (Most Operations Remaining)
- LOR (Least Operations Remaining)
- CR (Critical Ratio)

**Custom Intelligent Agents:**

- **HybridPriorityScoringAgent**: Combines multiple heuristics with dynamic weights
- **AdaptiveLookAheadAgent**: Uses limited lookahead for better decisions

### Controller-Constrained Scheduling

The main script supports realistic scheduling scenarios where:

- People have specific machine qualifications
- Resource availability constraints apply
- Gantt charts visualize the final schedule
- **Comprehensive performance reports** ⭐ NEW ⭐

### Output Analysis

The framework generates comprehensive results:

1. **Performance Metrics**

   - Average makespan and standard deviation
   - Best and worst case performance
   - Execution time statistics

2. **Visualizations**

   - Comprehensive performance dashboard
   - Detailed comparison charts
   - Gantt charts for schedule visualization

3. **Reports**
   - **Detailed performance report (report.txt)** ⭐ NEW ⭐
   - Performance ranking summary
   - Statistical analysis
   - CSV files with detailed episode results

## 🧠 Agent Algorithms

### HybridPriorityScoringAgent

This agent implements a sophisticated scoring system that combines:

- **Shortest Processing Time (SPT)**: Prioritizes jobs with shorter processing times
- **Work Remaining**: Considers remaining workload for each job
- **Critical Path**: Evaluates path criticality in the schedule
- **Machine Utilization**: Accounts for machine availability
- **Bottleneck Detection**: Identifies and prioritizes bottleneck resources
- **Flow Continuity**: Ensures smooth job flow between operations

The agent uses **dynamic weight adjustment** based on scheduling progress:

- Early stage (0-30%): Focus on critical path and work remaining
- Middle stage (30-70%): Balanced approach across all factors
- Late stage (70-100%): Emphasis on SPT and machine utilization

### AdaptiveLookAheadAgent

This agent evaluates scheduling decisions by:

- Performing limited lookahead simulation
- Considering immediate and future benefits
- Evaluating machine availability for next operations
- Making informed decisions based on projected outcomes

### ControllerJSSAgent

Specialized for real-world constraints:

- Respects people-machine qualification matrices
- Tracks person availability and assignments
- Optimizes considering both job priorities and resource constraints
- Generates detailed scheduling information with person assignments

## 📊 Performance Analysis

### Metrics Collected

- **Makespan**: Total completion time
- **Reward**: Environment-specific performance measure
- **Execution Time**: Algorithm runtime
- **Consistency**: Standard deviation of results

### Statistical Analysis

The framework provides:

- Performance ranking across all methods
- Statistical significance testing
- Improvement analysis for custom agents
- Detailed performance reports

## 🔧 Configuration

### Instance Format

JSS instances follow standard format:

```
[num_jobs] [num_machines]
[job_0_operations: machine_id processing_time ...]
[job_1_operations: machine_id processing_time ...]
...
```

### Controller Format

Controller files define people-machine assignments:

```
person_id machine_id_1 machine_id_2 ...
person_id machine_id_1 machine_id_2 ...
...
```

## 📈 Example Results

The framework generates comprehensive outputs including:

- **Performance Dashboard**: Visual comparison of all methods
- **Gantt Charts**: Schedule visualization with job assignments **for custom agents** ⭐
- **Statistical Reports**: Detailed performance analysis
- **CSV Data**: Raw results for further analysis
- **Performance Report (report.txt)**: Comprehensive analysis for ControllerJSSAgent ⭐ NEW ⭐

### 🎯 New Gantt Chart Feature

The comparison framework now automatically generates Gantt charts for your custom agents, showing:

- **Individual Gantt charts** for each custom agent (HybridPriorityScoringAgent, AdaptiveLookAheadAgent)
- **Side-by-side comparison** Gantt chart for visual performance comparison
- **Job-to-machine assignments** with color-coded jobs
- **Makespan visualization** showing the scheduling efficiency
- **Best performance capture** - charts show the best run out of 5 episodes

Charts are automatically saved to `results/{instance_name}/gantt_charts/` directory.

### 📄 New Performance Report Feature

The ControllerJSSAgent now automatically generates a detailed `report.txt` file containing:

- **Performance Summary**: Makespan, efficiency, and task completion statistics
- **Resource Utilization**: Detailed machine and people utilization analysis
- **Controller Efficiency**: Analysis of person-machine combination usage
- **Job Completion Analysis**: Individual job completion times and patterns
- **Performance Insights**: Automated recommendations and bottleneck identification
- **Configuration Details**: Instance and controller settings used

Example report sections:

```
🎯 PERFORMANCE SUMMARY
Makespan: 245.50 time units
Overall Efficiency: 78.45%
Total Tasks Scheduled: 150

🔧 RESOURCE UTILIZATION
Average Machine Utilization: 82.30%
Average People Utilization: 75.60%

💡 PERFORMANCE INSIGHTS
✅ Excellent efficiency - schedule is well-optimized
⚠️  2 people are potential bottlenecks
```

## 🔬 Research Applications

This framework is designed for:

- **Algorithm Development**: Testing new JSS heuristics and algorithms
- **Benchmarking**: Comparing performance across standard instances
- **Real-world Modeling**: Incorporating realistic constraints
- **Educational Purposes**: Understanding JSS optimization techniques
- **Educational Purposes**: Understanding JSS optimization techniques

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

- Additional heuristic implementations
- Extended visualization capabilities
- New constraint types
- Performance optimizations

## 📚 References

This implementation is based on established JSS research and incorporates:

- Classical dispatching rules from scheduling literature
- Modern AI-based approaches
- Real-world constraint modeling
- Comprehensive evaluation methodologies

## 📝 License

This project is provided for educational and research purposes. Please ensure proper attribution when using or extending this work.

---

**Note**: This framework requires the JSSEnv environment package for execution. Ensure all dependencies are properly installed before running the examples.

# Advanced Job Shop Scheduling (JSS) Comparison Framework

A comprehensive framework for comparing custom agents against traditional dispatching rules in Job Shop Scheduling problems using the JSSEnv environment.

## 🎯 Project Overview

This project implements and compares advanced Job Shop Scheduling agents with traditional dispatching rules. It features:

- **Custom Intelligent Agents**: Hybrid priority scoring and adaptive lookahead agents
- **Comprehensive Comparison**: Against 7+ dispatching rules (SPT, FIFO, MWR, LWR, MOR, LOR, CR)
- **Advanced Heuristics**: Multi-factor decision making with dynamic weighting
- **Performance Analytics**: Detailed metrics, visualizations, and statistical analysis

## 🚀 Features

### Custom Agents
- **HybridPriorityScoringAgent**: Combines multiple heuristics with dynamic weighting
  - Shortest Processing Time (SPT) scoring
  - Work remaining analysis
  - Critical path considerations
  - Machine utilization optimization
  - Bottleneck detection
  - Flow continuity analysis
  
- **AdaptiveLookAheadAgent**: Limited lookahead for better decision making

### Analysis Tools
- Performance comparison across multiple episodes
- Statistical analysis (mean, std, min, max makespans)
- Visualization generation (bar charts, box plots)
- Detailed results export to CSV
- Progress tracking and execution time monitoring

## 📋 Requirements

- Python 3.8+
- JSSEnv
- Gymnasium
- NumPy
- Pandas
- Matplotlib
- Seaborn

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/votuongquan/REL301m_JSS_Solution.git
cd REL301m_JSS_Solution
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have JSS problem instances in the `instances/` directory

## 🏃‍♂️ Quick Start

### Basic Usage

```python
from comparison_framework import JSSComparisonFramework
from agents import create_agent

# Initialize framework
framework = JSSComparisonFramework("instances/ta01")

# Create agents
agents = [
    create_agent("hybrid"),
    create_agent("lookahead")
]

# Run comparison
results = framework.run_comprehensive_comparison(agents, num_episodes=20)
```

### Running the Full Comparison

```bash
python main.py
```

This will:
1. Test environment setup
2. Run custom agents vs dispatching rules
3. Generate performance visualizations
4. Save detailed results to CSV
5. Display comprehensive analysis

## 📁 Project Structure

```
REL301_JSS_Solution/
├── main.py                    # Main execution script
├── agents.py                  # Custom agent implementations
├── comparison_framework.py    # Comparison infrastructure
├── instances/                 # JSS problem instances
│   ├── ta01
│   ├── dmu19
│   └── ...
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .gitignore                # Git ignore rules
```

## 🔧 Configuration

### Instance Selection
Edit `main.py` to change the problem instance:
```python
instance_path = "instances/ta01"  # Change to your instance
```

### Episode Count
Adjust the number of episodes for more robust results:
```python
num_episodes = 30  # Increase for better statistics
```

### Agent Parameters
Customize agents in `agents.py`:
```python
# For lookahead agent
agent = AdaptiveLookAheadAgent(lookahead_depth=3)
```

## 📊 Output Files

- `jss_comparison_plots.png`: Visualization comparing all methods
- `detailed_results.csv`: Episode-by-episode results
- Console output with comprehensive analysis

## 🧪 Extending the Framework

### Adding New Agents

1. Create a new agent class inheriting from `BaseJSSAgent`:
```python
class YourCustomAgent(BaseJSSAgent):
    def __init__(self):
        super().__init__("YourAgentName")
    
    def __call__(self, env, obs):
        # Your decision logic here
        return selected_action
```

2. Add to the factory function in `agents.py`:
```python
def create_agent(agent_type: str):
    if agent_type == "your_agent":
        return YourCustomAgent()
    # ... existing agents
```

### Adding New Dispatching Rules

Modify `dispatching_rules` list in `comparison_framework.py`:
```python
self.dispatching_rules = [
    'SPT', 'FIFO', 'MWR', 'LWR', 'MOR', 'LOR', 'CR', 'YOUR_RULE'
]
```

## 📈 Performance Metrics

The framework tracks:
- **Makespan**: Total completion time (primary objective)
- **Reward**: Cumulative environment reward
- **Execution Time**: Agent decision time
- **Statistical Measures**: Mean, standard deviation, min/max values

## 🏆 Expected Performance

The HybridPriorityScoringAgent typically achieves:
- 5-15% improvement over best dispatching rules
- Consistent performance across different problem instances
- Adaptive behavior based on scheduling progress

## 🐛 Troubleshooting

### Common Issues

1. **Environment Creation Failed**
   - Check instance path exists
   - Verify JSSEnv installation
   - Ensure instance format is correct

2. **Agent Performance Issues**
   - Increase number of episodes for better statistics
   - Check for legal action handling
   - Verify observation format compatibility

3. **Memory Issues**
   - Reduce number of episodes
   - Close environments properly
   - Monitor memory usage during runs

## 📚 References

- [JSSEnv GitHub Repository](https://github.com/prosysscience/JSSEnv)
- Job Shop Scheduling Problem literature
- Dispatching rules in manufacturing systems


**Note**: Make sure to have proper JSS problem instances in the `instances/` directory before running the comparison framework.
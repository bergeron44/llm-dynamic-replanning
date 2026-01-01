# Comparative Cognitive Architectures Experiment Suite

## 🚀 Quick Start

### 1. Run All Experiments (16 combinations)
```bash
./run_batch_experiments.sh
```
This will run all 4 scenarios × 4 algorithms = 16 experiments and save results to `experiment_results.csv`.

### 2. Generate Analysis Graphs
```bash
python generate_experiment_graphs.py
```
Creates 4 publication-ready plots and a summary report.

## 📊 Expected Results Patterns

### Scenario 1 (Irrelevant - Old Tree)
- **Algorithm A (Blind)**: Low compute time, no replans
- **Algorithm B (Obsessive)**: High compute time (wasted on irrelevant discovery)
- **Algorithm C (Smart)**: Low compute time (filters noise effectively)
- **Algorithm D (Heuristic)**: Medium compute time

### Scenario 4 (Sweet Spot - Osher Ad: Cheap & Close)
- **Algorithm A (Blind)**: High final cost (missed opportunity)
- **Algorithms B/C/D**: Lower costs, but C provides better reasoning quality

## 📈 Generated Visualizations

After running `generate_experiment_graphs.py`, you'll get:

1. **`cost_comparison.png`** - Cost efficiency across scenarios
2. **`compute_time_comparison.png`** - Computational efficiency
3. **`replans_comparison.png`** - Replanning behavior patterns
4. **`algorithm_efficiency_heatmap.png`** - Overall efficiency heatmap
5. **`experiment_summary.txt`** - Statistical summary report

## 🎯 Research Insights

The experiments demonstrate how different cognitive architectures balance:
- **Perception accuracy** vs **decision quality**
- **Computational efficiency** vs **economic outcomes**
- **Conservatism** vs **opportunism** in replanning

## ⚙️ Customization

### Test Specific Combinations
```bash
ALGORITHM_MODE=C SCENARIO_ID=SCENARIO_4 python run_live_dashboard.py
```

### Modify Batch Script
Edit `run_batch_experiments.sh` to change timeout duration or add more scenarios.

### Customize Graphs
Modify `generate_experiment_graphs.py` to add new visualizations or metrics.

## 📋 Current Results

Check `experiment_results.csv` for raw data with columns:
- `scenario_id`, `algorithm_mode`, `total_steps`, `total_cost`
- `compute_time_seconds`, `replans_count`, `victory_reached`

Run the batch script and share the CSV results or generated graphs! 📊
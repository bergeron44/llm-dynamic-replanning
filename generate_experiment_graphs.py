"""
Experiment Results Visualizer
Creates comparative graphs from experiment_results.csv for the research paper
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_experiment_data(csv_file="experiment_results.csv"):
    """Load and preprocess experiment data"""
    df = pd.read_csv(csv_file)

    # Convert data types
    df['total_steps'] = pd.to_numeric(df['total_steps'], errors='coerce')
    df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce')
    df['compute_time_seconds'] = pd.to_numeric(df['compute_time_seconds'], errors='coerce')
    df['replans_count'] = pd.to_numeric(df['replans_count'], errors='coerce')

    # Fill NaN values
    df = df.fillna(0)

    return df

def create_cost_comparison_plot(df, output_file="cost_comparison.png"):
    """Create bar chart comparing total cost by scenario and algorithm"""
    plt.figure(figsize=(12, 8))

    # Create grouped bar chart
    scenarios = df['scenario_id'].unique()
    algorithms = df['algorithm_mode'].unique()

    x = np.arange(len(scenarios))
    width = 0.2

    for i, algo in enumerate(sorted(algorithms)):
        algo_data = df[df['algorithm_mode'] == algo]
        means = []
        stds = []

        for scenario in scenarios:
            scenario_data = algo_data[algo_data['scenario_id'] == scenario]
            if len(scenario_data) > 0:
                means.append(scenario_data['total_cost'].mean())
                stds.append(scenario_data['total_cost'].std())
            else:
                means.append(0)
                stds.append(0)

        plt.bar(x + i*width, means, width, label=f'Algorithm {algo}',
                yerr=stds, capsize=5, alpha=0.8)

    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Total Cost ($)', fontsize=12)
    plt.title('Cost Comparison: Algorithm Performance Across Scenarios', fontsize=14, fontweight='bold')
    plt.xticks(x + width*1.5, [s.replace('SCENARIO_', '') for s in scenarios])
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"💰 Cost comparison plot saved to {output_file}")

def create_compute_time_plot(df, output_file="compute_time_comparison.png"):
    """Create bar chart comparing compute time by scenario and algorithm"""
    plt.figure(figsize=(12, 8))

    scenarios = df['scenario_id'].unique()
    algorithms = df['algorithm_mode'].unique()

    x = np.arange(len(scenarios))
    width = 0.2

    for i, algo in enumerate(sorted(algorithms)):
        algo_data = df[df['algorithm_mode'] == algo]
        means = []
        stds = []

        for scenario in scenarios:
            scenario_data = algo_data[algo_data['scenario_id'] == scenario]
            if len(scenario_data) > 0:
                means.append(scenario_data['compute_time_seconds'].mean())
                stds.append(scenario_data['compute_time_seconds'].std())
            else:
                means.append(0)
                stds.append(0)

        plt.bar(x + i*width, means, width, label=f'Algorithm {algo}',
                yerr=stds, capsize=5, alpha=0.8)

    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Compute Time (seconds)', fontsize=12)
    plt.title('Efficiency Comparison: Compute Time Across Scenarios', fontsize=14, fontweight='bold')
    plt.xticks(x + width*1.5, [s.replace('SCENARIO_', '') for s in scenarios])
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"⚡ Compute time comparison plot saved to {output_file}")

def create_replans_plot(df, output_file="replans_comparison.png"):
    """Create bar chart showing replanning frequency"""
    plt.figure(figsize=(12, 8))

    scenarios = df['scenario_id'].unique()
    algorithms = df['algorithm_mode'].unique()

    x = np.arange(len(scenarios))
    width = 0.2

    for i, algo in enumerate(sorted(algorithms)):
        algo_data = df[df['algorithm_mode'] == algo]
        means = []

        for scenario in scenarios:
            scenario_data = algo_data[algo_data['scenario_id'] == scenario]
            if len(scenario_data) > 0:
                means.append(scenario_data['replans_count'].mean())
            else:
                means.append(0)

        plt.bar(x + i*width, means, width, label=f'Algorithm {algo}', alpha=0.8)

    plt.xlabel('Scenario', fontsize=12)
    plt.ylabel('Average Replans Count', fontsize=12)
    plt.title('Replanning Behavior: Frequency Across Scenarios', fontsize=14, fontweight='bold')
    plt.xticks(x + width*1.5, [s.replace('SCENARIO_', '') for s in scenarios])
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"🔄 Replans comparison plot saved to {output_file}")

def create_algorithm_efficiency_heatmap(df, output_file="algorithm_efficiency_heatmap.png"):
    """Create heatmap showing algorithm efficiency across scenarios"""
    plt.figure(figsize=(10, 8))

    # Create pivot table for cost
    cost_pivot = df.pivot_table(values='total_cost', index='scenario_id',
                               columns='algorithm_mode', aggfunc='mean')

    # Create pivot table for compute time
    time_pivot = df.pivot_table(values='compute_time_seconds', index='scenario_id',
                               columns='algorithm_mode', aggfunc='mean')

    # Create efficiency score (lower cost + lower time = better)
    efficiency_score = 1 / (cost_pivot * time_pivot)

    # Plot heatmap
    sns.heatmap(efficiency_score, annot=True, fmt='.2f', cmap='RdYlGn_r',
                cbar_kws={'label': 'Efficiency Score (higher = better)'})

    plt.title('Algorithm Efficiency Heatmap\n(Lower Cost × Lower Time = Higher Efficiency)',
              fontsize=14, fontweight='bold')
    plt.xlabel('Algorithm', fontsize=12)
    plt.ylabel('Scenario', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"🎯 Efficiency heatmap saved to {output_file}")

def generate_summary_report(df, output_file="experiment_summary.txt"):
    """Generate text summary of experiment results"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🧪 COMPARATIVE COGNITIVE ARCHITECTURES EXPERIMENT RESULTS\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Total Experiments: {len(df)}\n")
        f.write(f"Scenarios Tested: {len(df['scenario_id'].unique())}\n")
        f.write(f"Algorithms Tested: {len(df['algorithm_mode'].unique())}\n\n")

        f.write("📊 KEY FINDINGS:\n\n")

        # Best performing algorithm by cost
        best_cost = df.groupby('algorithm_mode')['total_cost'].mean().idxmin()
        best_cost_value = df.groupby('algorithm_mode')['total_cost'].mean().min()

        f.write(f"🏆 Most Cost-Effective Algorithm: {best_cost} (${best_cost_value:.2f} avg cost)\n")

        # Fastest algorithm by compute time
        fastest = df.groupby('algorithm_mode')['compute_time_seconds'].mean().idxmin()
        fastest_value = df.groupby('algorithm_mode')['compute_time_seconds'].mean().min()

        f.write(f"⚡ Fastest Algorithm: {fastest} ({fastest_value:.2f}s avg compute time)\n")

        # Most conservative (least replans)
        conservative = df.groupby('algorithm_mode')['replans_count'].mean().idxmin()
        conservative_value = df.groupby('algorithm_mode')['replans_count'].mean().min()

        f.write(f"🎭 Most Conservative Algorithm: {conservative} ({conservative_value:.1f} avg replans)\n\n")

        f.write("📈 DETAILED STATISTICS:\n\n")

        for algo in sorted(df['algorithm_mode'].unique()):
            algo_data = df[df['algorithm_mode'] == algo]
            f.write(f"Algorithm {algo}:\n")
            f.write(f"   • Average Cost: ${algo_data['total_cost'].mean():.2f}\n")
            f.write(f"   • Average Compute Time: {algo_data['compute_time_seconds'].mean():.2f}s\n")
            f.write(f"   • Average Replans: {algo_data['replans_count'].mean():.1f}\n")
            f.write(f"   • Experiments: {len(algo_data)}\n")
            f.write("\n")

    print(f"📋 Summary report saved to {output_file}")

def main():
    """Main function to generate all graphs and reports"""
    print("🎨 Generating Experiment Visualization Suite...")

    # Check if CSV exists
    csv_file = "experiment_results.csv"
    if not Path(csv_file).exists():
        print(f"❌ Error: {csv_file} not found!")
        return

    # Load data
    df = load_experiment_data(csv_file)
    print(f"📊 Loaded {len(df)} experiment results")

    if len(df) == 0:
        print("❌ No data found in CSV!")
        return

    # Generate all plots
    create_cost_comparison_plot(df)
    create_compute_time_plot(df)
    create_replans_plot(df)
    create_algorithm_efficiency_heatmap(df)

    # Generate summary report
    generate_summary_report(df)

    print("✅ Visualization suite complete!")
    print("📁 Generated files:")
    print("   • cost_comparison.png")
    print("   • compute_time_comparison.png")
    print("   • replans_comparison.png")
    print("   • algorithm_efficiency_heatmap.png")
    print("   • experiment_summary.txt")

if __name__ == "__main__":
    main()

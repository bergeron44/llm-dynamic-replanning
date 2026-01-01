#!/usr/bin/env python3
"""
Comparative Experiment Runner
Runs all 4 algorithms (A, B, C, D) on 4 different mazes (seeds) with SCENARIO_3.
Each algorithm runs on the same maze (same seed) for fair comparison.
"""

import os
import subprocess
import sys
from datetime import datetime

# Configuration
SEEDS = [1001, 1002, 1003, 1004]  # 4 different mazes
ALGORITHMS = ['A', 'B', 'C', 'D']
SCENARIO = 'SCENARIO_3'
TIMEOUT_SECONDS = 600  # 10 minutes per run

def run_single_experiment(seed, algorithm, scenario):
    """
    Run a single experiment with specified seed, algorithm, and scenario.
    
    Args:
        seed: Seed value for maze generation
        algorithm: Algorithm mode (A/B/C/D)
        scenario: Scenario ID (e.g., 'SCENARIO_3')
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"🎲 SEED: {seed} | 🤖 ALGORITHM: {algorithm} | 📋 SCENARIO: {scenario}")
    print(f"{'='*70}")
    
    # Prepare environment variables
    env = os.environ.copy()
    env['USE_FIXED_SEED'] = 'true'  # Use fixed seed for reproducibility
    env['SEED'] = str(seed)
    env['ALGORITHM_MODE'] = algorithm
    env['SCENARIO_ID'] = scenario
    
    try:
        # Run the experiment with timeout
        result = subprocess.run(
            [sys.executable, 'run_live_dashboard.py'],
            env=env,
            timeout=TIMEOUT_SECONDS,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Seed {seed}, Algorithm {algorithm}")
            return True
        else:
            print(f"❌ FAILED: Seed {seed}, Algorithm {algorithm} (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: Seed {seed}, Algorithm {algorithm} (exceeded {TIMEOUT_SECONDS}s)")
        return False
    except Exception as e:
        print(f"❌ ERROR: Seed {seed}, Algorithm {algorithm} - {str(e)}")
        return False

def main():
    """Main experiment runner"""
    print("\n" + "="*70)
    print("🚀 STARTING COMPARATIVE EXPERIMENT")
    print("="*70)
    print(f"📋 Scenario: {SCENARIO}")
    print(f"🎲 Seeds: {SEEDS} (4 different mazes)")
    print(f"🤖 Algorithms: {ALGORITHMS}")
    print(f"📊 Total runs: {len(SEEDS) * len(ALGORITHMS)} experiments")
    print("="*70)
    
    start_time = datetime.now()
    results = {}
    
    # Run experiments: for each seed, run all algorithms
    for seed in SEEDS:
        print(f"\n{'#'*70}")
        print(f"# 🎲 MAZE {seed} - Running all algorithms on the same maze")
        print(f"{'#'*70}")
        
        seed_results = {}
        for algorithm in ALGORITHMS:
            success = run_single_experiment(seed, algorithm, SCENARIO)
            seed_results[algorithm] = success
            
            # Brief pause between runs
            import time
            time.sleep(1)
        
        results[seed] = seed_results
        
        # Summary for this seed
        print(f"\n📊 Results for SEED {seed}:")
        for algo, success in seed_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} Algorithm {algo}")
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    print(f"⏱️  Total duration: {duration}")
    print(f"🎲 Total seeds tested: {len(SEEDS)}")
    print(f"🤖 Algorithms per seed: {len(ALGORITHMS)}")
    print(f"📈 Total experiments: {len(SEEDS) * len(ALGORITHMS)}")
    
    print("\n📋 Results by Seed:")
    for seed, seed_results in results.items():
        successful = sum(1 for s in seed_results.values() if s)
        total = len(seed_results)
        print(f"  SEED {seed}: {successful}/{total} successful")
    
    print("\n📋 Results by Algorithm:")
    for algo in ALGORITHMS:
        successful = sum(1 for seed_results in results.values() if seed_results.get(algo, False))
        total = len(SEEDS)
        print(f"  Algorithm {algo}: {successful}/{total} successful")
    
    print("\n" + "="*70)
    print("✅ EXPERIMENT COMPLETE")
    print("="*70)
    print("📁 Results saved to: experiment_results.csv")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()


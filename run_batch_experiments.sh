#!/bin/bash

echo "🚀 Starting Batch Experiment Run with Shared Seeds..."
echo "כל תרחיש מקבל seed קבוע - כל האלגוריתמים רצים על אותו לוח!"
echo ""

# Define arrays for Scenarios and Algorithms
SCENARIOS=("SCENARIO_1" "SCENARIO_2" "SCENARIO_3" "SCENARIO_4")
ALGOS=("A" "B" "C" "D")

# Create seeds for each scenario (deterministic but different per scenario)
# Use simple variable assignment for compatibility
SEED_SCENARIO_1=12345
SEED_SCENARIO_2=23456
SEED_SCENARIO_3=34567
SEED_SCENARIO_4=45678

# Loop through scenarios (each gets its own seed)
for scen in "${SCENARIOS[@]}"; do
    # Get seed dynamically using variable indirection
    seed_var="SEED_$scen"
    seed=${!seed_var}

    echo "🎲 ================================================"
    echo "🎲 SCENARIO: $scen (Seed: $seed)"
    echo "🎲 כל האלגוריתמים ירוצו על אותו לוח!"
    echo "🎲 ================================================"

    # For each scenario, run all algorithms with the SAME seed
    for algo in "${ALGOS[@]}"; do
        echo "🤖 Running: $scen + $algo (Seed: $seed)"

        # Run the simulation with environment variables
        # Use 'timeout' to prevent stuck loops from halting the batch
        SEED=$seed ALGORITHM_MODE=$algo SCENARIO_ID=$scen timeout 300s python run_live_dashboard.py

        # Optional: Sleep briefly to let files close/save
        sleep 1
        echo ""
    done
done

echo "✅ Batch Experiment Complete!"
echo "📊 כל תרחיש רץ עם seed קבוע - השוואה הוגנת!"
echo "📁 Check experiment_results.csv"

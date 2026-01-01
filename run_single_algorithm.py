#!/usr/bin/env python3
"""
Run single algorithm on all scenarios for external review
"""

import os
import subprocess
import time

def run_algorithm(algorithm, scenarios):
    """Run single algorithm on all scenarios"""

    print(f"🔬 הרצת אלגוריתם {algorithm} על כל התרחישים")
    print("=" * 50)

    # Seeds for each scenario
    seeds = {
        'SCENARIO_1': 12345,
        'SCENARIO_2': 23456,
        'SCENARIO_3': 34567,
        'SCENARIO_4': 45678
    }

    for scenario in scenarios:
        seed = seeds[scenario]

        print(f"🎯 תרחיש {scenario} (Seed: {seed})")
        print("-" * 30)

        # Set environment variables
        env = os.environ.copy()
        env['ALGORITHM_MODE'] = algorithm
        env['SCENARIO_ID'] = scenario
        env['SEED'] = str(seed)

        # Run simulation
        try:
            result = subprocess.run(
                ['python', 'run_live_dashboard.py'],
                env=env,
                capture_output=True,
                text=True,
                timeout=180  # 180 seconds timeout for LLM-based runs
            )

            # Check if completed successfully
            if "EXPERIMENT COMPLETED" in result.stdout:
                print("✅ הושלם בהצלחה")
            else:
                print("⚠️ הושלם עם אזהרות")

        except subprocess.TimeoutExpired:
            print("⏰ נתקע - timeout")
        except Exception as e:
            print(f"❌ שגיאה: {e}")

        print()

def show_results():
    """Show current results"""
    print("📊 תוצאות נוכחיות:")
    print("-" * 30)

    try:
        with open('experiment_results.csv', 'r') as f:
            lines = f.readlines()
            print(f"סה\"כ תוצאות: {len(lines) - 1}")  # Minus header

            if len(lines) > 1:
                # Show last result
                last_line = lines[-1].strip()
                print(f"תוצאה אחרונה: {last_line}")
    except FileNotFoundError:
        print("אין קובץ תוצאות")

if __name__ == "__main__":
    scenarios = ['SCENARIO_1', 'SCENARIO_2', 'SCENARIO_3', 'SCENARIO_4']

    print("בחר אלגוריתם להרצה:")
    print("A - העיוור (Baseline)")
    print("B - הטיפש (Naive)")
    print("C - החכם (Smart)")
    print("D - המתמטי (Heuristic)")

    algo = input("הכנס אלגוריתם (A/B/C/D): ").strip().upper()

    if algo in ['A', 'B', 'C', 'D']:
        run_algorithm(algo, scenarios)
        show_results()

        print(f"🎉 סיים הרצת אלגוריתם {algo}")
        print("עכשיו תוכל להראות למבקר החיצוני את התוצאות!")
    else:
        print("אלגוריתם לא תקין")

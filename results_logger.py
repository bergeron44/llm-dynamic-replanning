"""
Results Logger for Comparative Experiment Framework
Logs experimental results to CSV for analysis of different cognitive architectures
"""

import csv
import os
import time
from typing import Dict, Any
from datetime import datetime

class ResultsLogger:
    """
    Handles data collection and logging for comparative experiments
    """

    def __init__(self, csv_file="experiment_results.csv"):
        """
        Initialize the results logger

        Args:
            csv_file: Path to CSV file for storing results
        """
        self.csv_file = csv_file
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'scenario_id',
                    'algorithm_mode',
                    'total_steps',
                    'total_cost',
                    'compute_time_seconds',
                    'replans_count',
                    'llm_calls_count',
                    'true_final_price',
                    'victory_reached',
                    'termination_reason'
                ])

    def log_experiment_result(self,
                            scenario_id: str,
                            algorithm_mode: str,
                            total_steps: int,
                            total_cost: float,
                            compute_time: float,
                            replans_count: int,
                            llm_calls_count: int = 0,
                            true_final_price: float = None,
                            victory_reached: bool = False,
                            termination_reason: str = "completed"):
        """
        Log a single experiment result to CSV

        Args:
            scenario_id: Scenario identifier (e.g., "SCENARIO_1")
            algorithm_mode: Algorithm used (A/B/C/D)
            total_steps: Total steps taken by agent
            total_cost: Final cost (price paid + step cost)
            compute_time: Total time spent on LLM + planning (seconds)
            replans_count: Number of times planner was called
            llm_calls_count: Number of LLM API calls made
            true_final_price: Actual price paid at final destination
            victory_reached: Whether agent reached victory
            termination_reason: Why experiment ended
        """
        timestamp = datetime.now().isoformat()

        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                scenario_id,
                algorithm_mode,
                total_steps,
                f"{total_cost:.2f}",
                f"{compute_time:.3f}",
                replans_count,
                llm_calls_count,
                f"{true_final_price:.2f}" if true_final_price is not None else "",
                victory_reached,
                termination_reason
            ])

    def start_experiment_timer(self) -> float:
        """
        Start timing an experiment

        Returns:
            Start time timestamp
        """
        return time.time()

    def end_experiment_timer(self, start_time: float) -> float:
        """
        End timing and return duration

        Args:
            start_time: Start time from start_experiment_timer()

        Returns:
            Duration in seconds
        """
        return time.time() - start_time

    def get_summary_stats(self, scenario_id: str = None, algorithm_mode: str = None):
        """
        Get summary statistics from logged results

        Args:
            scenario_id: Filter by specific scenario (optional)
            algorithm_mode: Filter by specific algorithm (optional)

        Returns:
            Dict with summary statistics
        """
        results = []
        if not os.path.exists(self.csv_file):
            return {"error": "No results file found"}

        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if scenario_id and row['scenario_id'] != scenario_id:
                    continue
                if algorithm_mode and row['algorithm_mode'] != algorithm_mode:
                    continue
                results.append(row)

        if not results:
            return {"error": "No matching results found"}

        # Calculate statistics
        total_experiments = len(results)
        steps_list = [int(r['total_steps']) for r in results]
        cost_list = [float(r['total_cost']) for r in results]
        time_list = [float(r['compute_time_seconds']) for r in results]
        replans_list = [int(r['replans_count']) for r in results]
        victory_rate = sum(1 for r in results if r['victory_reached'].lower() == 'true') / total_experiments

        return {
            "total_experiments": total_experiments,
            "avg_steps": sum(steps_list) / total_experiments,
            "avg_cost": sum(cost_list) / total_experiments,
            "avg_compute_time": sum(time_list) / total_experiments,
            "avg_replans": sum(replans_list) / total_experiments,
            "victory_rate": victory_rate,
            "min_steps": min(steps_list),
            "max_steps": max(steps_list),
            "min_cost": min(cost_list),
            "max_cost": max(cost_list)
        }

# Global logger instance
logger = ResultsLogger()

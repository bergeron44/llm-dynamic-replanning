"""
Standalone scientific experiment runner to compare algorithms A/B/C/D across
four handcrafted scenarios. The script is non-destructive and does not modify
core modules. It manually injects scenario objects into the grid after
environment creation to avoid touching RandomizedMazeEnv internals.
"""

import csv
import os
import time
from typing import Dict, List, Tuple

from minigrid.core.world_object import Ball, Wall

from custom_env import RandomizedMazeEnv
from llm_reasoner import LLMReasoner
from simulation_engine import FastDownwardRunner, StateTranslator, detect_new_entities  # Reuse policy compliance
from state_manager import StateManager
from pddl_patcher import PDDLPatcher
from utils.logger import setup_logger


# ---------------------------------------------------------------------------
# Scenario Definitions (hardcoded for isolation)
# ---------------------------------------------------------------------------
SCENARIOS: Dict[str, Dict] = {
    "SCENARIO_1": {
        "name": "Golden Opportunity",
        "description": "Close & Cheap store; expect A to miss, others to succeed.",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "objects": [
            {"name": "rami_levy_express", "position": (5, 5), "type": "store", "price": 2.0},
        ],
    },
    "SCENARIO_2": {
        "name": "Honey Pot",
        "description": "Close & Expensive; expect B to wastefully replan, C/D ignore.",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "objects": [
            {"name": "am_pm_tlv", "position": (3, 3), "type": "store", "price": 8.0},
        ],
    },
    "SCENARIO_3": {
        "name": "Strategic Dilemma",
        "description": "Far & Very Cheap; expect D to be rigid, C to be contextual.",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "objects": [
            {"name": "osher_ad_outlet", "position": (1, 14), "type": "store", "price": 1.0},
        ],
    },
    "SCENARIO_4": {
        "name": "Noise Storm",
        "description": "Irrelevant objects along diagonal; expect B to slow/fail, D/D ignore.",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "objects": [
            {"name": "old_oak_tree", "position": (4, 4), "type": "irrelevant", "price": None},
            {"name": "bronze_statue", "position": (6, 6), "type": "irrelevant", "price": None},
            {"name": "stray_signpost", "position": (8, 8), "type": "irrelevant", "price": None},
        ],
    },
}

ALGORITHMS = ["A", "B", "C", "D"]
VICTORY_PRICE = 4.0

# Initialize central logger to ensure trace.log is created
logger = setup_logger("trace.log")


# ---------------------------------------------------------------------------
# Environment & Scenario Setup
# ---------------------------------------------------------------------------
def setup_scenario_env(scenario_id: str):
    """Instantiate environment and manually inject scenario objects."""
    scenario = SCENARIOS[scenario_id]

    # Instantiate normally (no scenario arg) to honor non-destructive constraint
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.0, sensor_radius=5, render_mode="rgb_array")

    # Clear any non-wall artifacts the base generator might place
    for x in range(env.width):
        for y in range(env.height):
            cell = env.grid.get(x, y)
            if cell and not isinstance(cell, Wall):
                env.grid.set(x, y, None)

    # Force agent start
    env.agent_pos = scenario["start_pos"]
    env.agent_dir = 0

    # Place victory store
    victory = Ball("blue")
    victory.name = "victory"
    victory.price = VICTORY_PRICE
    env.grid.set(*scenario["victory_pos"], victory)

    # Inject scenario-specific objects
    for obj in scenario["objects"]:
        color = "red" if obj["type"] == "store" else "grey"
        ball = Ball(color)
        ball.name = obj["name"]
        if obj.get("price") is not None:
            ball.price = obj["price"]
        env.grid.set(*obj["position"], ball)

    return env, scenario


def animate_agent_walk(env, target_pos: Tuple[int, int], delay: float = 0.1):
    """Simple Manhattan walk visualization to target (ignores walls since wall_density=0)."""
    env.render()
    cx, cy = env.agent_pos
    tx, ty = target_pos

    # Move in X then Y
    while (cx, cy) != (tx, ty):
        if cx < tx:
            cx += 1
        elif cx > tx:
            cx -= 1
        elif cy < ty:
            cy += 1
        elif cy > ty:
            cy -= 1

        env.agent_pos = (cx, cy)
        env.render()
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Algorithm Decision Logic (lightweight, reusing LLMReasoner semantics)
# ---------------------------------------------------------------------------
def decide_target_for_algorithm(
    env: RandomizedMazeEnv,
    scenario: Dict,
    algorithm: str,
    reasoner: LLMReasoner,
) -> Tuple[str, Tuple[int, int], float, int, int]:
    """
    Return chosen target name, position, price, replan_count, llm_calls.
    """
    start_pos = tuple(scenario["start_pos"])
    base_distance = env.calculate_walking_distance(start_pos, tuple(scenario["victory_pos"]))

    chosen = {
        "name": "victory",
        "position": tuple(scenario["victory_pos"]),
        "price": VICTORY_PRICE,
        "replans": 0,
    }

    if algorithm == "A":
        return chosen["name"], chosen["position"], chosen["price"], chosen["replans"], reasoner.get_llm_call_count()

    for obj in scenario["objects"]:
        pos = tuple(obj["position"])
        distance = env.calculate_walking_distance(start_pos, pos)
        if distance >= 9999:
            continue  # unreachable, skip

        analysis = reasoner.analyze_observation(obj["name"])
        est_price = obj.get("price", analysis.get("estimated_price", VICTORY_PRICE))
        sells_milk = analysis.get("sells_milk", False) and (est_price is not None and est_price > 0)

        if algorithm == "B":
            if sells_milk:
                chosen = {"name": obj["name"], "position": pos, "price": est_price, "replans": 1}
                break

        elif algorithm == "C":
            if sells_milk:
                context = {
                    "agent_location": start_pos,
                    "current_plan_length": base_distance,
                    "walking_distance_to_new_store": distance,
                    "price_at_victory": VICTORY_PRICE,
                }
                decision = reasoner.decide_replan(context, {"type": analysis.get("type", ""), "sells_milk": True, "estimated_price": est_price})
                if decision.get("replan_needed", False):
                    chosen = {"name": obj["name"], "position": pos, "price": est_price, "replans": 1}
                    break

        elif algorithm == "D":
            if sells_milk:
                savings = VICTORY_PRICE - est_price
                should_replan = (savings > 1.0) and (distance < 10)
                if should_replan:
                    chosen = {"name": obj["name"], "position": pos, "price": est_price, "replans": 1}
                    break

    return chosen["name"], chosen["position"], chosen["price"], chosen["replans"], reasoner.get_llm_call_count()


# ---------------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------------
def run_experiment(scenario_id: str, algorithm: str) -> Dict:
    env, scenario = setup_scenario_env(scenario_id)
    # Don't call reset() - setup_scenario_env already places agent at start_pos

    # Core components
    runner = FastDownwardRunner(env=env)
    translator = StateTranslator(env)
    patcher = PDDLPatcher("problem_initial.pddl")
    state_manager = StateManager()
    reasoner = LLMReasoner(price_weight=0.6, dist_weight=0.4)

    logger.info("EXPERIMENT", f"Starting Run: scenario={scenario_id}, algorithm={algorithm}")

    # Create basic problem file with connectivity (like run_live_dashboard.py)
    start_pos = scenario.get("start_pos", (1, 1))
    victory_pos = scenario.get("victory_pos", (18, 18))
    start_loc = f"loc_{start_pos[0]}_{start_pos[1]}"
    victory_loc = f"loc_{victory_pos[0]}_{victory_pos[1]}"
    
    # Generate all grid locations
    all_locations = []
    for x in range(env.width):
        for y in range(env.height):
            all_locations.append(f"loc_{x}_{y}")
    locations_str = " ".join(all_locations)
    
    # Create fresh problem_initial.pddl
    with open("problem_initial.pddl", "w") as f:
        f.write(f"""(define (problem supermarket-navigation-problem)
    (:domain supermarket-navigation)
    (:objects
      agent - agent
      {locations_str} - location
      victory - store
      milk - item
    )
    (:init
      (at_agent agent {start_loc})
      (at_store victory {victory_loc})
      (selling victory milk)
      (clear {victory_loc})
    )
    (:goal (and (have agent milk)))
    )""")
    
    # CRITICAL: Add (clear ...) predicates for ALL locations (required for drive action)
    # The drive action requires (clear ?to), so all walkable locations must have (clear ...)
    with open("problem_initial.pddl", "r") as f:
        content = f.read()
    
    # Find :init section and add (clear loc_X_Y) for all locations
    init_pos = content.find("(:init")
    if init_pos != -1:
        # Find closing of :init
        depth = 0
        init_end = None
        for i in range(init_pos, len(content)):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    init_end = i
                    break
        
        if init_end:
            # Add (clear ...) for all locations before closing :init
            clear_predicates = []
            for x in range(env.width):
                for y in range(env.height):
                    clear_predicates.append(f"      (clear loc_{x}_{y})")
            
            clear_block = "\n" + "\n".join(clear_predicates) + "\n"
            content = content[:init_end] + clear_block + content[init_end:]
            
            with open("problem_initial.pddl", "w") as f:
                f.write(content)
    
    # Initialize grid connectivity (CRITICAL - without this, Fast Downward can't find a path!)
    patcher.init_grid_connectivity(env.width, env.height)
    
    # Seed knowledge with victory store
    state_manager.update_agent_pos(env.agent_pos)
    state_manager.add_discovery("victory", victory_pos, obj_type="store", price=VICTORY_PRICE, sells_milk=True)
    patcher.update_problem_file(env.agent_pos, state_manager.discovered_objects)

    # Initial plan
    try:
        current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
        logger.info("PLAN", f"Initial plan length={len(current_plan)}")
    except Exception as e:
        logger.error("PLAN", f"Initial planning failed: {e}")
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "algorithm": algorithm,
            "target": "none",
            "target_pos": None,
            "total_steps": 0,
            "total_cost": 0.0,
            "replan_count": 0,
            "llm_calls": 0,
            "victory_reached": False,
            "compute_time_sec": 0.0,
        }

    start_time = time.time()
    visual_memory = set()
    step = 0
    max_steps = 200
    current_step_index = 0
    replans = 0
    victory = False

    while step < max_steps and not victory and current_step_index < len(current_plan):
        pddl_action = current_plan[current_step_index]

        # Populate translator buffer if empty
        if not translator.has_actions():
            mock_agent = type("MockAgent", (), {"pos": tuple(env.agent_pos), "dir": env.agent_dir})()
            translator.get_micro_action(pddl_action, mock_agent)

        # Execute one motor action or handle buy
        if translator.has_actions():
            motor_action = translator.action_buffer.pop(0)
            result = env.step(motor_action)
            if len(result) == 5:
                obs, reward, terminated, truncated, info = result
                done = terminated or truncated
            else:
                obs, reward, done, info = result
            # env.render()  # Disabled for faster execution
            # time.sleep(0.1)  # Disabled for faster execution
            step += 1
            # If buffer empty, advance PDDL step
            if not translator.has_actions():
                current_step_index += 1
        else:
            # No motor actions: likely a buy action
            if "buy" in pddl_action:
                env.step(5)  # toggle
                victory = True
                step += 1
                current_step_index += 1
                break
            current_step_index += 1
            step += 1

        # Detection of new entities
        new_entity = detect_new_entities(None, ["victory"], env, visual_memory=visual_memory)
        if new_entity:
            visual_memory.add((new_entity["position"][0], new_entity["position"][1], new_entity["name"]))
            logger.info("DISCOVERY", f"Found {new_entity['name']} at {new_entity['position']}")

            # Algorithm-specific decision
            analysis = reasoner.analyze_observation(new_entity["name"])
            llm_calls = reasoner.get_llm_call_count()
            sells_milk = analysis.get("sells_milk", False)
            est_price = analysis.get("estimated_price", VICTORY_PRICE)
            walking_distance = env.calculate_walking_distance(tuple(env.agent_pos), new_entity["position"])

            should_replan = False
            if algorithm == "B":
                should_replan = sells_milk or walking_distance < 9999
            elif algorithm == "C":
                decision = reasoner.decide_replan(
                    {
                        "agent_location": tuple(env.agent_pos),
                        "current_plan_length": len(current_plan),
                        "walking_distance_to_new_store": walking_distance,
                        "price_at_victory": VICTORY_PRICE,
                    },
                    {"type": analysis.get("type", ""), "sells_milk": sells_milk, "estimated_price": est_price},
                )
                should_replan = decision.get("replan_needed", False)
            elif algorithm == "D":
                savings = VICTORY_PRICE - est_price
                should_replan = (savings > 1.0) and (walking_distance < 10) and sells_milk
            elif algorithm == "A":
                should_replan = False

            if should_replan:
                replans += 1
                obj_type = "store" if sells_milk else "obstacle"
                state_manager.add_discovery(new_entity["name"], new_entity["position"], obj_type=obj_type, price=est_price, sells_milk=sells_milk)
                state_manager.update_agent_pos(env.agent_pos)
                patcher.update_problem_file(env.agent_pos, state_manager.discovered_objects)
                try:
                    current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
                    logger.info("PLAN", f"Replan successful length={len(current_plan)}")
                    translator.clear_buffer()
                    current_step_index = 0
                except Exception as e:
                    logger.error("PLAN", f"Replan failed: {e}")
                    break

    total_cost = VICTORY_PRICE  # price paid at victory; discovered store prices not modeled in planner
    compute_time = time.time() - start_time

    logger.info("RESULT", f"Steps={step} Cost={total_cost} Replans={replans} LLM_calls={reasoner.get_llm_call_count()} Victory={victory}")

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "algorithm": algorithm,
        "target": "victory" if victory else "unknown",
        "target_pos": tuple(env.agent_pos),
        "total_steps": step,
        "total_cost": total_cost,
        "replan_count": replans,
        "llm_calls": reasoner.get_llm_call_count(),
        "victory_reached": victory,
        "compute_time_sec": round(compute_time, 3),
    }


def run_all():
    results: List[Dict] = []

    print("\n================= SCIENTIFIC EXPERIMENTS =================")
    for scenario_idx in range(1, 4 + 1):
        scenario_id = f"SCENARIO_{scenario_idx}"
        print(f"\nScenario: {scenario_id} - {SCENARIOS[scenario_id]['name']}")
        for algo in ALGORITHMS:
            for run_i in range(1, 4):
                print(f"--- Running Scenario {scenario_idx} | Algo {algo} | Run {run_i}/3 ---")
                res = run_experiment(scenario_id, algo)
                res["scenario"] = scenario_idx
                res["algorithm"] = algo
                res["run_id"] = run_i
                results.append(res)
                print(f"  Algo {algo} Run {run_i}: target={res['target']}, steps={res['total_steps']}, cost={res['total_cost']}, replans={res['replan_count']}")

    # Write CSV
    csv_path = "experiment_results_raw.csv"
    fieldnames = [
        "scenario_id",
        "scenario_name",
        "scenario",
        "algorithm",
        "run_id",
        "target",
        "target_pos",
        "total_steps",
        "total_cost",
        "replan_count",
        "llm_calls",
        "victory_reached",
        "compute_time_sec",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {csv_path}\n")

    # Print summary table
    header = f"{'Scenario':<12} {'Run':<4} {'Algo':<5} {'Target':<18} {'Steps':<7} {'Cost':<6} {'Replans':<8} {'LLM':<4}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['scenario_id']:<12} {r['run_id']:<4} {r['algorithm']:<5} {r['target']:<18} "
            f"{r['total_steps']:<7} {r['total_cost']:<6.2f} {r['replan_count']:<8} {r['llm_calls']:<4}"
        )


# ---------------------------------------------------------------------------
# Debug helper: Dry-run setup to list injected objects (no simulation)
# ---------------------------------------------------------------------------
def debug_print_scenario_objects():
    for scenario_id in SCENARIOS:
        env, scenario = setup_scenario_env(scenario_id)
        found_objects = []
        for obj in scenario["objects"]:
            cell = env.grid.get(*obj["position"])
            if cell:
                price = getattr(cell, "price", None)
                found_objects.append((obj["name"], obj["position"], price))
        if scenario_id == "SCENARIO_4":
            print(f"[CHECK] Scenario 4 Setup: Found {len(found_objects)} distraction objects.")
        else:
            name, pos, price = found_objects[0] if found_objects else ("", (), None)
            print(f"[CHECK] Scenario {scenario_id[-1]} Setup: Found '{name}' at {pos} | Price: {price}")


if __name__ == "__main__":
    run_all()

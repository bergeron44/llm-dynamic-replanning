"""
Live Dashboard for LLM-Driven Dynamic Replanning Research
50x50 Maze Configuration with Full Logging and Walking Distance Analysis
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file immediately
load_dotenv()

import matplotlib.pyplot as plt
import time
from custom_env import RandomizedMazeEnv
from simulation_engine import FastDownwardRunner, StateTranslator, detect_new_entities
from llm_reasoner import LLMReasoner
from pddl_patcher import PDDLPatcher
from state_manager import StateManager
from utils.logger import setup_logger
from scenarios import SCENARIOS, get_scenario
from results_logger import logger as results_logger

logger = setup_logger()

def run_live_dashboard():
    """
    COMPARATIVE EXPERIMENT FRAMEWORK: Testing 4 Cognitive Architectures
    """
    # --- EXPERIMENT CONFIGURATION ---
    ALGORITHM_MODE = os.environ.get('ALGORITHM_MODE', 'C').upper()  # A/B/C/D, default C (Smart Agent)
    SCENARIO_ID = os.environ.get('SCENARIO_ID', 'SCENARIO_4')  # Default to sweet spot scenario

    logger.info("EXPERIMENT", f"=== STARTING COMPARATIVE EXPERIMENT ===")
    logger.info("EXPERIMENT", f"Algorithm: {ALGORITHM_MODE}, Scenario: {SCENARIO_ID}")
    logger.info("EXPERIMENT", "Initializing comparative experiment framework...")

    # Load scenario configuration
    scenario = get_scenario(SCENARIO_ID)
    if not scenario:
        logger.error("EXPERIMENT", f"Invalid scenario: {SCENARIO_ID}")
        return

    logger.info("SCENARIO", f"Loaded: {scenario['name']}")
    logger.info("SCENARIO", f"Description: {scenario['description']}")

    # Start experiment timer for results logging
    experiment_start_time = results_logger.start_experiment_timer()

    # 1. INIT EXPERIMENT ENVIRONMENT (Scenario-based)
    import numpy as np
    np.random.seed(42)  # For reproducible research results

    # Use scenario-defined dimensions or default to 20x20
    env_width = scenario.get('width', 20)
    env_height = scenario.get('height', 20)

    env = RandomizedMazeEnv(
    width=env_width,
    height=env_height,
    wall_density=0.2,   # 20% walls for balanced difficulty
    sensor_radius=5,    # Appropriate sensor range
    render_mode='rgb_array',
    scenario=scenario    # Pass scenario for deterministic store placement
    )

    obs, info = env.reset()
    logger.info("ENV", f"Environment initialized: {env.width}x{env.height} grid")
    logger.info("ENV", f"Start: {scenario['start_pos']}, Victory: {scenario['victory_pos']}")

    # Place scenario-defined stores
    surprise_obj = scenario['surprise_object']
    logger.info("SCENARIO", f"Surprise Object: {surprise_obj['name']} at {surprise_obj['position']}")
    if surprise_obj['true_price']:
        logger.info("SCENARIO", f"True Price: ${surprise_obj['true_price']}")
    else:
        logger.info("SCENARIO", "True Price: N/A (not a store)")

    # Initialize research components
    runner = FastDownwardRunner(env=env)
    translator = StateTranslator(env)
    # Initialize LLM with "stingy" personality (100% price, 0% distance)
    reasoner = LLMReasoner(price_weight=1.0, dist_weight=0.0)
    patcher = PDDLPatcher("problem_initial.pddl")

    # CRITICAL: Add all walls to PDDL so planner knows about obstacles
    logger.info("SYSTEM", "Adding environment walls to PDDL knowledge...")
    patcher.update_environment_walls(env)

    # Reset PDDL to clean state (copy from backup if exists)
    if os.path.exists("problem_backup.pddl"):
    with open("problem_initial.pddl", "w") as f:
        with open("problem_backup.pddl", "r") as backup:
        f.write(backup.read())
    else:
    # Create basic problem file
    with open("problem_initial.pddl", "w") as f:
        f.write("""(define (problem maze-navigation)
    (:domain maze)
    (:objects
      agent - agent
      home - location
      victory - store
    )
    (:init
      (at agent home)
      (= (total-cost) 0)
    )
    (:goal (and (has agent milk)))
    (:metric minimize (total-cost))
    )""")

    # GUI Setup for Large 50x50 Grid
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 12))  # Large figure for 50x50 visualization

    # Research state tracking
    visual_memory = set()
    current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
    logger.info("PLANNER", f"Initial plan generated: {len(current_plan)} actions")
    if current_plan:
    logger.info("PLANNER", f"First few actions: {current_plan[:5]}")
    logger.info("PLANNER", f"Last few actions: {current_plan[-5:]}")

    # Research metrics
    step = 0
    total_cost = 0
    discoveries = []
    replan_events = []
    victory_achieved = False  # Track if victory was achieved

    # --- STUCK WATCHDOG VARIABLES ---
    last_pos = None
    stuck_counter = 0
    just_skipped = False  # Flag to prevent sync after watchdog skip

    # --- INFINITE LOOP PROTECTION ---
    last_error_msg = None
    error_repeat_count = 0
    max_error_repeats = 5  # Exit after 5 consecutive identical errors

    def check_infinite_loop(error_msg):
    """Check for infinite loops and exit if too many repeated errors"""
    nonlocal last_error_msg, error_repeat_count

    if error_msg == last_error_msg:
        error_repeat_count += 1
        if error_repeat_count >= max_error_repeats:
        logger.critical("INFINITE LOOP", f"Same error repeated {error_repeat_count} times: {error_msg}")
        logger.critical("INFINITE LOOP", "EXITING TO PREVENT INFINITE LOOP")
        sys.exit(1)
    else:
        error_repeat_count = 1
        last_error_msg = error_msg

    def is_blocking_path(obj_pos, current_plan):
    """
    Check if discovered object blocks the agent's planned path.
    Returns True if the object position is in the future path coordinates.
    """
    if not current_plan:
        return False

    # Extract all future position coordinates from the plan
    # Plan actions are like: "drive loc_1_1 loc_1_2", "buy milk victory loc_18_18"
    future_positions = set()

    for action in current_plan:
        # Parse coordinates from PDDL actions
        # drive loc_X_Y loc_A_B -> positions (X,Y) and (A,B)
        if action.startswith("drive"):
        parts = action.split()
        if len(parts) >= 3:
            # Extract loc_X_Y format
            for part in parts[1:3]:  # Skip "drive", take loc_X_Y arguments
            if part.startswith("loc_"):
                try:
                coords = part.replace("loc_", "").split("_")
                if len(coords) == 2:
                    x, y = int(coords[0]), int(coords[1])
                    future_positions.add((x, y))
                except (ValueError, IndexError):
                continue
        # buy milk STORE loc_X_Y -> position (X,Y)
        elif action.startswith("buy milk"):
        parts = action.split()
        if len(parts) >= 4 and parts[2].startswith("loc_"):
            try:
            coords = parts[2].replace("loc_", "").split("_")
            if len(coords) == 2:
                x, y = int(coords[0]), int(coords[1])
                future_positions.add((x, y))
            except (ValueError, IndexError):
            continue

    # Check if object position is in future path
    result = obj_pos in future_positions
    logger.debug("PATH_CHECK", f"Object at {obj_pos} in plan positions {list(future_positions)[:5]}...: {result}")
    return result

    # --- STATE MANAGER ---
    state_manager = StateManager()  # Manages robot's belief state in memory

    done = False

    while not done and step < 200:  # Appropriate limit for 20x20 maze
    step_start_time = time.time()

    # --- STUCK WATCHDOG LOGIC ---
    current_pos = env.agent_pos
    if current_pos == last_pos:
        stuck_counter += 1
    else:
        stuck_counter = 0
        last_pos = current_pos

    # Recovery: If stuck for 6 frames, force full replan instead of just skipping
    if stuck_counter > 6:
        error_msg = f"Agent STUCK at {current_pos} for {stuck_counter} steps"
        logger.warning("WATCHDOG", f"{error_msg}. Forcing full replan due to persistent blocking.")
        check_infinite_loop(error_msg)

        # Force immediate replan instead of just skipping one action
        replan_triggered = True
        stuck_counter = 0
        logger.info("WATCHDOG", "Full replan triggered due to stuck condition")
        # The replan will be handled in the main loop
    logger.debug("LOOP", f"=== STEP {step} START ===")
    logger.debug("LOOP", f"Agent position: {env.agent_pos}, Direction: {env.agent_dir}")
    logger.debug("LOOP", f"Plan remaining: {len(current_plan)} actions")

    # --- STATE MANAGEMENT: Update Agent Position ---
    state_manager.update_agent_pos(env.agent_pos)

    # 1. VISUAL RENDERING (Research Observation)
    img = env.render()
    ax.clear()
    ax.imshow(img)
    ax.axis('off')
    status = f"Step: {step} | Plan: {len(current_plan)} | Cost: ${total_cost:.1f}"
    if stuck_counter > 2: status += " | ⚠️ STUCK DETECTED"
    ax.set_title(status)
    plt.pause(0.02)  # Fast updates for research monitoring

    # 2. PERCEPTION (Algorithm-aware Discovery)
    logger.debug("PERCEPTION", f"Scanning for new entities within sensor range...")
    new_discovery = detect_new_entities(None, ['victory'], env, visual_memory=visual_memory)
    logger.debug("PERCEPTION", f"Scan complete. Discovery: {new_discovery is not None}")

    if new_discovery:
        discovery_time = time.time()
        logger.info("DISCOVERY", f"NEW OBJECT DETECTED: {new_discovery['name']}")
        logger.info("DISCOVERY", f"Position: {new_discovery['position']}")

        # Calculate true walking distance
        agent_pos = env.agent_pos
        store_pos = new_discovery['position']
        true_walking_distance = env.calculate_walking_distance(agent_pos, store_pos)
        new_discovery['walking_distance'] = true_walking_distance
        discoveries.append(new_discovery)

        # Visual feedback
        ax.set_title(f"🔍 DISCOVERED: {new_discovery['name']} (Walk: {true_walking_distance})")
        plt.pause(0.5)

        # 3. ALGORITHM-SPECIFIC DECISION MAKING
        logger.info("ALGORITHM", f"Processing discovery with Algorithm {ALGORITHM_MODE}")

        # Initialize timing for compute time tracking
        compute_start = time.time()
        replan_triggered = False

        # --- ALGORITHM DISPATCH ---
        if ALGORITHM_MODE == 'A':
        # ALGO_A (Baseline / "Blind"): Ignore discovery completely
        logger.info("ALGORITHM_A", "Ignoring discovery - continuing current plan")
        # Note: Collision avoidance is handled universally above for ALL algorithms

        elif ALGORITHM_MODE == 'B':
        # ALGO_B (Naive / "Obsessive"): Update map with everything, always replan
        logger.info("ALGORITHM_B", "Obsessive mode: Adding to map and forcing replan")

        # Only update type if not already set by universal collision avoidance
        if new_discovery.get('type') != 'obstacle':  # Don't override wall designation
            analysis = reasoner.analyze_observation(new_discovery['name'])
            obj_type = 'store' if analysis.get('sells_milk', False) else 'obstacle'
            new_discovery['type'] = obj_type

            # Update state with discovery (even if irrelevant)
            state_manager.add_discovery(
            new_discovery['name'],
            store_pos,
            obj_type=obj_type
            )

        # Force replan regardless of relevance (unless already triggered by collision)
        if not replan_triggered:
            replan_triggered = True
        logger.info("ALGORITHM_B", f"Forced replan triggered (final type: {new_discovery.get('type', 'unknown')})")

        elif ALGORITHM_MODE == 'C':
        # ALGO_C (Rational / "The Smart Agent"): Filter noise, strategic replanning
        logger.info("ALGORITHM_C", "Smart Agent: Analyzing relevance and making strategic decision")

        # Phase 1: Perception - Analyze what the object is
        analysis = reasoner.analyze_observation(new_discovery['name'])
        logger.info("ANALYSIS", f"Type: {analysis.get('type', 'unknown')}")
        logger.info("ANALYSIS", f"Sells Milk: {analysis.get('sells_milk', False)}")
        if analysis.get('sells_milk'):
            logger.info("ANALYSIS", f"Estimated Price: ${analysis.get('estimated_price', 0):.2f}")

        # Phase 2: Decision - Only proceed if relevant
        if analysis.get('sells_milk', False):
            decision_context = {
            "agent_location": agent_pos,
            "current_plan_length": len(current_plan),
            "estimated_current_cost": total_cost,
            "walking_distance_to_new_store": true_walking_distance,
            "price_at_victory": 4.0
            }

            decision = reasoner.decide_replan(decision_context, analysis)
            replan_triggered = decision.get('replan_needed', False)

            logger.info("DECISION", f"Strategic Decision: {'REPLAN' if replan_triggered else 'CONTINUE'}")
            logger.info("DECISION", f"Reasoning: {decision.get('reasoning', 'N/A')}")

            # Update state with price if replanning (collision avoidance handled universally above)
            if replan_triggered:
            new_discovery['price'] = analysis.get('estimated_price', 4.0)
            # Don't override obstacle type set by universal collision avoidance
            obj_type = new_discovery.get('type', 'store')
            state_manager.add_discovery(
                new_discovery['name'],
                store_pos,
                obj_type=obj_type,
                price=new_discovery['price'] if obj_type == 'store' else None
            )
        else:
            logger.info("ALGORITHM_C", "Irrelevant object - filtering out noise")
            replan_triggered = False

        elif ALGORITHM_MODE == 'D':
        # ALGO_D (Heuristic / "Math Only"): Simple formula without LLM
        logger.info("ALGORITHM_D", "Math-only heuristic: Analyzing with simple formula")

        # Get price estimate (still need basic analysis for this)
        analysis = reasoner.analyze_observation(new_discovery['name'])

        if analysis.get('sells_milk', False):
            estimated_price = analysis.get('estimated_price', 4.0)
            price_savings = 4.0 - estimated_price

            # Simple heuristic: replan if savings > $1.00 AND detour < 10 steps
            replan_triggered = (price_savings > 1.0) and (true_walking_distance < 10)

            logger.info("HEURISTIC", f"Price Savings: ${price_savings:.1f}, Distance: {true_walking_distance}")
            logger.info("HEURISTIC", f"Formula Result: {'REPLAN' if replan_triggered else 'CONTINUE'}")

            if replan_triggered:
            new_discovery['price'] = estimated_price
            # Don't override obstacle type set by universal collision avoidance
            obj_type = new_discovery.get('type', 'store')
            state_manager.add_discovery(
                new_discovery['name'],
                store_pos,
                obj_type=obj_type,
                price=new_discovery['price'] if obj_type == 'store' else None
            )
        else:
            logger.info("HEURISTIC", "Does not sell milk - no replan")
            replan_triggered = False

        else:
        logger.error("ALGORITHM", f"Unknown algorithm mode: {ALGORITHM_MODE}")
        replan_triggered = False

        # Track compute time
        compute_time = time.time() - compute_start

        # Add to visual memory (prevents rediscovery)
        visual_memory.add((store_pos[0], store_pos[1], new_discovery['name']))

        # 🚨 FINAL UNIVERSAL COLLISION CHECK: If no algorithm triggered replan but object blocks path
        if not replan_triggered and is_blocking_path(new_discovery['position'], current_plan):
        logger.warning("COLLISION", f"🚨 FINAL CHECK: Object {new_discovery['name']} blocks path but no algorithm triggered replan - forcing obstacle replan!")
        replan_triggered = True
        new_discovery['type'] = 'obstacle'  # Mark as wall for navigation

        # Add as obstacle to PDDL
        state_manager.add_discovery(
            new_discovery['name'],
            store_pos,
            obj_type='obstacle'
        )
        logger.info("COLLISION", f"Added {new_discovery['name']} as final obstacle")

        # 4. REPLANNING EXECUTION (if triggered)
        if replan_triggered:
        logger.info("REPLAN", "EXECUTING REPLAN SEQUENCE")

        replan_events.append({
            'step': step,
            'store': new_discovery['name'],
            'walking_distance': true_walking_distance,
            'price_savings': 4.0 - new_discovery.get('price', 4.0),
            'algorithm': ALGORITHM_MODE
        })

        # Sync belief state to PDDL
        current_predicates = state_manager.get_current_state_predicates()
        logger.info("REPLAN", f"Injecting {len(current_predicates)} state predicates to PDDL")
        logger.info("REPLAN", f"Predicates: {current_predicates}")

        success = patcher.inject_dynamic_state(current_predicates)

        if success:
            logger.info("REPLAN", "PDDL state successfully updated")
            current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
            logger.info("REPLAN", f"New plan generated: {len(current_plan)} actions")

            # Flush translator buffer
            if hasattr(translator, 'action_buffer'):
            translator.action_buffer = []
            logger.info("REPLAN", "Flushed stale micro-actions from translator buffer")
        else:
            logger.error("REPLAN", "Failed to update PDDL state - continuing with current plan")
        else:
        logger.info("CONTINUE", f"Continuing with current plan (Algorithm {ALGORITHM_MODE})")

    # 4. MOTOR EXECUTION (Micro-step Navigation)
    if current_plan:
        pddl_action = current_plan[0]  # Peek (don't pop yet)
        logger.debug("EXECUTION", f"Processing PDDL action: {pddl_action}")

        # --- STRICT PLAN SYNCHRONIZATION CHECK ---
        # Parse expected starting location from PDDL action
        parts = pddl_action.split()
        if len(parts) >= 3 and parts[0] == "drive":
        expected_from = parts[1]  # e.g., "loc_1_17"
        current_agent_loc = f"loc_{env.agent_pos[0]}_{env.agent_pos[1]}"

        # ONLY sync if we didn't just force a skip (prevent infinite loop)
        if expected_from != current_agent_loc and not just_skipped:
            error_msg = f"Plan Desynchronized! Action expects {expected_from}, Agent at {current_agent_loc}"
            logger.warning("SYNC", error_msg)
            logger.info("SYNC", "Forcing immediate replan from current position...")
            check_infinite_loop(error_msg)

            # Update PDDL with correct agent position
            success = patcher.update_agent_position(env.agent_pos)
            if success:
            logger.info("SYNC", "Agent position updated in PDDL")

            # Generate new valid plan
            current_plan = runner.run_planner("domain.pddl", "problem_initial.pddl")
            logger.info("SYNC", f"New synchronized plan: {len(current_plan)} actions")

            # Skip this iteration to process new plan
            continue
            else:
            logger.error("SYNC", "Failed to update agent position - continuing with current plan")

        logger.debug("EXECUTION", f"Target parsing: {pddl_action.split()}")

        # Get micro-action for this step
        mock_agent = type('MockAgent', (), {
        'pos': env.agent_pos,
        'dir': env.agent_dir
        })()

        micro_action, is_action_complete = translator.get_micro_action(pddl_action, mock_agent)
        logger.info("EXECUTION", f"Micro-action result: {micro_action} (complete: {is_action_complete})")
        logger.info("EXECUTION", f"Agent pos: {env.agent_pos}, dir: {env.agent_dir}, front_pos: {getattr(env, 'front_pos', 'N/A')}")

        if is_action_complete:
        # Action finished - remove from plan
        completed_action = current_plan.pop(0)
        logger.info("EXECUTION", f"COMPLETED ACTION: {completed_action}")

        # Special check for buy milk action - verify we're at the store
        if "buy milk" in completed_action:
            # Parse the store name from the action
            parts = completed_action.split()
            if len(parts) >= 4:
            store_name = parts[2]  # "buy milk STORE_NAME position"
            # Check if agent is at the store position
            store_pos = None
            for pos, name in env.store_positions.items():
                if name == store_name:
                store_pos = pos
                break

            if store_pos and env.agent_pos == store_pos:
                logger.info("EXECUTION", f"SUCCESSFULLY BOUGHT MILK AT {store_name}")
                if store_name == "victory":
                victory_achieved = True
            else:
                logger.warning("EXECUTION", f"BUY MILK FAILED - Agent at {env.agent_pos}, {store_name} expected at {store_pos}")

        # Check if plan is finished
        if not current_plan:
            logger.info("EXECUTION", "PLAN COMPLETED - MISSION ACCOMPLISHED")
            print(f"DEBUG MISSION: Final position: {env.agent_pos}, Victory expected: {scenario.get('victory_pos', 'unknown')}")
            break
        else:
        # Execute micro-step
        env.step(micro_action)

        # --- DEBUG BLOCK: WHY AM I STUCK? ---
        if env.agent_pos == last_pos and micro_action == 1:  # Tried forward but didn't move
            front_cell = env.grid.get(*env.front_pos) if hasattr(env, 'front_pos') else None
            front_name = getattr(front_cell, 'type', 'empty') if front_cell else 'empty'
            error_msg = f"Failed to move! Pos: {env.agent_pos}, Dir: {env.agent_dir}, Blocked by: {front_name} at {env.front_pos}"
            logger.error("PHYSICS DEBUG", error_msg)
            check_infinite_loop(error_msg)

            # Check for Coordinate Mismatch
            parts = pddl_action.split()
            if len(parts) >= 3 and parts[0] == "drive":
            pddl_target = translator.pddl_to_coord(parts[2])  # target of 'drive a b'
            error_msg = f"PDDL wants to go to: {pddl_target}"
            logger.error("LOGIC DEBUG", error_msg)
            check_infinite_loop(error_msg)

        total_cost += 1  # Each step costs 1 unit
        step += 1

        # Log micro-action for research analysis
        action_name = translator.minigrid_action_to_name(micro_action)
        logger.debug("EXECUTION", f"Micro-step: {action_name} at {env.agent_pos}")

        # Reset skip flag after successful step
        just_skipped = False
    else:
        logger.warning("EXECUTION", "No plan available - terminating")
        break

    # Reset skip flag at end of loop iteration
    just_skipped = False

    # Step summary
    logger.debug("LOOP", f"=== STEP {step-1} END ===")

    step_end_time = time.time()
    step_duration = step_end_time - step_start_time
    logger.debug("PERFORMANCE", f"Step {step} duration: {step_duration:.3f}s")

    # EXPERIMENT RESULTS & LOGGING
    logger.info("EXPERIMENT", "=== EXPERIMENT COMPLETED ===")
    logger.info("RESULTS", f"Algorithm: {ALGORITHM_MODE}, Scenario: {SCENARIO_ID}")
    logger.info("RESULTS", f"Total Steps: {step}")
    logger.info("RESULTS", f"Total Cost: ${total_cost:.1f}")
    logger.info("RESULTS", f"Replanning Events: {len(replan_events)}")

    # Determine if victory was reached and final price
    victory_reached = victory_achieved  # Use our tracked variable
    true_final_price = 4.0 if victory_reached else None

    # Debug: check victory condition
    print(f"DEBUG VICTORY: victory_achieved={victory_achieved}, victory_reached={victory_reached}")

    logger.info("RESULTS", f"Victory Reached: {victory_reached}")
    if true_final_price:
    logger.info("RESULTS", f"True Final Price: ${true_final_price}")

    # Calculate total compute time
    total_compute_time = results_logger.end_experiment_timer(experiment_start_time)

    # Log results to CSV
    results_logger.log_experiment_result(
    scenario_id=SCENARIO_ID,
    algorithm_mode=ALGORITHM_MODE,
    total_steps=step,
    total_cost=total_cost,
    compute_time=total_compute_time,
    replans_count=len(replan_events),
    true_final_price=true_final_price,
    victory_reached=victory_reached,
    termination_reason="completed"
    )

    logger.info("LOGGING", "Results saved to experiment_results.csv")

    # Detailed discovery summary
    for i, discovery in enumerate(discoveries):
    logger.info("DISCOVERY_SUMMARY", f"Discovery {i+1}: {discovery['name']} at {discovery['position']} (Walk: {discovery.get('walking_distance', 'N/A')})")

    # Detailed replan summary
    for i, replan in enumerate(replan_events):
    logger.info("REPLAN_SUMMARY", f"Replan {i+1}: {replan['store']} - Distance: {replan['walking_distance']}, Savings: ${replan['price_savings']:.1f} (Algo: {replan.get('algorithm', ALGORITHM_MODE)})")

    print(f"Comparative Experiment Completed: Algorithm {ALGORITHM_MODE} on {SCENARIO_ID}")
    print(f"Results logged to experiment_results.csv")

    if __name__ == "__main__":
    run_live_dashboard()

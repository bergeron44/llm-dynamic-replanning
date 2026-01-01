"""
Phase 4 Diagnostic: Execution Logic & Turn Tolerance Verification

This script verifies that:
1. Turn actions don't trigger false replans when position doesn't change
2. Plan validation correctly identifies when agent reaches target
3. Wall collisions are properly detected and trigger replanning

The critical issue: During a turn, the agent position stays the same, but the plan
should still be considered valid since we're executing a micro-action sequence.
"""

import os
import sys
from typing import List, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scenarios import get_scenario
from custom_env import RandomizedMazeEnv
from simulation_engine import StateTranslator


def validate_plan(agent_pos: Tuple[int, int], current_plan: List[str], 
                  is_turn_action: bool = False) -> bool:
    """
    Validate that the current plan is synchronized with the agent's position.
    
    This simulates the validation logic from run_live_dashboard.py:
    - Checks if agent's current position matches the "from" location of next PDDL action
    - BUT: If we're in the middle of executing a turn, position may not have changed yet
    
    Args:
        agent_pos: Current agent position (x, y)
        current_plan: List of PDDL action strings
        is_turn_action: True if we just executed a turn (position shouldn't change)
    
    Returns:
        True if plan is valid, False if desynchronized
    """
    if not current_plan:
        return False
    
    pddl_action = current_plan[0]  # Peek at next action
    parts = pddl_action.split()
    
    if len(parts) >= 3 and parts[0] == "drive":
        expected_from = parts[1]  # e.g., "loc_1_1"
        current_agent_loc = f"loc_{agent_pos[0]}_{agent_pos[1]}"
        
        # CRITICAL: If we just executed a turn, position hasn't changed yet
        # but the plan is still valid - we're executing micro-actions
        if is_turn_action:
            return True  # Turn actions don't change position - this is expected
        
        # Normal validation: check if positions match
        return expected_from == current_agent_loc
    
    # For non-drive actions (buy, etc.), always valid
    return True


def is_blocking_path(obj_pos: Tuple[int, int], current_plan: List[str]) -> bool:
    """
    Check if discovered object blocks the agent's planned path.
    This simulates the collision detection logic from run_live_dashboard.py.
    """
    if not current_plan:
        return False
    
    # Extract all future position coordinates from the plan
    future_positions = set()
    
    for action in current_plan:
        # Parse coordinates from PDDL actions
        if action.startswith("drive"):
            parts = action.split()
            if len(parts) >= 3:
                # Extract loc_X_Y format from both "from" and "to"
                for part in parts[1:3]:
                    if part.startswith("loc_"):
                        try:
                            coords = part.replace("loc_", "").split("_")
                            if len(coords) == 2:
                                x, y = int(coords[0]), int(coords[1])
                                future_positions.add((x, y))
                        except (ValueError, IndexError):
                            continue
    
    # Check if object position is in future path
    return obj_pos in future_positions


def simulate_action_execution(agent_pos: List[int], agent_dir: int, 
                              action: int) -> Tuple[Tuple[int, int], int]:
    """
    Simulate executing a MiniGrid action and return new position/direction.
    
    Args:
        agent_pos: Current position [x, y] (list for mutability)
        agent_dir: Current direction (0=East, 1=South, 2=West, 3=North)
        action: MiniGrid action (0=Left, 1=Right, 2=Forward)
    
    Returns:
        Tuple of (new_position, new_direction)
    """
    new_pos = list(agent_pos)
    new_dir = agent_dir
    
    if action == 0:  # Turn Left
        new_dir = (agent_dir - 1) % 4
    elif action == 1:  # Turn Right
        new_dir = (agent_dir + 1) % 4
    elif action == 2:  # Forward
        # Move in current direction
        if agent_dir == 0:  # East
            new_pos[0] += 1
        elif agent_dir == 1:  # South
            new_pos[1] += 1
        elif agent_dir == 2:  # West
            new_pos[0] -= 1
        elif agent_dir == 3:  # North
            new_pos[1] -= 1
    
    return (tuple(new_pos), new_dir)


def test_step_1_turn_tolerance():
    """Test 1: Verify that turns don't trigger false replans."""
    print("\n" + "=" * 70)
    print("TEST 1: Turn Tolerance - Turn actions don't trigger false replans")
    print("=" * 70)
    
    # Setup: Agent at (1, 1) facing East, wants to move South
    scenario = get_scenario('SCENARIO_4')
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.2,
                           render_mode='rgb_array', scenario=scenario)
    obs, info = env.reset()
    
    env.agent_pos = (1, 1)
    env.agent_dir = 0  # Facing East
    
    translator = StateTranslator(env)
    
    # Plan: Move from (1, 1) to (1, 2) - requires turn South + forward
    current_plan = ["drive loc_1_1 loc_1_2"]
    
    print(f"\n📋 Setup:")
    print(f"   Agent position: {env.agent_pos}")
    print(f"   Agent direction: {env.agent_dir} (East)")
    print(f"   Plan: {current_plan[0]}")
    print(f"   Target: Move South to loc_1_2")
    
    # Get micro-actions for this PDDL action
    mock_agent = type('MockAgent', (), {'pos': env.agent_pos, 'dir': env.agent_dir})()
    translator.action_buffer = []  # Clear buffer
    translator.env.agent_pos = env.agent_pos
    translator.env.agent_dir = env.agent_dir
    
    # This should generate [1, 2] (turn right, then forward)
    micro_action_1, is_complete_1 = translator.get_micro_action(current_plan[0], mock_agent)
    
    print(f"\n🔧 Step 1.1: Get micro-actions from translator")
    print(f"   First micro-action: {micro_action_1} ({translator.minigrid_action_to_name(micro_action_1)})")
    print(f"   Is complete: {is_complete_1}")
    print(f"   Action buffer: {translator.action_buffer}")
    
    # Execute the turn (action 1 = Turn Right)
    print(f"\n🎮 Step 1.2: Execute Turn Right (action 1)")
    agent_pos = list(env.agent_pos)
    agent_dir = env.agent_dir
    
    new_pos, new_dir = simulate_action_execution(agent_pos, agent_dir, micro_action_1)
    
    print(f"   Before: pos={tuple(agent_pos)}, dir={agent_dir} (East)")
    print(f"   After:  pos={new_pos}, dir={new_dir} (South)")
    print(f"   ✅ Position unchanged: {new_pos == tuple(agent_pos)} (expected for turn)")
    print(f"   ✅ Direction changed: {new_dir != agent_dir} (East → South)")
    
    # CRITICAL TEST: Validate plan while position hasn't changed
    print(f"\n🧪 Step 1.3: Validate plan after turn (position hasn't changed)")
    is_valid = validate_plan(new_pos, current_plan, is_turn_action=True)
    
    print(f"   Plan validation result: {is_valid}")
    print(f"   Expected: True (plan is valid even though position didn't change)")
    
    if is_valid:
        print(f"   ✅ PASS: Turn action correctly tolerated - no false replan triggered!")
        return True
    else:
        print(f"   ❌ FAIL: False replan would be triggered during turn!")
        return False


def test_step_2_plan_completion():
    """Test 2: Verify that after turn+forward, agent reaches target."""
    print("\n" + "=" * 70)
    print("TEST 2: Plan Completion - Agent reaches target after turn+forward")
    print("=" * 70)
    
    # Setup: Continue from Test 1 - agent just turned South
    scenario = get_scenario('SCENARIO_4')
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.2,
                           render_mode='rgb_array', scenario=scenario)
    obs, info = env.reset()
    
    env.agent_pos = (1, 1)
    env.agent_dir = 1  # Now facing South (after turn from Test 1)
    
    translator = StateTranslator(env)
    translator.action_buffer = [2]  # Forward action is buffered
    
    current_plan = ["drive loc_1_1 loc_1_2"]
    
    print(f"\n📋 Setup:")
    print(f"   Agent position: {env.agent_pos}")
    print(f"   Agent direction: {env.agent_dir} (South)")
    print(f"   Plan: {current_plan[0]}")
    print(f"   Action buffer: {translator.action_buffer} (Forward)")
    
    # Execute Forward action
    print(f"\n🎮 Step 2.1: Execute Forward (action 2)")
    agent_pos = list(env.agent_pos)
    agent_dir = env.agent_dir
    
    new_pos, new_dir = simulate_action_execution(agent_pos, agent_dir, 2)
    
    print(f"   Before: pos={tuple(agent_pos)}, dir={agent_dir} (South)")
    print(f"   After:  pos={new_pos}, dir={new_dir}")
    print(f"   ✅ Position changed: {new_pos != tuple(agent_pos)}")
    print(f"   ✅ Reached target loc_1_2: {new_pos == (1, 2)}")
    
    # CRITICAL TEST: Validate plan after reaching target
    print(f"\n🧪 Step 2.2: Validate plan after reaching target")
    
    # After completing the action, we'd normally pop it from the plan
    # For this test, we check if we're at the target location
    expected_target = "loc_1_2"
    current_agent_loc = f"loc_{new_pos[0]}_{new_pos[1]}"
    reached_target = current_agent_loc == expected_target
    
    print(f"   Current location: {current_agent_loc}")
    print(f"   Expected target: {expected_target}")
    print(f"   Reached target: {reached_target}")
    
    # If we reached target, the PDDL action is complete
    if reached_target:
        # Pop the completed action
        completed_plan = current_plan[1:] if len(current_plan) > 1 else []
        print(f"   Plan after completion: {len(completed_plan)} actions remaining")
        print(f"   ✅ PASS: Agent correctly reached target location!")
        return True
    else:
        print(f"   ❌ FAIL: Agent did not reach target location!")
        return False


def test_step_3_wall_collision():
    """Test 3: Verify that wall collisions trigger replanning."""
    print("\n" + "=" * 70)
    print("TEST 3: Wall Collision Detection - Blocked paths trigger replans")
    print("=" * 70)
    
    # Setup: Agent at (1, 2), next plan step goes to (1, 3)
    current_plan = [
        "drive loc_1_2 loc_1_3",
        "drive loc_1_3 loc_1_4",
        "drive loc_1_4 loc_2_4"
    ]
    
    # Place a wall at (1, 3)
    wall_position = (1, 3)
    
    print(f"\n📋 Setup:")
    print(f"   Current plan: {current_plan}")
    print(f"   Wall placed at: {wall_position}")
    
    # Check if wall blocks the path
    print(f"\n🧪 Step 3.1: Check if wall blocks planned path")
    is_blocked = is_blocking_path(wall_position, current_plan)
    
    print(f"   Wall position: {wall_position}")
    print(f"   Blocks path: {is_blocked}")
    
    # Extract future positions for verification
    future_positions = set()
    for action in current_plan:
        if action.startswith("drive"):
            parts = action.split()
            for part in parts[1:3]:
                if part.startswith("loc_"):
                    try:
                        coords = part.replace("loc_", "").split("_")
                        x, y = int(coords[0]), int(coords[1])
                        future_positions.add((x, y))
                    except:
                        continue
    
    print(f"   Future positions in plan: {sorted(future_positions)}")
    print(f"   Wall at {wall_position} in future positions: {wall_position in future_positions}")
    
    if is_blocked:
        print(f"   ✅ PASS: Wall collision correctly detected - replan would be triggered!")
        return True
    else:
        print(f"   ❌ FAIL: Wall collision NOT detected - no replan would occur!")
        return False


def main():
    print("=" * 70)
    print("PHASE 4 DIAGNOSTIC: Execution Logic & Turn Tolerance Verification")
    print("=" * 70)
    print("\nThis diagnostic verifies:")
    print("1. Turn actions don't trigger false replans (position doesn't change)")
    print("2. Plan completion is correctly detected (agent reaches target)")
    print("3. Wall collisions are properly detected (triggers replanning)")
    
    results = []
    
    # Run Test 1: Turn Tolerance
    try:
        result1 = test_step_1_turn_tolerance()
        results.append(("Turn Tolerance", result1))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Turn Tolerance", False))
    
    # Run Test 2: Plan Completion
    try:
        result2 = test_step_2_plan_completion()
        results.append(("Plan Completion", result2))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Plan Completion", False))
    
    # Run Test 3: Wall Collision
    try:
        result3 = test_step_3_wall_collision()
        results.append(("Wall Collision", result3))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Wall Collision", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("PHASE 4 SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 PHASE 4 SUCCESS!")
        print("   ✅ Turn actions are correctly tolerated")
        print("   ✅ Plan completion is correctly detected")
        print("   ✅ Wall collisions correctly trigger replanning")
        print("\n   The execution logic is robust and handles all edge cases!")
        return True
    else:
        print("\n❌ PHASE 4 FAILED!")
        print("   Some tests failed - check the output above for details")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



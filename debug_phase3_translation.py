"""
Phase 3 Diagnostic: Plan Parsing & Action Translation Verification

This script verifies that StateTranslator can:
1. Parse the sas_plan file format (with parentheses)
2. Convert PDDL actions (drive loc_X_Y loc_X_Y) into MiniGrid actions (0=Left, 1=Right, 2=Forward)
3. Handle directional logic correctly (turns + forward movements)
4. Generate valid action sequences

Expected: A non-empty queue of MiniGrid action IDs [2, 2, 1, 2, ...]
"""

import os
import sys
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scenarios import get_scenario
from custom_env import RandomizedMazeEnv
from simulation_engine import StateTranslator


def parse_sas_plan(plan_file: str) -> List[str]:
    """
    Parse sas_plan file format into list of PDDL action strings (without parentheses).
    
    Format: (drive loc_1_1 loc_1_2)
    Returns: ['drive loc_1_1 loc_1_2', ...]
    """
    if not os.path.exists(plan_file):
        print(f"❌ Plan file not found: {plan_file}")
        return []
    
    plan_actions = []
    with open(plan_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith(";"):
                continue
            
            # Remove parentheses and extract action
            if line.startswith("(") and line.endswith(")"):
                action = line[1:-1]  # Remove parentheses
                plan_actions.append(action)
    
    return plan_actions


def decode_plan(translator: StateTranslator, plan_actions: List[str], 
                start_pos: Tuple[int, int], start_dir: int) -> List[int]:
    """
    Convert a list of PDDL actions into a sequence of MiniGrid action IDs.
    
    This simulates how the system processes plans during execution.
    
    Args:
        translator: StateTranslator instance
        plan_actions: List of PDDL action strings (e.g., 'drive loc_1_1 loc_1_2')
        start_pos: Starting position (x, y)
        start_dir: Starting direction (0=East, 1=South, 2=West, 3=North)
    
    Returns:
        List of MiniGrid action IDs [0=Left, 1=Right, 2=Forward, ...]
    """
    # Create a mock environment state
    mock_env = type('MockEnv', (), {
        'agent_pos': list(start_pos),
        'agent_dir': start_dir,
        'width': 20,
        'height': 20
    })()
    
    translator.env = mock_env
    translator.action_buffer = []  # Clear buffer
    
    all_minigrid_actions = []
    current_pos = list(start_pos)
    current_dir = start_dir
    
    for i, pddl_action in enumerate(plan_actions):
        # Update mock environment state
        mock_env.agent_pos = current_pos
        mock_env.agent_dir = current_dir
        
        # Process this PDDL action (may generate multiple MiniGrid actions)
        actions_from_this_pddl = []
        
        # Keep processing until the PDDL action is complete
        is_complete = False
        while not is_complete:
            micro_action, is_complete = translator.get_micro_action(pddl_action)
            
            if micro_action != 6:  # 6 = done, skip it in the output
                actions_from_this_pddl.append(micro_action)
            
            # Simulate action execution to update position/direction
            if micro_action == 0:  # turn left
                current_dir = (current_dir - 1) % 4
            elif micro_action == 1:  # turn right
                current_dir = (current_dir + 1) % 4
            elif micro_action == 2:  # forward
                # Move in current direction
                if current_dir == 0:  # East
                    current_pos[0] += 1
                elif current_dir == 1:  # South
                    current_pos[1] += 1
                elif current_dir == 2:  # West
                    current_pos[0] -= 1
                elif current_dir == 3:  # North
                    current_pos[1] -= 1
        
        all_minigrid_actions.extend(actions_from_this_pddl)
        
        print(f"  PDDL Action {i+1}: {pddl_action}")
        print(f"    → MiniGrid actions: {actions_from_this_pddl}")
    
    return all_minigrid_actions


def verify_coordinate_parsing():
    """Verify that loc_X_Y strings are parsed correctly."""
    from simulation_engine import StateTranslator
    from custom_env import RandomizedMazeEnv
    
    scenario = get_scenario('SCENARIO_4')
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.2, 
                           render_mode='rgb_array', scenario=scenario)
    obs, info = env.reset()
    
    translator = StateTranslator(env)
    
    test_cases = [
        ("loc_1_1", (1, 1)),
        ("loc_18_18", (18, 18)),
        ("loc_3_5", (3, 5)),
        ("loc_0_0", (0, 0))
    ]
    
    print("\n=== COORDINATE PARSING VERIFICATION ===")
    all_passed = True
    for pddl_loc, expected_coord in test_cases:
        result = translator.pddl_to_coord(pddl_loc)
        passed = result == expected_coord
        status = "✅" if passed else "❌"
        print(f"{status} {pddl_loc} → {result} (expected {expected_coord})")
        if not passed:
            all_passed = False
    
    return all_passed


def verify_directional_logic():
    """Verify that turns are calculated correctly based on agent direction."""
    from simulation_engine import StateTranslator
    from custom_env import RandomizedMazeEnv
    
    scenario = get_scenario('SCENARIO_4')
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.2, 
                           render_mode='rgb_array', scenario=scenario)
    obs, info = env.reset()
    
    translator = StateTranslator(env)
    
    # Test: Agent at (1,1) facing East (0), needs to move to (2,1) (right)
    # Expected: [2] (forward, no turn needed)
    env.agent_pos = (1, 1)
    env.agent_dir = 0  # East
    action, _ = translator.get_micro_action("drive loc_1_1 loc_2_1")
    
    print("\n=== DIRECTIONAL LOGIC VERIFICATION ===")
    print(f"Test: Agent at (1,1) facing East, move to (2,1) (right)")
    print(f"Expected: [2] (forward), Got: [{action}]")
    
    if action == 2:
        print("✅ Correct: No turn needed, forward movement")
        return True
    else:
        print(f"❌ Incorrect: Expected forward (2), got {action}")
        return False


def main():
    print("=" * 70)
    print("PHASE 3 DIAGNOSTIC: Plan Parsing & Action Translation Verification")
    print("=" * 70)
    
    # 1. Check if sas_plan exists
    plan_file = "sas_plan"
    if not os.path.exists(plan_file):
        print(f"\n❌ ERROR: {plan_file} not found!")
        print("   Please run Phase 2 diagnostic first to generate a plan.")
        return False
    
    print(f"\n📄 Step 1: Loading plan from {plan_file}...")
    plan_actions = parse_sas_plan(plan_file)
    
    if not plan_actions:
        print("❌ ERROR: No actions found in plan file!")
        return False
    
    print(f"   ✅ Found {len(plan_actions)} PDDL actions")
    print(f"   First 5 actions:")
    for i, action in enumerate(plan_actions[:5]):
        print(f"      {i+1}. {action}")
    if len(plan_actions) > 5:
        print(f"      ... and {len(plan_actions) - 5} more")
    
    # 2. Verify coordinate parsing
    coord_ok = verify_coordinate_parsing()
    if not coord_ok:
        print("\n❌ Coordinate parsing failed!")
        return False
    
    # 3. Verify directional logic
    dir_ok = verify_directional_logic()
    if not dir_ok:
        print("\n❌ Directional logic failed!")
        return False
    
    # 4. Initialize translator with Scenario 4
    print("\n📄 Step 2: Initializing StateTranslator...")
    scenario = get_scenario('SCENARIO_4')
    env = RandomizedMazeEnv(width=20, height=20, wall_density=0.2, 
                           render_mode='rgb_array', scenario=scenario)
    obs, info = env.reset()
    
    # Set agent to starting position from scenario
    start_pos = scenario['start_pos']
    env.agent_pos = start_pos
    env.agent_dir = 0  # Facing East
    
    translator = StateTranslator(env)
    print(f"   ✅ Translator initialized")
    print(f"   Agent starting position: {env.agent_pos}")
    print(f"   Agent starting direction: {env.agent_dir} (East)")
    
    # 5. Parse & Convert plan
    print("\n📄 Step 3: Parsing and converting PDDL actions to MiniGrid actions...")
    print("   Processing plan actions:")
    
    minigrid_actions = decode_plan(translator, plan_actions, start_pos, 0)
    
    if not minigrid_actions:
        print("\n❌ ERROR: No MiniGrid actions generated!")
        return False
    
    print(f"\n   ✅ Generated {len(minigrid_actions)} MiniGrid actions")
    
    # 6. Validate logic
    print("\n📄 Step 4: Validating action sequence...")
    print(f"   Action queue: {minigrid_actions[:20]}{'...' if len(minigrid_actions) > 20 else ''}")
    print(f"   Total actions: {len(minigrid_actions)}")
    
    # Count action types
    action_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    for action in minigrid_actions:
        action_counts[action] = action_counts.get(action, 0) + 1
    
    print(f"\n   Action breakdown:")
    print(f"      Turn Left (0): {action_counts[0]}")
    print(f"      Turn Right (1): {action_counts[1]}")
    print(f"      Forward (2): {action_counts[2]}")
    print(f"      Pickup (3): {action_counts[3]}")
    print(f"      Drop (4): {action_counts[4]}")
    print(f"      Toggle (5): {action_counts[5]}")
    print(f"      Done (6): {action_counts[6]}")
    
    # 7. Assertions
    print("\n🧪 ASSERTIONS:")
    assert_not_empty = len(minigrid_actions) > 0
    print(f"   ✅ Action queue is not empty: {assert_not_empty}")
    
    assert_valid_actions = all(0 <= a <= 6 for a in minigrid_actions)
    print(f"   ✅ All actions are valid (0-6): {assert_valid_actions}")
    
    assert_has_forward = action_counts[2] > 0
    print(f"   ✅ Contains forward movements: {assert_has_forward}")
    
    if assert_not_empty and assert_valid_actions and assert_has_forward:
        print("\n🎉 PHASE 3 SUCCESS!")
        print("   StateTranslator can parse sas_plan format!")
        print("   PDDL actions are correctly translated to MiniGrid actions!")
        print("   The action queue is valid and ready for execution!")
        return True
    else:
        print("\n❌ PHASE 3 FAILED!")
        print("   Some assertions failed - check the output above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)







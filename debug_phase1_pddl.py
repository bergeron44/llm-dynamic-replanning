#!/usr/bin/env python3
"""
Phase 1 Diagnostic Script - PDDL Generation Verification
QA Automation Engineer: Debug PDDL object vs predicate handling
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scenarios import get_scenario
from custom_env import RandomizedMazeEnv
from state_manager import StateManager
from pddl_patcher import PDDLPatcher

def extract_pddl_section(pddl_content, section_name):
    """Extract a section from PDDL content (e.g., :objects or :init)"""
    start_marker = f"(:{section_name.lower()}"
    end_markers = [":init", ":goal", ")"] if section_name.lower() == "objects" else [":goal", ")"]

    start_idx = pddl_content.find(start_marker)
    if start_idx == -1:
        return f"Section {section_name} not found"

    # Find the end of this section
    content_after = pddl_content[start_idx:]
    end_idx = len(content_after)

    for marker in end_markers:
        marker_idx = content_after.find(f"(:{marker}")
        if marker_idx != -1 and marker_idx < end_idx:
            end_idx = marker_idx

    section_content = content_after[:end_idx].strip()
    return section_content

def main():
    print("=" * 60)
    print("PHASE 1 DIAGNOSTIC: PDDL Generation Verification")
    print("=" * 60)

    # 1. Setup
    print("\n1. SETUP")
    print("-" * 20)

    # Load SCENARIO_4
    scenario = get_scenario("SCENARIO_4")
    if not scenario:
        print("❌ Failed to load SCENARIO_4")
        return

    print(f"✅ Loaded scenario: {scenario['name']}")

    # Initialize Environment
    env = RandomizedMazeEnv(
        width=scenario.get('width', 20),
        height=scenario.get('height', 20),
        wall_density=0.2,
        render_mode='rgb_array',
        scenario=scenario
    )
    obs, info = env.reset()
    print(f"✅ Environment initialized: {env.width}x{env.height}")

    # Initialize StateManager and PDDLPatcher
    state_manager = StateManager()
    patcher = PDDLPatcher("debug_problem.pddl")
    print("✅ StateManager and PDDLPatcher initialized")

    # 2. Generate Static PDDL
    print("\n2. GENERATE STATIC PDDL")
    print("-" * 25)

    # Create basic problem file (same logic as in run_live_dashboard.py)
    with open("debug_problem.pddl", "w") as f:
        f.write("""(define (problem supermarket-navigation-problem)
    (:domain supermarket-navigation)
    (:objects
      agent - agent
      home victory_loc - location
      victory - store
      milk - item
    )
    (:init
      (at_agent agent home)
      (at_store victory victory_loc)
      (selling victory milk)
      (connected home victory_loc)
      (connected victory_loc home)
      (clear victory_loc)
    )
    (:goal (and (have agent milk)))
    )""")

    # Read and display the sections
    with open("debug_problem.pddl", "r") as f:
        static_pddl = f.read()

    print("📋 STATIC PDDL - OBJECTS SECTION:")
    objects_section = extract_pddl_section(static_pddl, "objects")
    print(objects_section)

    print("\n📋 STATIC PDDL - INIT SECTION:")
    init_section = extract_pddl_section(static_pddl, "init")
    print(init_section)

    # 3. Simulate Wall Discovery
    print("\n3. SIMULATE WALL DISCOVERY")
    print("-" * 28)

    print("🔍 Adding discovered wall: name='wall_at_4_1', type='wall', pos=(4,1)")

    # This is the critical test - how does the system handle wall discovery?
    state_manager.add_discovery("wall_at_4_1", (4, 1), obj_type='wall')

    # Get the predicates to inject
    current_predicates = state_manager.get_current_state_predicates()
    print(f"📝 Predicates to inject: {current_predicates}")

    # Inject them into PDDL
    success = patcher.inject_dynamic_state(current_predicates)
    print(f"✅ PDDL injection success: {success}")

    # Read updated PDDL
    with open("debug_problem.pddl", "r") as f:
        updated_pddl = f.read()

    print("\n📋 UPDATED PDDL - OBJECTS SECTION:")
    updated_objects = extract_pddl_section(updated_pddl, "objects")
    print(updated_objects)

    print("\n📋 UPDATED PDDL - INIT SECTION:")
    updated_init = extract_pddl_section(updated_pddl, "init")
    print(updated_init)

    # 4. Assertions
    print("\n4. ASSERTIONS")
    print("-" * 12)

    # Check if wall appears as object (SHOULD FAIL)
    wall_as_object = "wall_at_4_1" in updated_objects
    print(f"❌ Wall as OBJECT in (:objects): {wall_as_object} {'← THIS SHOULD BE FALSE' if wall_as_object else '← GOOD'}")

    # Check if wall appears as blocked predicate (SHOULD PASS)
    wall_as_blocked = "(blocked loc_4_1)" in updated_pddl
    print(f"✅ Wall as BLOCKED predicate: {wall_as_blocked} {'← GOOD' if wall_as_blocked else '← THIS SHOULD BE TRUE'}")

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if wall_as_object and not wall_as_blocked:
        print("🚨 CRITICAL: Walls are being added as OBJECTS instead of BLOCKED predicates!")
        print("   This will break PDDL parsing and planning.")
    elif not wall_as_object and wall_as_blocked:
        print("✅ GOOD: Walls are correctly handled as BLOCKED predicates.")
    else:
        print("⚠️  MIXED: Unexpected behavior - check the logic.")

    print("\nDebug file saved as: debug_problem.pddl")

if __name__ == "__main__":
    main()






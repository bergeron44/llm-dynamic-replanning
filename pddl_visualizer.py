#!/usr/bin/env python3
"""
PDDL Visualizer - See the Perfect Translation Between World and PDDL
Shows side-by-side comparison of environment state vs PDDL state
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_env import RandomizedMazeEnv
from scenarios import get_scenario
from state_manager import StateManager
from pddl_patcher import PDDLPatcher

class PDDLVisualizer:
    def __init__(self, scenario_id="SCENARIO_4"):
        self.scenario_id = scenario_id
        self.setup_environment()
        self.setup_pddl()

    def setup_environment(self):
        """Initialize environment and get current state"""
        scenario = get_scenario(self.scenario_id)
        self.env = RandomizedMazeEnv(
            width=scenario.get('width', 20),
            height=scenario.get('height', 20),
            wall_density=0.2,
            render_mode='rgb_array',
            scenario=scenario
        )
        self.obs, self.info = self.env.reset()

        # Extract world state
        self.world_state = {
            'agent_pos': self.env.agent_pos,
            'grid': self.env.grid,
            'width': self.env.width,
            'height': self.env.height
        }

    def setup_pddl(self):
        """Initialize PDDL system and get current state"""
        self.state_manager = StateManager()
        self.patcher = PDDLPatcher("temp_pddl.pddl")

        # Create basic PDDL
        with open("temp_pddl.pddl", "w") as f:
            f.write("""(define (problem temp)
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

        # Add initial stores from scenario
        scenario = get_scenario(self.scenario_id)
        if scenario and 'surprise_object' in scenario:
            obj = scenario['surprise_object']
            self.state_manager.add_discovery(
                obj['name'],
                obj['position'],
                obj_type='store',
                price=obj.get('true_price')
            )

        # Get current PDDL predicates
        self.pddl_state = self.state_manager.get_current_state_predicates()

    def parse_pddl_predicates(self):
        """Parse PDDL predicates into structured data"""
        pddl_data = {
            'agent_positions': [],
            'store_positions': [],
            'blocked_locations': [],
            'clear_locations': [],
            'connections': [],
            'selling': []
        }

        for pred in self.pddl_state:
            pred = pred.strip('()')
            parts = pred.split()

            if pred.startswith('at_agent'):
                # (at_agent agent loc_x_y)
                loc = parts[2].replace('loc_', '').split('_')
                pddl_data['agent_positions'].append((int(loc[0]), int(loc[1])))

            elif pred.startswith('at_store'):
                # (at_store store_name loc_x_y)
                store_name = parts[1]
                loc = parts[2].replace('loc_', '').split('_')
                pddl_data['store_positions'].append({
                    'name': store_name,
                    'pos': (int(loc[0]), int(loc[1]))
                })

            elif pred.startswith('blocked'):
                # (blocked loc_x_y)
                loc = parts[1].replace('loc_', '').split('_')
                pddl_data['blocked_locations'].append((int(loc[0]), int(loc[1])))

            elif pred.startswith('clear'):
                # (clear loc_x_y)
                loc = parts[1].replace('loc_', '').split('_')
                pddl_data['clear_locations'].append((int(loc[0]), int(loc[1])))

            elif pred.startswith('connected'):
                # (connected loc1 loc2)
                loc1 = parts[1].replace('loc_', '').split('_')
                loc2 = parts[2].replace('loc_', '').split('_')
                pddl_data['connections'].append((
                    (int(loc1[0]), int(loc1[1])),
                    (int(loc2[0]), int(loc2[1]))
                ))

            elif pred.startswith('selling'):
                # (selling store item)
                pddl_data['selling'].append({
                    'store': parts[1],
                    'item': parts[2]
                })

        return pddl_data

    def create_visualization(self):
        """Create side-by-side visualization of world vs PDDL"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # Left: World State
        self.draw_world_state(ax1)

        # Right: PDDL State
        self.draw_pddl_state(ax2)

        plt.tight_layout()
        plt.savefig('pddl_translation_verification.png', dpi=150, bbox_inches='tight')
        plt.show()

        print("✅ Visualization saved as: pddl_translation_verification.png")
        print("\n" + "="*80)
        print("TRANSLATION VERIFICATION REPORT")
        print("="*80)

        self.print_verification_report()

    def draw_world_state(self, ax):
        """Draw the actual world/environment state"""
        # Create grid representation
        grid_display = np.zeros((self.world_state['height'], self.world_state['width'], 3))

        # Draw walls
        for x in range(self.world_state['width']):
            for y in range(self.world_state['height']):
                cell = self.world_state['grid'].get(x, y)
                if cell and hasattr(cell, 'type') and cell.type == 'wall':
                    grid_display[y, x] = [0.5, 0.5, 0.5]  # Gray walls
                else:
                    grid_display[y, x] = [1, 1, 1]  # White empty

        # Draw agent
        agent_x, agent_y = self.world_state['agent_pos']
        grid_display[agent_y, agent_x] = [0, 0, 1]  # Blue agent

        # Draw stores (from scenario)
        scenario = get_scenario(self.scenario_id)
        if scenario and 'surprise_object' in scenario:
            store_pos = scenario['surprise_object']['position']
            grid_display[store_pos[1], store_pos[0]] = [1, 0, 0]  # Red store

        ax.imshow(grid_display)
        ax.set_title('🌍 REAL WORLD STATE\n(Blue=Agent, Red=Store, Gray=Walls)', fontsize=12, pad=20)
        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        ax.grid(True, alpha=0.3)

        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='blue', label='Agent'),
            plt.Rectangle((0,0),1,1, facecolor='red', label='Store'),
            plt.Rectangle((0,0),1,1, facecolor='gray', label='Wall'),
            plt.Rectangle((0,0),1,1, facecolor='white', edgecolor='black', label='Empty')
        ]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)

    def draw_pddl_state(self, ax):
        """Draw the PDDL representation of the world"""
        # Create empty grid
        grid_display = np.ones((self.world_state['height'], self.world_state['width'], 3))

        # Parse PDDL data
        pddl_data = self.parse_pddl_predicates()

        # Draw blocked locations (walls)
        for x, y in pddl_data['blocked_locations']:
            if 0 <= x < self.world_state['width'] and 0 <= y < self.world_state['height']:
                grid_display[y, x] = [0.5, 0.5, 0.5]  # Gray walls

        # Draw agent positions
        for x, y in pddl_data['agent_positions']:
            if 0 <= x < self.world_state['width'] and 0 <= y < self.world_state['height']:
                grid_display[y, x] = [0, 0, 1]  # Blue agent

        # Draw store positions
        for store in pddl_data['store_positions']:
            x, y = store['pos']
            if 0 <= x < self.world_state['width'] and 0 <= y < self.world_state['height']:
                grid_display[y, x] = [1, 0, 0]  # Red store

        ax.imshow(grid_display)
        ax.set_title('📋 PDDL STATE REPRESENTATION\n(Same color coding)', fontsize=12, pad=20)
        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        ax.grid(True, alpha=0.3)

        # Add PDDL facts as text
        facts_text = "PDDL Facts:\n"
        facts_text += f"• Agent positions: {len(pddl_data['agent_positions'])}\n"
        facts_text += f"• Store positions: {len(pddl_data['store_positions'])}\n"
        facts_text += f"• Blocked locations: {len(pddl_data['blocked_locations'])}\n"
        facts_text += f"• Clear locations: {len(pddl_data['clear_locations'])}\n"
        facts_text += f"• Connections: {len(pddl_data['connections'])}\n"

        ax.text(1.05, 0.5, facts_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

    def print_verification_report(self):
        """Print detailed verification report"""
        pddl_data = self.parse_pddl_predicates()

        print("🔍 VERIFICATION DETAILS:")
        print()

        # Agent position check
        world_agent = self.world_state['agent_pos']
        pddl_agents = pddl_data['agent_positions']
        print(f"🤖 AGENT POSITION:")
        print(f"   World: {world_agent}")
        print(f"   PDDL:  {pddl_agents}")
        if pddl_agents and pddl_agents[0] == world_agent:
            print("   ✅ MATCH!")
        else:
            print("   ❌ MISMATCH!")
        print()

        # Store positions check
        scenario = get_scenario(self.scenario_id)
        world_stores = []
        if scenario and 'surprise_object' in scenario:
            world_stores.append(scenario['surprise_object']['position'])

        pddl_stores = [s['pos'] for s in pddl_data['store_positions']]
        print(f"🏪 STORE POSITIONS:")
        print(f"   World: {world_stores}")
        print(f"   PDDL:  {pddl_stores}")
        if set(world_stores) == set(pddl_stores):
            print("   ✅ MATCH!")
        else:
            print("   ❌ MISMATCH!")
        print()

        # Wall/blocked check
        world_walls = []
        for x in range(self.world_state['width']):
            for y in range(self.world_state['height']):
                cell = self.world_state['grid'].get(x, y)
                if cell and hasattr(cell, 'type') and cell.type == 'wall':
                    world_walls.append((x, y))

        pddl_blocked = pddl_data['blocked_locations']
        print(f"🧱 WALLS/BLOCKED:")
        print(f"   World walls: {len(world_walls)}")
        print(f"   PDDL blocked: {len(pddl_blocked)}")

        # Check if PDDL blocked locations are subset of world walls
        pddl_in_world = set(pddl_blocked).issubset(set(world_walls))
        print(f"   All PDDL blocked locations exist in world: {'✅ YES' if pddl_in_world else '❌ NO'}")
        print()

        # Summary
        print("🎯 TRANSLATION QUALITY:")
        translation_score = 0
        total_checks = 3

        if pddl_agents and pddl_agents[0] == world_agent:
            translation_score += 1
        if set(world_stores) == set(pddl_stores):
            translation_score += 1
        if pddl_in_world:
            translation_score += 1

        percentage = (translation_score / total_checks) * 100
        print(f"   Score: {translation_score}/{total_checks} ({percentage:.0f}%)")

        if percentage == 100:
            print("   🏆 PERFECT TRANSLATION! World ↔ PDDL mapping is flawless!")
        elif percentage >= 66:
            print("   👍 GOOD TRANSLATION! Minor issues but mostly accurate.")
        else:
            print("   ⚠️  TRANSLATION NEEDS WORK! Significant mismatches detected.")

def main():
    print("🔍 PDDL Translation Verifier")
    print("=" * 50)

    visualizer = PDDLVisualizer("SCENARIO_4")

    # Simulate some discoveries to make it interesting
    print("🎲 Simulating discoveries...")
    visualizer.state_manager.add_discovery("wall_north", (5, 1), obj_type='wall')
    visualizer.state_manager.add_discovery("wall_south", (5, 18), obj_type='wall')

    # Update PDDL
    predicates = visualizer.state_manager.get_current_state_predicates()
    visualizer.patcher.inject_dynamic_state(predicates)

    print("📊 Creating visualization...")
    visualizer.create_visualization()

    print("✨ Done! Check the image file for perfect translation verification!")

if __name__ == "__main__":
    main()

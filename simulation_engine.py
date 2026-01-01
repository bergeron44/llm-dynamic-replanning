"""
Simulation Engine - Core PDDL Planning and Translation Logic
Handles FastDownward integration, state translation, and entity detection.
"""

import subprocess
import os
import re
from typing import List, Tuple, Dict, Optional, Set
import numpy as np
from minigrid.core.world_object import Wall


class FastDownwardRunner:
    """
    Runs Fast Downward planner on PDDL domain and problem files.
    """

    def __init__(self, fd_path=None, env=None):
        if fd_path is None:
            # Try to find the Fast Downward executable
            import os
            possible_paths = [
                "./downward/fast-downward.py",
                os.path.expanduser("~/Desktop/replaning/downward/fast-downward.py"),
                "/Users/ronberger/Desktop/replaning/downward/fast-downward.py"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    fd_path = path
                    break
        self.fd_path = fd_path
        self.env = env

    def run_planner(self, domain_file: str, problem_file: str) -> List[str]:
        """
        Execute Fast Downward planner. NO FALLBACK ALLOWED.

        Args:
            domain_file: Path to PDDL domain file
            problem_file: Path to PDDL problem file

        Returns:
            List of action strings (without parentheses)

        Raises:
            RuntimeError: If Fast Downward fails
        """
        import subprocess
        import os

        # Execute Fast Downward - NO FALLBACK
        cmd = [
            self.fd_path,
            domain_file,
            problem_file,
            "--search",
            "astar(lmcut())"
        ]

        print(f"🔍 Executing Fast Downward: {' '.join(cmd)}")

        # ==============================================================================
        # DEBUG: DUMP PDDL FILES BEFORE EXECUTION
        # ==============================================================================
        print("\n" + "="*70)
        print("--- DEBUG: DUMPING domain.pddl ---")
        print("="*70)
        try:
            with open(domain_file, 'r') as f:
                domain_content = f.read()
            print(domain_content)
        except Exception as e:
            print(f"❌ ERROR reading domain.pddl: {e}")
        
        print("\n" + "="*70)
        print("--- DEBUG: DUMPING problem_initial.pddl ---")
        print("="*70)
        try:
            with open(problem_file, 'r') as f:
                problem_content = f.read()
            print(problem_content)
        except Exception as e:
            print(f"❌ ERROR reading problem_initial.pddl: {e}")
        
        print("="*70 + "\n")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        if result.returncode != 0:
            error_msg = f"Fast Downward failed with exit code {result.returncode}"
            print(f"❌ {error_msg}")
            raise RuntimeError(f"{error_msg}: {result.stderr}")

        # Check if sas_plan file was created
        if not os.path.exists("sas_plan"):
            error_msg = "Fast Downward completed but no sas_plan file found"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        # Read and parse the plan
        print("📄 Reading sas_plan file...")
        with open("sas_plan", "r") as f:
            raw_plan_content = f.read()
        print(f"📄 Raw sas_plan content:\n{repr(raw_plan_content)}")

        plan_actions = []
        for line in raw_plan_content.split('\n'):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith(";"):
                continue

            # Remove parentheses and extract action
            if line.startswith("(") and line.endswith(")"):
                action = line[1:-1]  # Remove parentheses
                plan_actions.append(action)

        # Keep sas_plan for debugging - don't delete it
        # if os.path.exists("sas_plan"):
        #     os.remove("sas_plan")

        print(f"✅ Fast Downward found plan with {len(plan_actions)} actions")
        return plan_actions

    def _parse_blocked_locations(self, problem_file: str) -> set:
        """Parse blocked locations from PDDL problem file."""
        blocked = set()
        try:
            with open(problem_file, 'r') as f:
                content = f.read()
                # Find all (blocked loc_X_Y) predicates
                import re
                blocked_matches = re.findall(r'\(blocked loc_(\d+)_(\d+)\)', content)
                for x, y in blocked_matches:
                    blocked.add((int(x), int(y)))
        except Exception as e:
            print(f"Warning: Could not parse blocked locations: {e}")
        return blocked

    def _bfs_path(self, start: tuple, goal: tuple, blocked: set) -> list:
        """Find shortest path using BFS, avoiding blocked positions."""
        from collections import deque

        if start == goal:
            return [start]

        if start in blocked or goal in blocked:
            return None

        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()

            # Try all 4 directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_pos = (current[0] + dx, current[1] + dy)

                # Check bounds (assume 20x20 grid)
                if not (0 <= next_pos[0] < 20 and 0 <= next_pos[1] < 20):
                    continue

                if next_pos == goal:
                    return path + [next_pos]

                if next_pos not in visited and next_pos not in blocked:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))

        return None  # No path found

    def _bfs_planner(self, domain_file: str, problem_file: str) -> list:
        # Read problem file content
        try:
            with open(problem_file, 'r') as f:
                problem_file_content = f.read()
        except:
            problem_file_content = ""
        """Simple BFS planner as fallback when Fast Downward fails."""
        print("🧭 BFS Planner: Finding path using Breadth-First Search")

        # Parse blocked locations
        blocked = self._parse_blocked_locations(problem_file)

        # Parse start and goal from problem file
        start_pos = None
        goal_stores = []  # List of stores that sell milk
        try:
            with open(problem_file, 'r') as f:
                content = f.read()
                # Find start location (agent position)
                import re
                start_match = re.search(r'\(at_agent agent loc_(\d+)_(\d+)\)', content)
                if start_match:
                    start_pos = (int(start_match.group(1)), int(start_match.group(2)))

                # Find all stores that sell milk
                selling_matches = re.findall(r'\(selling (\w+) milk\)', content)
                goal_stores = selling_matches

                print(f"Found stores that sell milk: {goal_stores}")
        except Exception as e:
            print(f"Warning: Could not parse problem: {e}")

        if not start_pos:
            start_pos = (1, 1)  # Default start

        # For now, pick the first store as goal
        target_store = "victory"  # Default
        if goal_stores:
            # Find the position of the first store
            store_name = goal_stores[0]
            target_store = store_name
            store_match = re.search(f'\\(at {store_name} loc_(\\d+)_(\\d+)\\)', content)
            if store_match:
                goal_pos = (int(store_match.group(1)), int(store_match.group(2)))
                print(f"Planning to store: {store_name} at {goal_pos}")
            else:
                goal_pos = (18, 18)  # Fallback
        else:
            goal_pos = (18, 18)  # Fallback

        print(f"📍 Planning path from {start_pos} to {goal_pos}")

        # Use proper BFS to find shortest path avoiding blocked locations
        # Also consider environment grid if available (only walls)
        if hasattr(self, 'env') and self.env:
            # Get additional blocked locations from environment grid (only walls)
            env_blocked = set()
            for x in range(self.env.width):
                for y in range(self.env.height):
                    cell = self.env.grid.get(x, y)
                    if cell and hasattr(cell, 'type') and cell.type == 'wall':
                        env_blocked.add((x, y))
            if env_blocked:
                blocked.update(env_blocked)
                print(f"📍 Added {len(env_blocked)} wall locations from environment grid")

        path = self._bfs_path(start_pos, goal_pos, blocked)
        if path and len(path) > 1:
            actions = []
            for i in range(len(path) - 1):
                from_pos = path[i]
                to_pos = path[i + 1]
                actions.append(f"drive loc_{from_pos[0]}_{from_pos[1]} loc_{to_pos[0]}_{to_pos[1]}")

            # Add buy action for the target store
            actions.append(f"buy milk {target_store} 4.0")
            print(f"✅ BFS found path with {len(actions)} actions")
            return actions

        print("❌ BFS could not find valid path")
        return []

        # For debugging: try a very simple plan to the first store
        if goal_stores:
            store_name = goal_stores[0]
            store_pos = None
            for match in re.finditer(f'\\(at {store_name} loc_(\\d+)_(\\d+)\\)', problem_file_content):
                store_pos = (int(match.group(1)), int(match.group(2)))
                break

            if store_pos and abs(store_pos[0] - start_pos[0]) + abs(store_pos[1] - start_pos[1]) <= 5:
                # Simple path to nearby store
                actions = []
                cx, cy = start_pos[0], start_pos[1]
                tx, ty = store_pos[0], store_pos[1]

                # Simple diagonal-ish path
                while cx != tx or cy != ty:
                    if cx < tx:
                        cx += 1
                    elif cy < ty:
                        cy += 1
                    else:
                        break

                    if cx <= max_size and cy <= max_size:
                        actions.append(f"drive loc_{cx-1}_{cy-1} loc_{cx}_{cy}")
                    else:
                        actions = []
                        break

                    if len(actions) > 10:
                        break

                if actions:
                    actions.append("buy milk victory 4.0")
                    print(f"✅ Generated simple plan to nearby store with {len(actions)} actions")
                    return actions

        # Fallback: just try to go to (3,3) if it's a valid store
        if (3, 3) not in blocked:
            actions = [f"drive loc_{start_pos[0]}_{start_pos[1]} loc_2_2",
                      "drive loc_2_2 loc_3_3",
                      "buy milk victory 4.0"]
            print(f"✅ Generated hardcoded plan with {len(actions)} actions")
            return actions

        print("❌ Could not generate any plan")
        return []

    def _validate_single_step(self, from_pos, to_pos, blocked):
        """Validate that a single step from from_pos to to_pos is valid."""
        # Check if the destination is blocked
        if to_pos in blocked:
            return False

        # Check if this is a valid single step (adjacent positions)
        dx = abs(to_pos[0] - from_pos[0])
        dy = abs(to_pos[1] - from_pos[1])

        # Must be exactly one step in one direction
        if not ((dx == 1 and dy == 0) or (dx == 0 and dy == 1)):
            return False

        return True


class StateTranslator:
    """
    Translates between MiniGrid coordinates and PDDL location names.
    """

    def __init__(self, env):
        self.env = env
        self.action_buffer = []
        self.stuck_counter = {}  # Track how many times we tried the same action
        self.recent_failures = []  # Track recent failed forward attempts
        self.stuck_positions = {}  # Track how many times we replanned at same position

        # Action mappings (matching MiniGrid action space)
        self.minigrid_to_pddl = {
            0: "turn left",
            1: "turn right",
            2: "forward",
            3: "pickup",
            4: "drop",
            5: "toggle",
            6: "done"
        }

    def has_actions(self) -> bool:
        """Check if action_buffer has pending actions."""
        return len(self.action_buffer) > 0

    def clear_buffer(self):
        """Clear the action buffer (used on replan)."""
        self.action_buffer = []

    def coord_to_pddl(self, coord: Tuple[int, int]) -> str:
        """Convert (x,y) coordinate to PDDL location format loc_x_y"""
        return f"loc_{coord[0]}_{coord[1]}"

    def pddl_to_coord(self, pddl_loc: str) -> Tuple[int, int]:
        """Convert PDDL location format loc_x_y to (x,y) coordinate"""
        match = re.match(r'loc_(\d+)_(\d+)', pddl_loc)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0)

    def get_micro_action(self, pddl_action, agent):
        """
        Translate PDDL action to motor commands.
        FIXED: Now correctly parses target location and calculates required direction.

        Args:
            pddl_action: String like "drive loc_1_1 loc_1_2" or "buy milk victory loc_18_18"
            agent: Mock agent object with .pos and .dir attributes

        Returns:
            tuple: (motor_action, target_pos)
                motor_action: int (0=TurnLeft, 1=TurnRight, 2=Forward, 6=Done)
                target_pos: tuple (x, y) or None
        """
        if not pddl_action:
            return 6, None  # Done action
        
        # If we have buffered actions from previous calls, continue with them
        # CRITICAL FIX: When buffer exists, the main loop will pop from it directly
        # So we don't need to return anything here - just indicate buffer has actions
        if self.action_buffer:
            # Return None to indicate buffer should be used (main loop pops directly)
            target_pos = getattr(self, '_current_target', None)
            return None, target_pos
        
        # Parse PDDL action
        parts = pddl_action.replace('(', '').replace(')', '').split()
        action_type = parts[0] if parts else None
        
        # ========== DRIVE ACTION ==========
        if action_type == 'drive' and len(parts) >= 3:
            from_loc = parts[1]  # loc_X1_Y1 (source)
            to_loc = parts[2]    # loc_X2_Y2 (destination)
            
            try:
                # Parse destination coordinates "loc_X_Y"
                to_coords = to_loc.replace("loc_", "").split("_")
                if len(to_coords) != 2:
                    print(f"[TRANSLATE] ERROR: Invalid location format: {to_loc}")
                    return 6, None

                target_x, target_y = int(to_coords[0]), int(to_coords[1])
                target_pos = (target_x, target_y)

                # Get current agent state (use mock_agent if provided, otherwise env)
                if agent and hasattr(agent, 'pos'):
                    current_pos = tuple(agent.pos)
                    current_dir = agent.dir
                else:
                    current_pos = tuple(self.env.agent_pos)
                    current_dir = self.env.agent_dir

                # Check if already at target
                if current_pos == target_pos:
                    # Reset stuck counters on success
                    if hasattr(self, 'stuck_counter'):
                        self.stuck_counter = {}
                    if hasattr(self, 'recent_failures'):
                        self.recent_failures = []
                    return 6, target_pos

                # Calculate required movement delta
                dx = target_x - current_pos[0]
                dy = target_y - current_pos[1]

                print(f"[TRANSLATE] Drive: {current_pos} → {target_pos}, delta=({dx},{dy}), current_dir={current_dir}")

                # Map movement delta to MiniGrid direction
                # MiniGrid convention:
                # 0 = Right (+1, 0)
                # 1 = Down  (0, +1)
                # 2 = Left  (-1, 0)
                # 3 = Up    (0, -1)

                direction_map = {
                    (1, 0): 0,   # Move right: need to face Right (0)
                    (0, 1): 1,   # Move down: need to face Down (1)
                    (-1, 0): 2,  # Move left: need to face Left (2)
                    (0, -1): 3   # Move up: need to face Up (3)
                }

                required_dir = direction_map.get((dx, dy))

                if required_dir is None:
                    print(f"[TRANSLATE] ERROR: Invalid delta ({dx}, {dy}) - must be unit move (distance=1)")
                    return 6, None

                # Calculate turns needed (shortest rotation)
                turns_needed = (required_dir - current_dir) % 4

                print(f"[TRANSLATE] Required_dir={required_dir}, Turns_needed={turns_needed}")

                # Build action sequence: [turns...] + [forward]
                actions = []

                if turns_needed == 1:
                    actions.append(1)  # Turn right once
                elif turns_needed == 2:
                    actions.extend([1, 1])  # Turn right twice (180°)
                elif turns_needed == 3:
                    actions.append(0)  # Turn left (equivalent to 3 rights)
                # turns_needed == 0: already facing correct direction, no turns needed

                actions.append(2)  # Forward

                # CRITICAL FIX: Store ALL actions in buffer (not actions[1:])
                # The main loop will pop from buffer, so we need ALL actions there
                self.action_buffer = actions.copy()
                self._current_target = target_pos  # Store target for buffer pops

                print(f"[TRANSLATE] Action sequence: {actions}, buffer populated with all: {self.action_buffer}")

                # Return None to indicate buffer is populated (main loop will pop from buffer)
                return None, target_pos
                    
            except (ValueError, IndexError) as e:
                print(f"[TRANSLATE] ERROR: Failed to parse drive action '{pddl_action}': {e}")
                return 6, None
        
        # ========== BUY ACTION ==========
        elif action_type == 'buy':
            # Format: "buy milk store_name loc_X_Y"
            # Agent should already be at the location, so just return Done
            print(f"[TRANSLATE] Buy action: {pddl_action}")
            return 6, None
        
        # ========== UNKNOWN ACTION ==========
        else:
            print(f"[TRANSLATE] WARNING: Unknown action type '{action_type}' in: {pddl_action}")
            return 6, None

    def minigrid_action_to_name(self, action_id: int) -> str:
        """Convert MiniGrid action ID to human-readable name"""
        return self.minigrid_to_pddl.get(action_id, "unknown")


def detect_new_entities(mock_agent, forbidden_entities: List[str], env, visual_memory: Set = None) -> Optional[Dict]:
    """
    Detect new entities in the environment that the agent can see.

    Args:
        mock_agent: Mock agent object (for compatibility)
        forbidden_entities: List of entities to ignore (e.g., ['victory'])
        env: MiniGrid environment
        visual_memory: Set of previously seen entity positions

    Returns:
        Dict with new entity info, or None if no new entities
    """
    if visual_memory is None:
        visual_memory = set()

    # Get agent's current position and direction
    agent_pos = env.agent_pos
    agent_dir = env.agent_dir

    # Calculate visible area (simple cone in front of agent)
    visible_positions = set()

    # Front position
    front_pos = env.front_pos
    if front_pos is not None:
        visible_positions.add(tuple(front_pos))

    # Adjacent positions
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            pos = (agent_pos[0] + dx, agent_pos[1] + dy)
            if 0 <= pos[0] < env.width and 0 <= pos[1] < env.height:
                visible_positions.add(pos)

    # Check for entities at visible positions
    for pos in visible_positions:
        cell = env.grid.get(pos[0], pos[1])
        if cell and hasattr(cell, 'name') and cell.name:
            entity_name = cell.name

            # Skip forbidden entities
            if entity_name in forbidden_entities:
                continue

            # Check if we've seen this entity before
            entity_key = (pos[0], pos[1], entity_name)
            if entity_key not in visual_memory:
                return {
                    'name': entity_name,
                    'position': pos,
                    'type': getattr(cell, 'type', 'unknown'),
                    'color': getattr(cell, 'color', 'unknown')
                }

    return None
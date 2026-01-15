"""
PDDL Patcher - Safe PDDL Problem File Updates
Handles dynamic addition of objects and predicates to PDDL problem files.
"""

from typing import List, Tuple
import re


def scale_price_to_int(raw_price) -> int:
    """
    Convert fractional price to integer for PDDL compatibility.
    
    Fast Downward's lmcut heuristic only supports integer costs.
    We scale prices by 10 (e.g., 3.5 becomes 35, 4.0 becomes 40).
    
    Args:
        raw_price: Price as float (e.g., 3.5) or string (e.g., "3.5")
    
    Returns:
        Integer price scaled by 10 (e.g., 35 for 3.5)
    """
    try:
        return int(float(raw_price) * 10)
    except (ValueError, TypeError):
        return 0


def validate_no_fractional_numbers(predicate: str) -> Tuple[bool, str]:
    """
    Validate that a PDDL predicate doesn't contain fractional numbers.
    
    Fast Downward doesn't support fractional numbers in assignments.
    This function checks if a predicate contains floats like 3.5, 4.0, etc.
    
    Args:
        predicate: PDDL predicate string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if no fractional numbers found
        error_message: Empty if valid, otherwise describes the issue
    """
    # Check for decimal numbers (e.g., 3.5, 4.0, .5, 3.)
    fractional_pattern = r'\b\d+\.\d+|\b\.\d+|\b\d+\.\b'
    matches = re.findall(fractional_pattern, predicate)
    
    if matches:
        return False, f"Fractional numbers found in predicate: {matches}"
    
    return True, ""


class PDDLPatcher:
    """
    Safe PDDL problem file patching with idempotent operations.
    """

    def __init__(self, pddl_file_path: str):
        """
        Initialize with path to PDDL problem file.

        Args:
            pddl_file_path: Path to the problem.pddl file
        """
        self.pddl_file_path = pddl_file_path

    def add_blocked_location(self, position: Tuple[int, int]) -> bool:
        """
        Add a blocked location predicate without creating new objects.
        This is used for dynamic obstacle discovery during execution.
        """
        blocked_predicate = f"(blocked loc_{position[0]}_{position[1]})"

        try:
            # Read current content
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError, IOError) as e:
            print(f"[PDDL] Error reading PDDL file: {e}")
            return False

        # Check if predicate already exists
        if blocked_predicate in content:
            print(f"[PDDL] Blocked predicate {blocked_predicate} already exists")
            return True

        # Find the :init section and add the predicate INSIDE it
        init_start = content.find("(:init")
        if init_start == -1:
            print(f"[PDDL] Could not find :init section")
            return False

        # Find the closing ) of :init section by tracking nested parentheses
        depth = 0
        init_end = None
        for i in range(init_start, len(content)):
            char = content[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    init_end = i
                    break

        if init_end is None:
            print(f"[PDDL] Could not find closing ) for :init section")
            return False

        # Insert the blocked predicate INSIDE :init, before the closing )
        new_content = content[:init_end] + f"\n    {blocked_predicate}" + content[init_end:]

        try:
            with open(self.pddl_file_path, 'w') as f:
                f.write(new_content)
            print(f"[PDDL] Added blocked location: {blocked_predicate}")
            return True
        except (PermissionError, IOError) as e:
            print(f"[PDDL] Error writing PDDL file: {e}")
            return False

    def add_new_object(self, obj_name: str, obj_type: str, predicates: List[str], agent_pos: Tuple[int, int] = None) -> bool:
        """
        Idempotent PDDL object addition - safely add or skip if already exists.
        Returns True if object is now in PDDL (either added or already present).
        """
        try:
            # Read current content
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError, IOError) as e:
            print(f"[PDDL] Error reading PDDL file: {e}")
            return False

        # Check if object already exists (case-insensitive search)
        obj_name_lower = obj_name.lower()
        content_lower = content.lower()

        if obj_name_lower in content_lower:
            print(f"[PDDL] Object '{obj_name}' already exists in PDDL file, skipping addition")
            return True  # Success - object is already there

        # Object doesn't exist, try to add it
        try:
            # Find the :objects section and add the new object
            objects_start = content.find("(:objects")
            if objects_start == -1:
                print(f"[PDDL] Could not find :objects section in {self.pddl_file_path}")
                return False

            # Find the end of the objects section
            objects_end = content.find(")", objects_start)
            if objects_end == -1:
                print(f"[PDDL] Could not find end of :objects section")
                return False

            # Insert the new object before the closing parenthesis
            new_object_line = f"\n    {obj_name} - {obj_type}"
            new_content = content[:objects_end] + new_object_line + content[objects_end:]

            # Find the :init section and add predicates
            init_start = new_content.find("(:init")
            if init_start != -1:
                init_end = new_content.find(")", init_start)
                if init_end != -1:
                    # Add predicates before the closing paren of :init
                    predicates_text = "\n    " + "\n    ".join(predicates)
                    new_content = new_content[:init_end] + predicates_text + new_content[init_end:]

            # Write the updated content
            with open(self.pddl_file_path, 'w') as f:
                f.write(new_content)

            print(f"[PDDL] Successfully added object '{obj_name}' to PDDL file")
            return True

        except (PermissionError, IOError) as e:
            print(f"[PDDL] Error writing to PDDL file: {e}")
            return False

    def update_agent_position(self, agent_pos):
        """Updates the (at_agent agent ...) predicate in the PDDL file to current pos."""
        # Use inject_dynamic_state first to ensure proper structure
        new_pred = f"(at_agent agent loc_{agent_pos[0]}_{agent_pos[1]})"
        if self.inject_dynamic_state([new_pred]):
            return True

        # Fallback: direct replace/insert if inject failed
        try:
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()

            if re.search(r'\(at_agent agent loc_\d+_\d+\)', content):
                content = re.sub(r'\(at_agent agent loc_\d+_\d+\)', new_pred, content)
            else:
                init_start = content.find("(:init")
                if init_start == -1:
                    print("[PDDL] Could not find :init section for agent update")
                    return False
                init_end = self._find_init_end(content)
                if init_end == -1:
                    print("[PDDL] Could not find :init end for agent update")
                    return False
                content = content[:init_end] + f"\n    {new_pred}" + content[init_end:]

            with open(self.pddl_file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[PDDL] Error updating agent position: {e}")
            return False

    def update_problem_file(self, agent_pos, discovered_objects, output_path=None):
        """
        Updates the problem PDDL with current agent position and discovered objects.
        Handles dynamic blocking and store logic correctly.
        
        Args:
            agent_pos: Tuple (x, y) of agent position
            discovered_objects: Dict mapping object names to metadata:
                {
                    'name': {
                        'pos': (x, y),
                        'type': 'store' | 'obstacle' | 'wall',
                        'properties': {'price': 2.5, ...}
                    }
                }
            output_path: Optional path to write output (defaults to self.pddl_file_path)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # 1. Read original/current content
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()

            # --- DYNAMIC OBJECT INJECTION ---
            # Collect all known stores that need to be defined
            known_stores = set()
            # Always include victory_store
            known_stores.add("victory_store")

            # Add discovered stores
            for obj_name, metadata in discovered_objects.items():
                if metadata.get('type') == 'store' or metadata.get('sells_milk'):
                    known_stores.add(obj_name)

            # Inject into (:objects section
            if "(:objects" in content:
                # Regex to find the store definition line: e.g. "store1 store2 - store"
                # We look for "- store" and prepend our new stores
                match = re.search(r'([a-zA-Z0-9_ ]+)\s-\sstore', content)
                if match:
                    existing_stores_str = match.group(1)
                    existing_stores = set(existing_stores_str.split())

                    # Merge sets
                    all_stores = existing_stores.union(known_stores)
                    new_stores_str = " ".join(all_stores)

                    # Replace in content
                    content = content.replace(f"{existing_stores_str} - store", f"{new_stores_str} - store")
                else:
                    # Fallback: if no stores defined yet, add them after (:objects
                    stores_def = "\n    " + " ".join(known_stores) + " - store"
                    content = content.replace("(:objects", "(:objects" + stores_def)
            # --------------------------------

            # 2. Update Agent Position
            # Regex to replace (at_agent agent loc_x_y) with new pos
            new_pos_str = f"loc_{agent_pos[0]}_{agent_pos[1]}"
            content = re.sub(r'\(at_agent agent loc_\d+_\d+\)', f'(at_agent agent {new_pos_str})', content)

            # 3. Build Dynamic Predicates
            dynamic_lines = []
            
            for obj_name, metadata in discovered_objects.items():
                loc = metadata.get('pos')  # Tuple (x, y)
                if not loc:
                    continue
                
                loc_str = f"loc_{loc[0]}_{loc[1]}"
                obj_type = metadata.get('type', 'obstacle')
                properties = metadata.get('properties', {})
                
                # --- LOGIC CORE ---
                if obj_type == 'store' or properties.get('sells_milk'):
                    # It is a STORE: Make it accessible and selling milk
                    dynamic_lines.append(f"(at_store {obj_name} {loc_str})")
                    dynamic_lines.append(f"(selling {obj_name} milk)")  # Note: domain uses 'selling' not 'sells'
                    # DO NOT ADD BLOCKED FOR STORES - they must be accessible
                    # Note: Price info is handled in Python logic, not PDDL (Fast Downward doesn't support floats)
                else:
                    # It is an OBSTACLE: Block it
                    dynamic_lines.append(f"(blocked {loc_str})")
                # ------------------

            # 4. Remove old dynamic predicates first (to avoid duplicates)
            # Remove old at_store predicates
            content = re.sub(r'\(at_store \w+ loc_\d+_\d+\)\s*', '', content)
            # Remove old selling predicates
            content = re.sub(r'\(selling \w+ \w+\)\s*', '', content)
            # Remove old blocked predicates (but keep static walls from update_environment_walls)
            # We only remove blocked predicates that match our discovered objects
            for obj_name, metadata in discovered_objects.items():
                loc = metadata.get('pos')
                if loc:
                    loc_str = f"loc_{loc[0]}_{loc[1]}"
                    blocked_pred = f"(blocked {loc_str})"
                    # Remove only if it's not a store
                    if metadata.get('type') != 'store':
                        content = re.sub(re.escape(blocked_pred) + r'\s*', '', content)
            
            # CRITICAL FIX: Remove (clear loc_X_Y) predicates for obstacles
            # blocked and clear are mutually exclusive - cannot have both!
            # When we add (blocked loc_X_Y), we must remove (clear loc_X_Y)
            for obj_name, metadata in discovered_objects.items():
                loc = metadata.get('pos')
                if loc:
                    loc_str = f"loc_{loc[0]}_{loc[1]}"
                    obj_type = metadata.get('type', 'obstacle')
                    # If it's an obstacle (not a store), remove the conflicting (clear ...) predicate
                    if obj_type != 'store':
                        clear_pred = f"(clear {loc_str})"
                        clear_pattern = rf'\(clear\s+{re.escape(loc_str)}\)'
                        if re.search(clear_pattern, content):
                            content = re.sub(clear_pattern + r'\s*', '', content)
                            print(f"[PDDL_PATCHER] ✅ Removed conflicting (clear {loc_str}) for obstacle at {loc}")

            # 5. Inject into :init section
            # Find the :init section and its closing parenthesis
            init_start = content.find("(:init")
            if init_start == -1:
                print(f"[PDDL_PATCHER] ❌ Error: Could not find (:init section")
                return False
            
            # Find the closing ) of :init section by tracking nested parentheses
            depth = 0
            init_end = None
            for i in range(init_start, len(content)):
                char = content[i]
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        init_end = i
                        break
            
            if init_end is None:
                print(f"[PDDL_PATCHER] ❌ Error: Could not find closing ) for :init section")
                return False
            
            # Insert dynamic predicates INSIDE :init, before the closing )
            if dynamic_lines:
                new_predicates = "\n        ".join(dynamic_lines)
                content = content[:init_end] + "\n        " + new_predicates + "\n    " + content[init_end:]
            
            # 6. Write back
            target_path = output_path if output_path else self.pddl_file_path
            with open(target_path, 'w') as f:
                f.write(content)

            print(f"[PDDL_PATCHER] ✅ Successfully updated PDDL with {len(dynamic_lines)} predicates")
            return True

        except Exception as e:
            print(f"[PDDL_PATCHER] ❌ Error updating file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _find_init_end(self, content):
        """Robustly finds the insertion point (closing parenthesis) of the :init block."""
        # Method 1: Look for (:goal and backtrack to the previous )
        goal_idx = content.find("(:goal")
        if goal_idx != -1:
            return content.rfind(")", 0, goal_idx)

        # Method 2: Count parentheses if (:goal is missing
        init_start = content.find("(:init")
        if init_start == -1: return -1

        depth = 0
        for i, char in enumerate(content[init_start:], init_start):
            if char == '(': depth += 1
            elif char == ')': depth -= 1
            if depth == 0: return i
        return -1

    def update_environment_walls(self, env):
        """Adds all walls from the environment to the PDDL file as blocked locations."""
        try:
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()

            # Remove existing blocked and clear predicates
            import re
            content = re.sub(r'\(blocked [^\)]+\)\n?', '', content)
            content = re.sub(r'\(clear [^\)]+\)\n?', '', content)

            # Collect all walls and non-walls (for clear predicates)
            # CRITICAL: MiniGrid uses grid.get(x, y) where x=column (width) and y=row (height)
            # We iterate x (width) then y (height) to match MiniGrid's coordinate system
            # PDDL location strings must match: loc_{x}_{y} corresponds to grid.get(x, y)
            blocked_preds = []
            clear_preds = []
            for x in range(env.width):   # x = column (0 to width-1)
                for y in range(env.height):  # y = row (0 to height-1)
                    # Standard MiniGrid access: grid.get(x, y) where x=column, y=row
                    cell = env.grid.get(x, y)
                    if cell and cell.type == 'wall':
                        # Write loc_{x}_{y} to match what we read from grid.get(x, y)
                        blocked_preds.append(f"(blocked loc_{x}_{y})")
                    else:
                        # Non-wall cells are clear (can be driven to)
                        # Write loc_{x}_{y} to match what we read from grid.get(x, y)
                        clear_preds.append(f"(clear loc_{x}_{y})")

            # USE ROBUST FINDER
            insert_pos = self._find_init_end(content)
            if insert_pos != -1:
                text = "\n    ".join(blocked_preds + clear_preds)
                content = content[:insert_pos] + "\n    " + text + content[insert_pos:]

                with open(self.pddl_file_path, 'w') as f:
                    f.write(content)
                return True

        except (PermissionError, IOError) as e:
            print(f"[PDDL] Error updating wall blocks: {e}")
            return False

        return False

    def init_grid_connectivity(self, width, height):
        """Adds (connected x y) predicates for the entire grid."""
        try:
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()

            # Remove existing connected predicates to avoid duplicates
            import re
            content = re.sub(r'\(connected [^\)]+\)\n?', '', content)

            # Generate all grid connections (bidirectional)
            connected_preds = []
            for x in range(width):
                for y in range(height):
                    # Right neighbor
                    if x + 1 < width:
                        connected_preds.append(f"(connected loc_{x}_{y} loc_{x+1}_{y})")
                        connected_preds.append(f"(connected loc_{x+1}_{y} loc_{x}_{y})")

                    # Down neighbor
                    if y + 1 < height:
                        connected_preds.append(f"(connected loc_{x}_{y} loc_{x}_{y+1})")
                        connected_preds.append(f"(connected loc_{x}_{y+1} loc_{x}_{y})")

            # Add all connected predicates to :init (INSIDE the :init section, before it closes)
            if connected_preds:
                connected_text = "\n    ".join(connected_preds)
                # Find the closing ) of :init section
                init_start = content.find("(:init")
                if init_start != -1:
                    # Find the matching closing parenthesis
                    depth = 0
                    init_end = init_start
                    for i, char in enumerate(content[init_start:], init_start):
                        if char == '(':
                            depth += 1
                        elif char == ')':
                            depth -= 1
                            if depth == 0:
                                init_end = i
                                break
                    # Insert connections BEFORE the closing ) of :init
                    if init_end > init_start:
                        content = content[:init_end] + "\n    " + connected_text + "\n  " + content[init_end:]

                    with open(self.pddl_file_path, 'w') as f:
                        f.write(content)

                    print(f"[PDDL] Added {len(connected_preds)} grid connections to PDDL")
                    return True

        except (PermissionError, IOError) as e:
            print(f"[PDDL] Error initializing grid connectivity: {e}")
            return False

        return False

    def inject_dynamic_state(self, dynamic_predicates: List[str]) -> bool:
        """
        Safely injects dynamic predicates into the PDDL file while preserving static facts.
        Updates agent position and discovered objects without touching walls/connections.
        
        CRITICAL: This method preserves the exact structure of (:init ...) and (:goal ...) sections.

        Args:
            dynamic_predicates (list): List of dynamic predicates to inject

        Returns:
            bool: Success status
        """
        try:
            with open(self.pddl_file_path, 'r') as f:
                content = f.read()

            # 1. Find (:init section boundaries FIRST (before any modifications)
            init_start = content.find("(:init")
            if init_start == -1:
                print(f"[PDDL] Could not find :init marker in {self.pddl_file_path}")
                return False
            
            # Find the LAST closing ) of :init section by tracking nested parentheses
            depth = 0
            init_end = None
            for i in range(init_start, len(content)):
                char = content[i]
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        init_end = i
                        break
            
            if init_end is None:
                print(f"[PDDL] Could not find closing ) for :init in {self.pddl_file_path}")
                return False

            # 2. Extract (:init ... ) block content (without the opening and closing markers)
            init_content = content[init_start + 6:init_end].strip()  # +6 to skip "(:init"
            
            # 3. Remove old dynamic predicates from the init content only
            import re
            # Remove agent position predicates (match multiline patterns)
            init_content = re.sub(r'\(at_agent agent [^)]+\)\s*', '', init_content)
            # Remove discovered object predicates, but PRESERVE victory store (it's static)
            # CRITICAL FIX: Don't remove victory store predicates - they must always exist
            # First, extract victory store predicates to preserve them
            victory_store_preds = []
            victory_at_store = re.search(r'\(at_store victory [^)]+\)', init_content)
            if victory_at_store:
                victory_store_preds.append(victory_at_store.group(0))
            victory_selling = re.search(r'\(selling victory [^)]+\)', init_content)
            if victory_selling:
                victory_store_preds.append(victory_selling.group(0))
            
            # Remove all at_store and selling predicates (including victory temporarily)
            init_content = re.sub(r'\(at_store [^)]+ loc_\d+_\d+\)\s*', '', init_content)
            init_content = re.sub(r'\(selling [^)]+ [^)]+\)\s*', '', init_content)
            init_content = re.sub(r'\(= \(item-price [^)]+\) [^)]+\)\s*', '', init_content)
            
            # Restore victory store predicates (they are static and must always exist)
            if victory_store_preds:
                # Add victory predicates back at the beginning of init_content
                victory_restore = "\n    " + "\n    ".join(victory_store_preds)
                init_content = victory_restore + "\n" + init_content.lstrip()
            else:
                # If victory store doesn't exist yet, we need to add it
                # Try to extract victory_loc from the original content before modifications
                victory_loc_pattern = r'\(at_store\s+victory\s+(loc_\d+_\d+)\)'
                victory_loc_match = re.search(victory_loc_pattern, content)
                if victory_loc_match:
                    victory_loc = victory_loc_match.group(1)
                else:
                    # Default fallback - assume standard victory position
                    victory_loc = "loc_18_18"
                
                # Add victory store predicates if missing
                victory_store_preds = [
                    f"(at_store victory {victory_loc})",
                    "(selling victory milk)"
                ]
                victory_restore = "\n    " + "\n    ".join(victory_store_preds)
                init_content = victory_restore + "\n" + init_content.lstrip()
                print(f"[PDDL] VICTORY FIX: Added missing victory store predicates: {victory_store_preds}")
            
            # Keep blocked/clear/connected predicates - they are static infrastructure

            # 4. Clean up extra whitespace/newlines but preserve structure
            init_content = re.sub(r'\n\s*\n+', '\n    ', init_content)  # Normalize multiple newlines
            if init_content and not init_content.endswith('\n'):
                init_content = init_content.rstrip() + '\n    '

            # 5. Validate predicates for fractional numbers before injection
            if dynamic_predicates:
                # CRITICAL: Fast Downward doesn't support fractional numbers
                # Validate all predicates before adding them
                invalid_predicates = []
                for pred in dynamic_predicates:
                    is_valid, error_msg = validate_no_fractional_numbers(pred)
                    if not is_valid:
                        invalid_predicates.append((pred, error_msg))
                
                if invalid_predicates:
                    error_details = "\n".join([f"  - {pred}: {msg}" for pred, msg in invalid_predicates])
                    print(f"[PDDL] ERROR: Fractional numbers found in predicates!")
                    print(f"[PDDL] Fast Downward only supports integers.")
                    print(f"[PDDL] Invalid predicates:\n{error_details}")
                    print(f"[PDDL] Suggestion: Use scale_price_to_int() to convert prices to integers.")
                return False

                # ==============================================================================
                # 🚨 PHYSICAL CONSTRAINT INVARIANT: Only obstacles/walls block their cells
                # Stores should NOT be blocked - agent needs to enter them to buy milk
                # ==============================================================================
                obstacle_locations = set()  # Set of loc_X_Y strings for obstacles/walls ONLY
                store_locations = set()  # Set of loc_X_Y strings for stores (NOT blocked)
                location_to_obj_name = {}  # Map loc_X_Y -> object name for logging
                
                # Extract all locations where objects are discovered and categorize them
                for pred in dynamic_predicates:
                    # Match (at_store ?store loc_X_Y) patterns (stores) - DO NOT block these!
                    at_store_match = re.search(r'\(at_store\s+(\w+)\s+(loc_\d+_\d+)\)', pred)
                    if at_store_match:
                        obj_name = at_store_match.group(1)
                        loc = at_store_match.group(2)
                        store_locations.add(loc)  # This is a store, not an obstacle
                        location_to_obj_name[loc] = obj_name
                    
                    # Match (blocked loc_X_Y) patterns (obstacles/walls already marked as blocked)
                    blocked_match = re.search(r'\(blocked\s+(loc_\d+_\d+)\)', pred)
                    if blocked_match:
                        loc = blocked_match.group(1)
                        obstacle_locations.add(loc)  # This is an obstacle/wall
                        if loc not in location_to_obj_name:
                            location_to_obj_name[loc] = "obstacle"
                
                # Only enforce blocking for obstacles/walls, NOT for stores
                # Stores should remain accessible so the planner can target them
                for loc in obstacle_locations:
                    # CRITICAL SAFETY CHECK: If this location is also a store, skip blocking
                    # (This should not happen if state_manager is used correctly, but defensive programming)
                    if loc in store_locations:
                        store_name = location_to_obj_name.get(loc, "unknown")
                        print(f"[PDDL_PATCH] ⚠️  CONFLICT DETECTED: Location {loc} is both store ({store_name}) and obstacle!")
                        print(f"[PDDL_PATCH] ⚠️  PRIORITY: Store takes precedence - skipping blocking (stores must be accessible)")
                        continue
                    
                    blocked_pred = f"(blocked {loc})"
                    obj_name = location_to_obj_name.get(loc, "obstacle")
                    
                    # Step 1: Add blocked predicate to dynamic_predicates if not already there
                    if blocked_pred not in dynamic_predicates:
                        dynamic_predicates.append(blocked_pred)
                        print(f"[PDDL_PATCH] ✅ Enforced physics for {obj_name} at {loc}: +blocked")
                    
                    # Step 2: Remove conflicting (clear loc_X_Y) from init_content
                    clear_pred_pattern = rf'\(clear\s+{re.escape(loc)}\)'
                    if re.search(clear_pred_pattern, init_content):
                        init_content = re.sub(clear_pred_pattern + r'\s*', '', init_content)
                        print(f"[PDDL_PATCH] ✅ Removed conflicting (clear {loc}) predicate")
                
                # Ensure stores are NOT blocked and remain clear
                for loc in store_locations:
                    # Remove any blocking predicates for stores (they should be accessible)
                    blocked_pred = f"(blocked {loc})"
                    if blocked_pred in dynamic_predicates:
                        dynamic_predicates.remove(blocked_pred)
                        print(f"[PDDL_PATCH] ✅ Removed blocking from store at {loc} (stores must be accessible)")
                    
                    # Ensure (clear loc_X_Y) exists for stores so planner can target them
                    clear_pred = f"(clear {loc})"
                    clear_pred_pattern = rf'\(clear\s+{re.escape(loc)}\)'
                    if not re.search(clear_pred_pattern, init_content):
                        # Add clear predicate for store location
                        init_content = init_content.rstrip() + f"\n    {clear_pred}"
                        print(f"[PDDL_PATCH] ✅ Ensured store at {loc} is marked as clear (accessible)")
                
                injection = "\n    ".join(dynamic_predicates)
                if init_content.strip():
                    init_content = init_content.rstrip() + "\n    " + injection
                else:
                    init_content = "    " + injection

            # 6. Reconstruct the file with properly formatted (:init ... ) block
            before_init = content[:init_start]
            after_init = content[init_end + 1:]  # +1 to skip the closing )
            
            new_content = before_init + "(:init\n" + init_content + "  )" + after_init

            # 7. Write the reconstructed file
            with open(self.pddl_file_path, 'w') as f:
                f.write(new_content)

            print(f"[PDDL] Successfully injected {len(dynamic_predicates)} dynamic predicates into :init")
            
            # 8. Verify the injection worked and file structure is valid
            with open(self.pddl_file_path, 'r') as f:
                final_content = f.read()
            
            # Check that (:goal still exists and structure is intact
            if '(:goal' not in final_content:
                print(f"[PDDL] ERROR: (:goal section missing after injection!")
                return False
            
            # Verify predicates were added
            predicates_found = sum(1 for pred in dynamic_predicates if pred in final_content)
            if predicates_found == len(dynamic_predicates):
                print(f"[PDDL] Verification: All {len(dynamic_predicates)} predicates found in file")
            else:
                print(f"[PDDL] WARNING: Only {predicates_found}/{len(dynamic_predicates)} predicates found")
            
            return True

        except Exception as e:
            print(f"[PDDL] Error injecting dynamic state: {e}")
            import traceback
            traceback.print_exc()
            return False

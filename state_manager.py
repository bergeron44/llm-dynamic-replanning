"""
State Manager - Tracks the robot's beliefs about the world state in memory.
Only flushes to PDDL file when needed (before replanning).
"""


def scale_price_to_int(raw_price) -> int:
    """
    Convert fractional price to integer for PDDL compatibility.
    
    Fast Downward's lmcut heuristic only supports integer costs.
    We scale prices by 10 (e.g., 3.5 becomes 35, 4.0 becomes 40).
    
    Args:
        raw_price: Price as float (e.g., 3.5) or string (e.g., "3.5")
    
    Returns:
        Integer price scaled by 10 (e.g., 35 for 3.5)
    
    Examples:
        scale_price_to_int(3.5) -> 35
        scale_price_to_int(4.0) -> 40
        scale_price_to_int("2.99") -> 29
    """
    try:
        return int(float(raw_price) * 10)
    except (ValueError, TypeError):
        # If conversion fails, return 0
        return 0


class StateManager:
    """
    Manages the robot's belief state about the world.
    Tracks dynamic facts in memory, only syncs to PDDL when necessary.
    """

    def __init__(self):
        # Core state tracking
        self.agent_pos = (1, 1)
        self.discovered_objects = {}  # name -> {'pos': (x,y), 'type': 'store', 'properties': {...}}

        # Generic dynamic facts (for future extensibility)
        self.dynamic_facts = set()  # e.g., "(door-open d1)", "(has agent key1)"

        # Static facts that are set once (walls, connections)
        self.static_facts = set()

    def update_agent_pos(self, pos):
        """Update the agent's current position in belief state."""
        self.agent_pos = pos

    def add_discovery(self, name, pos, obj_type='store', **properties):
        """Add a newly discovered object to the belief state."""
        self.discovered_objects[name] = {
            'pos': pos,
            'type': obj_type,
            'properties': properties
        }

        # Handle object registration based on type
        if obj_type == 'store':
            # For stores: register as object first, then add properties
            # Note: We assume the patcher has access to register objects
            # For now, we just add the facts - the objects should be pre-registered
            self.dynamic_facts.add(f"(at_store {name} loc_{pos[0]}_{pos[1]})")
            # CRITICAL: Always add (selling {name} milk) for stores - required for buy action!
            # The planner needs this predicate to know the store sells milk, otherwise
            # the buy action precondition fails and the planner won't route to the store.
            # We add this regardless of whether 'price' exists in properties.
            self.dynamic_facts.add(f"(selling {name} milk)")
            
            # NOTE: item-price predicates are currently not added to PDDL.
            # If prices need to be added to PDDL in the future, use:
            #   scaled_price = scale_price_to_int(properties.get('price', 4.0))
            #   self.dynamic_facts.add(f"(= (item-price milk {name}) {scaled_price})")
            # This ensures integer values (3.5 -> 35, 4.0 -> 40) for Fast Downward compatibility.
            # Price information is currently handled in Python logic only.
        elif obj_type in ['obstacle', 'wall']:
            # For obstacles/walls: only add blocking predicate, no object registration needed
            self.dynamic_facts.add(f"(blocked loc_{pos[0]}_{pos[1]})")

    def add_generic_fact(self, fact):
        """Add a generic dynamic fact (for future proofing)."""
        self.dynamic_facts.add(fact)

    def remove_fact(self, fact_pattern):
        """Remove facts matching a pattern."""
        self.dynamic_facts = {f for f in self.dynamic_facts if fact_pattern not in f}

    def get_current_state_predicates(self):
        """Returns a list of PDDL strings representing current belief state."""
        preds = []

        # 1. Agent Position (always current)
        preds.append(f"(at_agent agent loc_{self.agent_pos[0]}_{self.agent_pos[1]})")

        # 2. Static facts (walls, connections - if any)
        preds.extend(list(self.static_facts))

        # 3. Dynamic facts (discovered objects, doors, inventory, etc.)
        preds.extend(list(self.dynamic_facts))

        return preds

    def reset(self, start_pos=(1, 1)):
        """Reset the state manager (for new episodes)."""
        self.agent_pos = start_pos
        self.discovered_objects = {}
        self.dynamic_facts = set()
        # Keep static_facts as they don't change between episodes

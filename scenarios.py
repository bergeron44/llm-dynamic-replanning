"""
Predefined Scenarios for Comparative Experiment Framework
Defines 4 distinct scenarios to test different cognitive architectures
"""

SCENARIOS = {
    "SCENARIO_1": {
        "name": "Irrelevant Object",
        "description": "Object is 'Old Tree in Jerusalem Forest' (Ancient tree, not a store)",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "surprise_object": {
            "name": "old_tree_jerusalem_forest",
            "position": (3, 2),  # Near path for reliable observation
            "true_price": None,  # Not a store, no price
            "type": "nature",
            "color": "green"
        }
    },

    "SCENARIO_2": {
        "name": "Relevant but Unuseful",
        "description": "Object is 'Moshe's Butcher Shop in Rehovot' (Butcher shop, sells meat not milk)",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "surprise_object": {
            "name": "moshe_butcher_rehovot",  # Real butcher shop
            "position": (2, 4),  # Near path for reliable observation
            "true_price": None,  # Butcher shop, doesn't sell milk
            "type": "butcher_shop",
            "color": "red"
        }
    },

    "SCENARIO_3": {
        "name": "Useful but Far",
        "description": "Object is 'Rami Levy Jerusalem' (Cheap supermarket) at central position",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "surprise_object": {
            "name": "rami_levy_jerusalem",
            "position": (10, 6),  # Visible from main path but still a detour
            "true_price": 2.5,    # Cheap price
            "type": "supermarket",
            "color": "red"
        }
    },

    "SCENARIO_4": {
        "name": "The Sweet Spot",
        "description": "Object is 'Mega Bulldog Tel Aviv' (Reasonable price) and close (2 steps)",
        "start_pos": (1, 1),
        "victory_pos": (18, 18),
        "surprise_object": {
            "name": "mega_bulldog_tlv",
            "position": (3, 3),   # Close position, minimal detour
            "true_price": 3.5,    # Medium price
            "type": "supermarket",
            "color": "green"
        }
    },

    "SCENARIO_5": {
        "name": "The Expensive Trap",
        "description": "Object is 'AM:PM Express' (Very expensive convenience store) but close (5 steps) - should be ignored",
        "start_pos": (1, 1),
        "victory_pos": (10, 10),  # Closer victory to make the trap more tempting
        "surprise_object": {
            "name": "am_pm_express",
            "position": (6, 4),     # Close but not TOO close
            "true_price": 12.0,     # Very expensive! (3x the victory price)
            "type": "convenience_store",
            "color": "yellow"
        }
    }
}

def get_scenario(scenario_id):
    """
    Retrieve a specific scenario by ID

    Args:
        scenario_id: String like "SCENARIO_1", "SCENARIO_2", etc.

    Returns:
        Dict containing scenario configuration
    """
    return SCENARIOS.get(scenario_id)

def list_scenarios():
    """
    Return list of all available scenario IDs
    """
    return list(SCENARIOS.keys())

def get_scenario_summary(scenario_id):
    """
    Get a human-readable summary of a scenario
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        return f"Scenario {scenario_id} not found"

    obj = scenario["surprise_object"]
    price_info = f" (Price: ${obj['true_price']})" if obj['true_price'] else " (No milk sold)"

    return f"{scenario['name']}: {scenario['description']}{price_info}"

"""
Custom MiniGrid Environments for LLM-Driven Dynamic Replanning Research
Supports both demo (8x8) and research (50x50) configurations
"""

import gymnasium as gym
from minigrid.core.grid import Grid
from minigrid.core.world_object import Ball, Wall
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.mission import MissionSpace
import numpy as np
import collections
import random
import os
from stores_database import STORES_DATABASE, get_random_stores

class SupermarketEnv(MiniGridEnv):
    """
    Demo 8x8 supermarket environment - LEGACY
    Kept for backward compatibility and small-scale testing
    """

    def __init__(self, width=8, height=8, max_steps=100,
                 victory_price=4.0, rami_levy_price=2.5, rami_levy_pos=(2, 6),
                 render_mode='rgb_array'):
        mission_space = MissionSpace(mission_func=lambda: "Navigate the supermarket world and complete objectives")

        # Call parent constructor with render_mode
        super().__init__(
            width=width,
            height=height,
            max_steps=max_steps,
            mission_space=mission_space,
            render_mode=render_mode,
            see_through_walls=True,  # Can see through walls for easier navigation
            agent_view_size=5  # Limited view to make discovery interesting
        )

        # Store configurable parameters
        self.victory_price = victory_price
        self.rami_levy_price = rami_levy_price
        self.rami_levy_pos = rami_levy_pos

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        # Clear a plus sign for navigation
        self.grid.wall_rect(0, 0, width, height)
        for i in range(1, height-1):
            for j in range(1, width-1):
                self.grid.set(i, j, None)

        # Place stores as colored balls
        # Victory (blue ball) at fixed position (5,5)
        from minigrid.core.world_object import Ball
        victory_ball = Ball('blue')
        victory_ball.name = 'victory'  # CRITICAL FIX
        victory_ball.price = self.victory_price
        self.grid.set(5, 5, victory_ball)

        # Rami Levy (red ball) at configurable position - this is the "hidden" store
        rami_levy_ball = Ball('red')
        rami_levy_ball.name = 'rami_levy'  # CRITICAL FIX
        rami_levy_ball.price = self.rami_levy_price
        self.grid.set(2, 6, rami_levy_ball)  # Fixed position for Rami Levy

        # Place agent at home (1,1)
        self.agent_pos = (1, 1)
        self.agent_dir = 0  # Facing right

        self.mission = "Navigate to victory and buy milk"

    def reset(self, **kwargs):
        obs = super().reset(**kwargs)
        return obs, {}

    def get_semantic_observation(self) -> list:
        """
        Convert MiniGrid observation to semantic entity list.
        Used by the perception system to detect stores.
        """
        semantic_objects = []
        agent_x, agent_y = self.agent_pos

        # Scan grid for objects within sensor range
        for x in range(max(0, agent_x - 3), min(self.width, agent_x + 4)):
            for y in range(max(0, agent_y - 3), min(self.height, agent_y + 4)):
                cell = self.grid.get(x, y)
                if cell and hasattr(cell, 'color'):
                    # Calculate distances
                    manhattan_dist = abs(agent_x - x) + abs(agent_y - y)
                    air_distance = ((agent_x - x) ** 2 + (agent_y - y) ** 2) ** 0.5

                    # Identify object
                    obj_name = getattr(cell, 'name', 'unknown_store')

                    semantic_objects.append({
                        'type': 'store',
                        'name': obj_name,
                        'color': cell.color,
                        'position': (x, y),
                        'manhattan_distance': manhattan_dist,
                        'air_distance': air_distance,
                        'price': getattr(cell, 'price', 4.0),
                        'price_level': 'cheap' if getattr(cell, 'price', 4.0) < 3 else 'expensive',
                    })

        return semantic_objects

class RandomizedMazeEnv(MiniGridEnv):
    """
    RESEARCH-GRADE 50x50 Randomized Maze Environment
    Implements procedural generation with guaranteed connectivity
    """

    def __init__(self, width=20, height=20, wall_density=0.2, sensor_radius=5, render_mode='rgb_array', scenario=None):
        """
        Initialize the randomized maze environment.

        Args:
            width, height: Maze dimensions (default 50x50 for research)
            wall_density: Percentage of walls (0.15-0.20 recommended)
            sensor_radius: Detection range in Manhattan distance
            render_mode: Rendering mode for gymnasium compatibility
            scenario: Optional scenario dict to override random store placement
        """
        self.wall_density = wall_density
        self.sensor_radius = sensor_radius
        self.scenario = scenario

        # Mission space (required by MiniGrid)
        mission_space = MissionSpace(mission_func=lambda: "Navigate the randomized maze and complete objectives")

        # Call parent constructor
        super().__init__(
            width=width,
            height=height,
            max_steps=1000,  # More steps for large maze
            mission_space=mission_space,
            render_mode=render_mode,
            see_through_walls=False,  # Walls block vision in research mode
            agent_view_size=5
        )

    def _gen_grid(self, width, height):
        """Generate a randomized maze with procedural walls and guaranteed connectivity."""
        self.grid = Grid(width, height)

        # Initialize position variables for stores
        self.store_positions = {}

        # Set seed based on USE_FIXED_SEED environment variable
        use_fixed_seed = os.environ.get('USE_FIXED_SEED', 'true').lower() == 'true'
        seed_env = os.environ.get('SEED')
        
        if use_fixed_seed and seed_env:
            # Use fixed seed for reproducible experiments
            try:
                seed = int(seed_env)
                random.seed(seed)
                np.random.seed(seed)
                print(f"[ENV_SEED] Using fixed SEED: {seed} for reproducible maze")
            except ValueError:
                print(f"[ENV_SEED] Invalid SEED value: {seed_env} - using random")
                pass  # Fall through to random
        elif not use_fixed_seed:
            # Use random seed (no seed set)
            print("[ENV_SEED] Using random seed (USE_FIXED_SEED=false)")
            # Don't set seed - let Python use system random
        else:
            # use_fixed_seed=True but no SEED provided - use random
            print("[ENV_SEED] USE_FIXED_SEED=true but no SEED provided - using random")

        # 1. Initialize with walls everywhere (except borders are kept)
        for x in range(width):
            for y in range(height):
                if (x == 0 or x == width-1 or y == 0 or y == height-1):
                    self.grid.set(x, y, Wall())  # Border walls
                else:
                    # Clear center area initially
                    self.grid.set(x, y, None)

        # 1.5. Ensure start position is clear (before placing any objects)
        self.grid.set(1, 1, None)

        # 2. Place random walls ensuring connectivity
        wall_count = 0
        max_walls = int(width * height * self.wall_density)

        attempts = 0
        while wall_count < max_walls and attempts < 2000:
            x = random.randint(1, width-2)
            y = random.randint(1, height-2)

            # STRICTLY FORBID walls in the top-left 4x4 safe zone for debugging
            if x < 4 and y < 4:
                attempts += 1
                continue

            # Don't place walls on start/goal areas or existing walls
            if ((x, y) == (1, 1) or  # Agent start
                (x, y) == (width-3, height-3) or  # Victory area
                self.grid.get(x, y) is not None):  # Already occupied
                attempts += 1
                continue

            # Try placing wall
            self.grid.set(x, y, Wall())
            wall_count += 1

            # Check if maze is still connected (Victory is still reachable)
            if not self._is_path_to_victory():
                # Remove wall if it disconnects maze
                self.grid.set(x, y, None)
                wall_count -= 1

            attempts += 1

        # 3. Place Agent at start
        self.agent_pos = (1, 1)
        self.agent_dir = 0

        # 4. Place Victory (Known Goal) - Use scenario position if provided
        if self.scenario:
            victory_pos = self.scenario['victory_pos']
        else:
            victory_pos = (width - 3, height - 3)

        victory = Ball('blue')
        victory.name = 'victory'
        victory.price = 4.0
        self.grid.set(*victory_pos, victory)

        # 5. Place Surprise Object (Scenario-based or default Rami Levy)
        if self.scenario:
            # Use scenario-defined surprise object
            surprise_obj = self.scenario['surprise_object']
            obj_pos = surprise_obj['position']

            # Choose color based on object type
            if surprise_obj['type'] == 'supermarket':
                color = 'red'  # Like Rami Levy
                price = surprise_obj.get('true_price', 2.5)
            elif surprise_obj['type'] == 'luxury_store':
                color = 'purple'  # Luxury
                price = surprise_obj.get('true_price', 0)  # Doesn't sell milk
            elif surprise_obj['type'] == 'nature':
                color = 'green'  # Natural object
                price = surprise_obj.get('true_price', 0)  # Not a store
            else:
                color = 'yellow'  # Default
                price = surprise_obj.get('true_price', 0)

            surprise_ball = Ball(color)
            surprise_ball.name = surprise_obj['name']
            if price is not None and price > 0:
                surprise_ball.price = price
            self.grid.set(*obj_pos, surprise_ball)

        if not self.scenario:
            # Default Rami Levy placement (original logic)
            attempts = 0
            rami_pos = None

            # Calculate points along the diagonal path with jitter
            path_points = []
            steps = min(width, height) // 3  # Divide path into segments
            for i in range(1, steps):
                # Interpolate along diagonal with some randomness
                base_x = 1 + (victory_pos[0] - 1) * i // steps
                base_y = 1 + (victory_pos[1] - 1) * i // steps

                # Add random jitter (±2 in each direction)
                jitter_x = random.randint(-2, 2)
                jitter_y = random.randint(-2, 2)

                candidate_x = max(1, min(width-2, base_x + jitter_x))
                candidate_y = max(1, min(height-2, base_y + jitter_y))

                path_points.append((candidate_x, candidate_y))

            # Try to place at one of the path points
            random.shuffle(path_points)  # Randomize order
            for rx, ry in path_points:
                if self.grid.get(rx, ry) is None:
                    rami = Ball('red')
                    rami.name = 'rami_levy'
                    rami.price = 2.5
                    self.grid.set(rx, ry, rami)
                    rami_pos = (rx, ry)
                    break

            # Fallback: random placement if path points don't work
            if rami_pos is None:
                while attempts < 20:
                    rx = random.randint(2, width-3)
                    ry = random.randint(2, height-3)

                    if ((rx, ry) != (1, 1) and
                        abs(rx - victory_pos[0]) > 3 and abs(ry - victory_pos[1]) > 3 and
                        self.grid.get(rx, ry) is None):

                        rami = Ball('red')
                        rami.name = 'rami_levy'
                        rami.price = 2.5
                        self.grid.set(rx, ry, rami)
                        rami_pos = (rx, ry)
                        break
                    attempts += 1

            # Ensure Rami Levy was placed
            if rami_pos is None:
                # Fallback placement
                rami_pos = (width//2, height//2)
                rami = Ball('red')
                rami.name = 'rami_levy'
                rami.price = 2.5
                self.grid.set(*rami_pos, rami)

        # 6. Place random stores from database (16 stores total)
        # Allow scenario-only runs to disable random store noise.
        scenario_only = os.environ.get('SCENARIO_ONLY', 'false').lower() == 'true'
        if not scenario_only:
            self._place_random_stores_from_database(victory_pos)
        else:
            print("[ENV] SCENARIO_ONLY=true - skipping random stores")
        # Close the scenario check - skip random stores when using scenarios

        self.mission = "Navigate maze, discover stores, buy milk efficiently"

    def _place_random_stores_from_database(self, victory_pos):
        """
        Place random stores from the database, ensuring scenario compatibility
        """
        width, height = self.grid.width, self.grid.height

        # Handle scenario-specific store first (if exists)
        if self.scenario:
            scenario_obj = self.scenario['surprise_object']
            store_ball = Ball(scenario_obj.get('color', 'green'))
            store_ball.name = scenario_obj['name']
            if scenario_obj.get('true_price') and scenario_obj['true_price'] > 0:
                store_ball.price = scenario_obj['true_price']
            # Override position for scenario objects
            pos = scenario_obj['position']
            self.grid.set(pos[0], pos[1], store_ball)
            self.store_positions[scenario_obj['name']] = pos

        # Always place 15 additional random stores (total 16 including scenario object)
        placed_stores = 0

        # Get all available stores, but exclude the scenario object if it exists
        all_store_names = list(STORES_DATABASE.keys())
        if self.scenario:
            scenario_name = self.scenario['surprise_object']['name']
            if scenario_name in all_store_names:
                all_store_names.remove(scenario_name)

        # Select 15 random stores (or fewer if not enough available)
        num_to_select = min(15, len(all_store_names))
        selected_stores = random.sample(all_store_names, num_to_select)

        for store_name in selected_stores:
            store_data = STORES_DATABASE[store_name]

            # Try to place the store
            attempts = 0
            while attempts < 50 and placed_stores < 15:
                # Random position
                x = random.randint(2, width-3)
                y = random.randint(2, height-3)

                # Check if position is valid
                if (self._is_valid_store_position((x, y), victory_pos) and
                    self.grid.get(x, y) is None):

                    # Create the store ball
                    store_ball = Ball(store_data['color'])
                    store_ball.name = store_name
                    if store_data.get('price_estimate', 0) > 0:
                        store_ball.price = store_data['price_estimate']

                    # Place it on the grid
                    self.grid.set(x, y, store_ball)
                    self.store_positions[store_name] = (x, y)
                    placed_stores += 1
                    break

                attempts += 1

        print(f"DEBUG: Placed {placed_stores} additional stores")
        if self.scenario:
            print(f"DEBUG: Scenario object: {self.scenario['surprise_object']['name']} at {self.scenario['surprise_object']['position']}")
        print(f"DEBUG: Total objects in store_positions: {len(self.store_positions)}")

    def _is_valid_store_position(self, pos, victory_pos):
        """
        Check if a position is valid for placing a store
        """
        x, y = pos
        vx, vy = victory_pos

        # Basic checks
        if (x, y) == (1, 1):  # Not on start
            return False
        if abs(x - vx) <= 4 and abs(y - vy) <= 4:  # Not too close to victory
            return False

        # Check distance from other stores (minimum distance 2)
        for other_pos in self.store_positions.values():
            if abs(x - other_pos[0]) <= 2 and abs(y - other_pos[1]) <= 2:
                return False

        return True

    def _is_path_to_victory(self):
        """Check if there's a path from start to Victory."""
        start = (1, 1)
        goal = (self.width - 3, self.height - 3)
        return self.calculate_walking_distance(start, goal) < 9999

    def calculate_walking_distance(self, start_pos, end_pos):
        """
        Calculate true walking distance using BFS, considering walls.
        Returns distance or 9999 if unreachable.
        """
        if start_pos == end_pos:
            return 0

        queue = collections.deque([(start_pos, 0)])
        visited = {start_pos}

        while queue:
            (cx, cy), dist = queue.popleft()
            if (cx, cy) == end_pos:
                return dist

            # Try all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy

                # Bounds check
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    cell = self.grid.get(nx, ny)
                    # Walkable if empty or contains a store (Ball)
                    if (cell is None or isinstance(cell, Ball)) and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), dist + 1))

        return 9999  # Unreachable

    def get_semantic_observation(self):
        """
        Get semantic observations within sensor range.
        Uses Manhattan distance for sensor detection.
        """
        semantic_objects = []
        agent_x, agent_y = self.agent_pos

        # Debug: print current position and sensor range
        # print(f"DEBUG OBS: Agent at ({agent_x},{agent_y}), sensor radius {self.sensor_radius}")

        # Scan grid for objects within sensor range
        for x in range(max(0, agent_x - self.sensor_radius),
                      min(self.width, agent_x + self.sensor_radius + 1)):
            for y in range(max(0, agent_y - self.sensor_radius),
                          min(self.height, agent_y + self.sensor_radius + 1)):

                cell = self.grid.get(x, y)
                if cell and isinstance(cell, Ball):  # Only stores (Balls)
                    # Calculate distances
                    manhattan_dist = abs(agent_x - x) + abs(agent_y - y)
                    air_distance = ((agent_x - x) ** 2 + (agent_y - y) ** 2) ** 0.5
                    walking_distance = self.calculate_walking_distance((agent_x, agent_y), (x, y))

                    # Get object info
                    obj_name = getattr(cell, 'name', 'unknown_store')
                    price = getattr(cell, 'price', 4.0)

                    # Debug: print found objects
                    # print(f"DEBUG OBS: Found {obj_name} at ({x},{y}), distance {manhattan_dist}")

                    semantic_objects.append({
                        'type': 'store',
                        'name': obj_name,
                        'color': cell.color,
                        'position': (x, y),
                        'manhattan_distance': manhattan_dist,
                        'air_distance': air_distance,
                        'walking_distance': walking_distance,
                        'price': price,
                        'price_level': 'cheap' if price < 3 else 'expensive',
                    })

        return semantic_objects

    def reset(self, **kwargs):
        """Reset environment and return observation."""
        obs = super().reset(**kwargs)
        return obs, {}

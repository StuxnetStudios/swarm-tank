"""
Bot role definitions and configuration
"""
from typing import Tuple

# Type aliases for better type safety
ColorTuple = Tuple[int, int, int]

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
LIME = (50, 205, 50)
MAGENTA = (255, 0, 255)


class RoleData:
    """Type definition for bot role data"""
    def __init__(self, 
                 color: ColorTuple,
                 max_speed: float,
                 max_force: float,
                 description: str,
                 **kwargs: float | bool | int):
        self.color = color
        self.max_speed = max_speed
        self.max_force = max_force
        self.description = description
        # Store additional role-specific attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key: str, default: float | bool | int = 0) -> float | bool | int:
        """Get attribute value with default fallback"""
        return getattr(self, key, default)


# Bot roles and their colors
BOT_ROLES = {
    'scout': RoleData(
        color=CYAN,
        max_speed=4.0,  # Nerfed from 5.5
        max_force=0.12, # Nerfed from 0.18
        description='Fast scouts - find food and alert others',
        food_seek_weight=2.0,  # Nerfed from 3.5
        shout_range=50  # Nerfed from 80
    ),
    'hunter': RoleData(
        color=PURPLE,
        max_speed=2.5,
        max_force=0.12,
        description='Hunters - protect swarm and taunt enemies',
        predator_avoid_weight=6.0,
        can_attack=True,
        attack_range=25,  # Increased from 15 to 25
        attack_damage=20,
        taunt_range=60,
        taunt_force=0.8
    ),
    'drone': RoleData(
        color=BLUE,
        max_speed=3.0,
        max_force=0.1,
        description='Drones - maintain formation',
        cohesion_weight=2.0
    ),
    'harvester': RoleData(
        color=GREEN,
        max_speed=3.2,
        max_force=0.11,
        description='Harvesters - collect & reproduce',
        food_seek_weight=4.0,
        food_detection_range=120,
        burst_speed_multiplier=1.8,
        priority_food_range=60,
        reproduction_chance=0.4  # Increased from 0.25 to 0.4 (40% chance)
    ),
    'leader': RoleData(
        color=YELLOW,
        max_speed=3.5,
        max_force=0.13,
        description='Leaders - maintain formation',
        cohesion_weight=1.5
    ),
    'gatherer': RoleData(
        color=(0, 120, 255),  # Blue accent for gatherer
        max_speed=3.0,
        max_force=0.11,
        description='Gatherers - collect food and deliver to home',
        food_seek_weight=4.0,
        food_detection_range=120,
        burst_speed_multiplier=1.8,
        priority_food_range=60,
        reproduction_chance=0.4  # Match harvester
    ),
    'miner': RoleData(
        color=(180, 120, 60),  # Brownish for miner
        max_speed=2.8,
        max_force=0.10,
        description='Miners - collect ore from rocks and deliver to home',
        ore_seek_weight=4.0,
        ore_detection_range=120,
        burst_speed_multiplier=1.7,
        priority_ore_range=60,
        reproduction_chance=0.3  # Slightly less than gatherer
    )
}

# Role distribution weights (higher = more common)
ROLE_WEIGHTS = {
    'drone': 5,         # Changed from 30 to 5 (5%)
    'gatherer': 25,    # Added gatherer at 25 (25%)
    'scout': 20,       # Same
    'harvester': 30,   # Same
    'hunter': 15,      # Same
    'leader': 5,        # Same
    'miner': 20        # Add miner at 20 (20%)
}

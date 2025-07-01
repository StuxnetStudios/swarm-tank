from typing import Any

"""
Utility functions for PowerUp defensive initialization and related helpers.
"""

def defensive_init_powerup(power_up: Any) -> object:
    if not hasattr(power_up, 'color') or not isinstance(power_up.color, tuple) or len(power_up.color) != 3:
        power_up.color = (255, 255, 255)
    if not hasattr(power_up, 'health_value') or not isinstance(power_up.health_value, (int, float)):
        if hasattr(power_up, 'energy_value') and isinstance(power_up.energy_value, (int, float)):
            power_up.health_value = power_up.energy_value
        else:
            power_up.health_value = 0
    if not hasattr(power_up, 'power_type') or not isinstance(power_up.power_type, str):
        power_up.power_type = 'health'
    return power_up

# Optionally, add more PowerUp-related helpers here.

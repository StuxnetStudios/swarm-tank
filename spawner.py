"""
Spawner utilities for the Swarm Tank game.
Handles spawning of food, power-ups, bots, and predators.
"""
import random
from entities import Food, PowerUp, Predator
from swarm_bot import SwarmBot
from rock import Rock
from powerup_utils import defensive_init_powerup
from typing import Optional

# Constants (should match those in swarm_tank.py)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800


def spawn_food(n: int = 1, food_list: Optional[list] = None) -> list:
    """Spawn n food items and add to food_list if provided."""
    foods = []
    for _ in range(n):
        x = random.uniform(20, SCREEN_WIDTH - 20)
        y = random.uniform(20, SCREEN_HEIGHT - 20)
        food = Food(x, y)
        foods.append(food)
        if food_list is not None:
            food_list.append(food)
    return foods


def spawn_powerup(power_type: Optional[str] = None, powerup_list: Optional[list] = None) -> PowerUp:
    """Spawn a power-up of given type (random if None) and add to powerup_list if provided."""
    x = random.uniform(20, SCREEN_WIDTH - 20)
    y = random.uniform(20, SCREEN_HEIGHT - 20)
    if power_type is None:
        power_type = random.choice(['energy', 'speed', 'damage'])
    power_up = PowerUp(x, y, power_type)
    defensive_init_powerup(power_up)
    if powerup_list is not None:
        powerup_list.append(power_up)
    return power_up


def spawn_bot(role: Optional[str] = None, bot_list: Optional[list] = None) -> SwarmBot:
    """Spawn a SwarmBot with optional role and add to bot_list if provided."""
    x = random.uniform(50, SCREEN_WIDTH - 50)
    y = random.uniform(50, SCREEN_HEIGHT - 50)
    bot = SwarmBot(x, y, role, SCREEN_WIDTH, SCREEN_HEIGHT)
    if bot_list is not None:
        bot_list.append(bot)
    return bot


def spawn_predator(predator_list: Optional[list] = None) -> Predator:
    """Spawn a Predator and add to predator_list if provided."""
    x = random.uniform(50, SCREEN_WIDTH - 50)
    y = random.uniform(50, SCREEN_HEIGHT - 50)
    predator = Predator(x, y, SCREEN_WIDTH, SCREEN_HEIGHT)
    if predator_list is not None:
        predator_list.append(predator)
    return predator


def spawn_rock(rock_list: Optional[list] = None) -> Rock:
    x = random.uniform(40, SCREEN_WIDTH - 40)
    y = random.uniform(40, SCREEN_HEIGHT - 40)
    rock = Rock(x, y)
    if rock_list is not None:
        rock_list.append(rock)
    return rock

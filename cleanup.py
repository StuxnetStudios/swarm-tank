"""
Cleanup and respawn logic for swarm simulation
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from swarm_tank import Game
    from swarm_bot import SwarmBot
    from entities import Predator

from entities import Food, Predator
from swarm_bot import SwarmBot
from predator_food import PredatorFood

def remove_dead_bots(game: 'Game', bots_to_remove: List['SwarmBot']) -> None:
    """Remove dead bots (energy <= 0) from the swarm, handle leader death event, and last harvester event."""
    # Check for dead leaders and spawn warriors if needed BEFORE removing dead bots
    dead_leaders = [bot for bot in bots_to_remove if bot.role == 'leader']
    if dead_leaders:
        print(f"WAR! event triggered for {len(dead_leaders)} leader(s): {[f'({bot.position.x:.1f},{bot.position.y:.1f})' for bot in dead_leaders]}")
        game.screen_flash_timer = 90
        game.leader_down_message_timer = 90
        for dead_leader in dead_leaders:
            for _ in range(10):
                new_warrior = SwarmBot(dead_leader.position.x, dead_leader.position.y, 'warrior', game.screen.get_width(), game.screen.get_height())
                game.swarm_bots.append(new_warrior)
    # Remove all dead bots
    for bot in bots_to_remove:
        if bot in game.swarm_bots:
            game.swarm_bots.remove(bot)
    # Check for last harvester death
    if not any(bot.role == 'harvester' for bot in game.swarm_bots):
        if not hasattr(game, 'no_breeders_message_timer') or game.no_breeders_message_timer == 0:
            game.no_breeders_message_timer = 120

def handle_dead_predators(game: 'Game') -> None:
    """Remove dead predators, drop food, and respawn as needed."""
    dead_predators = [pred for pred in game.predators if pred.health <= 0]
    for dead_predator in dead_predators:
        if dead_predator in game.predators:
            game.predators.remove(dead_predator)
        # Drop ONLY PredatorFood where predator died (3-5 items)
        food_drops = random.randint(3, 5)
        for _ in range(food_drops):
            offset_x = random.uniform(-30, 30)
            offset_y = random.uniform(-30, 30)
            food_x = max(20, min(game.screen.get_width() - 20, dead_predator.position.x + offset_x))
            food_y = max(20, min(game.screen.get_height() - 20, dead_predator.position.y + offset_y))
            game.food_list.append(PredatorFood(food_x, food_y))
        # Respawn a new predator after some time (25% chance per dead predator)
        if random.random() < 0.25:
            x = random.uniform(50, game.screen.get_width() - 50)
            y = random.uniform(50, game.screen.get_height() - 50)
            game.predators.append(Predator(x, y, game.screen.get_width(), game.screen.get_height()))
    # If all predators are dead, spawn 3 new ones
    if len(game.predators) == 0 and len(dead_predators) > 0:
        for _ in range(3):
            x = random.uniform(50, game.screen.get_width() - 50)
            y = random.uniform(50, game.screen.get_height() - 50)
            game.predators.append(Predator(x, y, game.screen.get_width(), game.screen.get_height()))

"""
Tick-based evaluation logic for Swarm Tank.
"""

from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from swarm_tank import Game

def tick_eval(game: 'Game') -> None:
    """Perform tick-based evaluation. Called every TICK_FRAMES frames from the main game loop."""
    # Increment tick count
    game.tick_count += 1
    print(f"[TICK] Frame: {game.frame_count}, Tick: {game.tick_count}")
    
    # Update Home resources
    home = game.home
    if getattr(home, 'food_collected', 0) > 100:
        home.food_collected -= 50
        game.ration += 1
    if getattr(home, 'ore_collected', 0) > 50:
        home.ore_collected -= 50
        game.material += 1
    if getattr(home, 'craft_points', 0) > 50:
        home.craft_points -= 50
        game.workunit += 1
    
    # Replenish ore in rocks
    for obstacle in game.obstacles:
        if hasattr(obstacle, 'ore_amount') and obstacle.ore_amount < 30:
            obstacle.ore_amount += random.randint(1, 3)
    
    # Update global stats directly in the Game instance
    game.stats = {
        "tick_count": game.tick_count,
        "ration": game.ration,
        "material": game.material,
        "craftsmanship": game.workunit,
        "miners": sum(1 for b in game.swarm_bots if getattr(b, 'role', None) == 'miner'),
    }
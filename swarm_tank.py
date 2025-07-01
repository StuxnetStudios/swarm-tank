"""
Main game class and entry point for the swarm simulation
"""
from __future__ import annotations
import pygame
import random
from typing import List
import math

from roles import BLACK
from entities import Food, PowerUp, Predator
from swarm_bot import SwarmBot
from rock import Rock  # Updated import to use rock.py
from cleanup import handle_dead_predators, remove_dead_bots
from ui import GameUI
from home import Home  # Import Home class
from spawner import spawn_food, spawn_powerup, spawn_bot
from tick import tick_eval


# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
NORMAL_VISION_RANGE = 120  # Example normal vision range for bots
HUNTER_VISION_RANGE = NORMAL_VISION_RANGE * 2
TICK_FRAMES = 300  # One tick is 300 frames


class Game:
    """Main game class"""
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Swarm Tank")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.ui = GameUI(self.font)
        
        # Initialize tick_count
        self.tick_count = 0  # Add this line to initialize tick_count

        # WAR event state (must be defined before any update logic)
        self.predator_fight_mode = False  # Flag for predator fight event
        self.predator_fight_timer = 0  # Timer for predator fight event

        # Game objects
        self.swarm_bots: List[SwarmBot] = []
        self.food_list: List[Food] = []
        self.power_ups: List[PowerUp] = []
        self.predators: List[Predator] = []
        self.obstacles: List[Rock] = []

        # Buffs
        self.speed_buff_stacks = 0
        self.damage_buff_stacks = 0
        self.speed_buff_timer = 0
        self.damage_buff_timer = 0
        # Game state overlays and timers
        self.leader_down_message_timer = 0
        self.starvation_events = []
        self.bots_starved = 0
        self.historical_predator_kills = 0
        self.shake_timer = 0
        self.shake_magnitude = 0
        self.screen_flash_timer = 0
        self.no_breeders_message_timer = 0
        # Game over state
        self.game_over = False
        # Total bot deaths (starvation + killed by predators)
        self.bots_died = 0
        # Home and resource tracking
        home_x = random.uniform(80, SCREEN_WIDTH - 80)
        home_y = random.uniform(80, SCREEN_HEIGHT - 80)
        self.home = Home(int(home_x), int(home_y), radius=40)
        # Ensure Home has all expected attributes
        self.home.food_collected = getattr(self.home, 'food_collected', 0)
        self.home.ore_collected = getattr(self.home, 'ore_collected', 0)
        self.home.hitpoints = getattr(self.home, 'hitpoints', 1000)
        self.home.repair_cooldown = getattr(self.home, 'repair_cooldown', 0)
        self.home.is_home = getattr(self.home, 'is_home', True)
        self.home.radius = getattr(self.home, 'radius', 40)
        self.home.craft_points = getattr(self.home, 'craft_points', 0)  # Track craft points
        # Add global resource stats to Game
        self.ration = 0
        self.material = 0
        self.workunit = 0
        # Add Home to obstacles
        self.obstacles.append(self.home)
        # Initialize swarm
        for i in range(50):
            x = random.uniform(50, SCREEN_WIDTH - 50)
            y = random.uniform(50, SCREEN_HEIGHT - 50)
            if i == 0:
                self.swarm_bots.append(SwarmBot(x, y, 'leader', SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
                bot = SwarmBot(x, y, None, SCREEN_WIDTH, SCREEN_HEIGHT)
                # Buff scout speed
                if getattr(bot, 'role', None) == 'scout':
                    bot.base_max_speed *= 1.5
                    bot.max_speed = bot.base_max_speed
                self.swarm_bots.append(bot)
        # Initialize food - more food for better gameplay
        for _ in range(40):  # Increased from 30 to 40
            x = random.uniform(20, SCREEN_WIDTH - 20)
            y = random.uniform(20, SCREEN_HEIGHT - 20)
            self.food_list.append(Food(x, y))
        # Initialize predators - more predators for increased challenge
        for _ in range(3):  # Increased from 2 to 3 predators
            x = random.uniform(50, SCREEN_WIDTH - 50)
            y = random.uniform(50, SCREEN_HEIGHT - 50)
            self.predators.append(Predator(x, y, SCREEN_WIDTH, SCREEN_HEIGHT))
        # Initialize rocks
        for _ in range(6):
            x = random.uniform(40, SCREEN_WIDTH - 40)
            y = random.uniform(40, SCREEN_HEIGHT - 40)
            self.obstacles.append(Rock(x, y))
        # --- Defensive: ensure all attributes used elsewhere are initialized ---
        self.last_attack_time = 0
        self.last_spawn_time = 0
        self.last_event_time = 0
        self.last_leader_death_time = 0
        self.last_starvation_time = 0
        self.last_buff_time = 0
        self.last_predator_attack_time = 0
        self.last_home_repair_time = 0
        self.last_home_damage_time = 0
        self.last_make_them_fight_time = 0
        self.last_no_breeders_time = 0
        self.last_overlay_time = 0
        self.last_stat_update_time = 0
        self.last_ui_update_time = 0
        self.last_screen_flash_time = 0
        self.last_shake_time = 0
        self.last_predator_fight_time = 0
        self.last_predator_fight_end_time = 0
        self.last_predator_kill_time = 0
        self.last_bot_death_time = 0
        self.last_bot_spawn_time = 0
        self.last_food_spawn_time = 0
        self.last_powerup_spawn_time = 0
        self.last_rock_replenish_time = 0
        self.last_ore_deposit_time = 0
        self.last_food_deposit_time = 0
        self.last_gatherer_deposit_time = 0
        self.last_miner_deposit_time = 0
        self.last_scout_broadcast_time = 0
        self.last_hunter_attack_time = 0
        self.last_drone_repair_time = 0
        self.last_home_attack_time = 0
        self.last_home_destroyed_time = 0
        self.last_game_over_time = 0
        self.last_restart_time = 0
        self.last_draw_time = 0
        self.last_update_time = 0
        self.last_run_time = 0
        self.last_event_overlay_time = 0
        self.last_overlay_message_time = 0
        self.last_overlay_clear_time = 0
        self.last_overlay_fade_time = 0
        self.last_overlay_flash_time = 0
        self.last_overlay_shake_time = 0
        self.last_overlay_predator_fight_time = 0
        self.last_overlay_predator_fight_end_time = 0
        self.last_overlay_leader_down_time = 0
        self.last_overlay_no_breeders_time = 0
        self.last_overlay_starvation_time = 0
        self.last_overlay_buff_time = 0
        self.last_overlay_stat_time = 0
        self.last_overlay_ui_time = 0
        self.last_overlay_screen_flash_time = 0
        self.last_overlay_shake_time = 0
        self.last_overlay_predator_kill_time = 0
        self.last_overlay_bot_death_time = 0
        self.last_overlay_bot_spawn_time = 0
        self.last_overlay_food_spawn_time = 0
        self.last_overlay_powerup_spawn_time = 0
        self.last_overlay_rock_replenish_time = 0
        self.last_overlay_ore_deposit_time = 0
        self.last_overlay_food_deposit_time = 0
        self.last_overlay_gatherer_deposit_time = 0
        self.last_overlay_miner_deposit_time = 0
        self.last_overlay_scout_broadcast_time = 0
        self.last_overlay_hunter_attack_time = 0
        self.last_overlay_drone_repair_time = 0
        self.last_overlay_home_attack_time = 0
        self.last_overlay_home_destroyed_time = 0
        self.last_overlay_game_over_time = 0
        self.last_overlay_restart_time = 0
        # Defensive: ensure all PowerUp attributes are initialized for all types (repeat for any new PowerUps)
        for power_up in self.power_ups:
            if not hasattr(power_up, 'color') or not isinstance(power_up.color, tuple) or len(power_up.color) != 3:
                power_up.color = (255, 255, 255)
            # Defensive: always set health_value for all PowerUps
            if not hasattr(power_up, 'health_value') or not isinstance(power_up.health_value, (int, float)):
                # Try to fallback to energy_value if present (legacy), else 0
                if hasattr(power_up, 'energy_value') and isinstance(power_up.energy_value, (int, float)):
                    power_up.health_value = power_up.energy_value
                else:
                    power_up.health_value = 0
            if not hasattr(power_up, 'power_type') or not isinstance(power_up.power_type, str):
                power_up.power_type = 'health'
    
        self.frame_count = 0  # Track total frames for tick-based logic

    def trigger_shake(self, frames: int = 12, magnitude: int = 12) -> None:
        """Trigger a screen shake effect for a number of frames and magnitude."""
        self.shake_timer = frames
        self.shake_magnitude = magnitude

    def handle_events(self) -> bool:
        """Handle input events"""
        for event in pygame.event.get():  # type: ignore
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # type: ignore
                    # Quit game
                    return False
                elif event.key == pygame.K_SPACE:  # type: ignore
                    # Spawn more food (increased from 5 to 8)
                    spawn_food(8, self.food_list)
                elif event.key == pygame.K_p:  # type: ignore
                    # Spawn power-up
                    spawn_powerup(random.choice(['energy', 'speed', 'damage']), self.power_ups)
                elif event.key == pygame.K_b:  # type: ignore
                    # Manually spawn a new bot
                    new_bot = spawn_bot(None, self.swarm_bots)
                    # Apply any active swarm buffs to the new bot
                    if self.swarm_bots:  # If there are existing bots to check
                        sample_bot = self.swarm_bots[0]  # Check first bot for active buffs
                        if sample_bot.speed_boost_timer > 0:
                            new_bot.speed_boost_timer = sample_bot.speed_boost_timer
                            new_bot.max_speed = new_bot.base_max_speed * 1.5
                        if sample_bot.damage_boost_timer > 0:
                            new_bot.damage_boost_timer = sample_bot.damage_boost_timer
                elif event.key == pygame.K_r:  # type: ignore
                    # Restart the game by returning a special value
                    return 'restart'
                elif event.key == pygame.K_m:  # type: ignore
                    # MAKE THEM FIGHT event: predators hunt each other for 10 seconds
                    self.predator_fight_mode = True
                    self.predator_fight_timer = FPS * 10  # 10 seconds
        
        return True
    
    def update(self) -> None:
        """Update game state"""
        # Update bots
        new_bots: List[SwarmBot] = []
        bots_to_remove: List[SwarmBot] = []
        for bot in self.swarm_bots[:]:
            bot.update(self.swarm_bots, self.food_list, self.power_ups, self.predators, self.obstacles)
            # Hunters attack predators if in range
            bot.attack_predators(self.predators)
            # Check for reproduction
            new_bot = bot.attempt_reproduction(self.swarm_bots)
            if new_bot:
                new_bots.append(new_bot)
            # Mark dead bots for removal (do NOT remove here)
            if bot.health <= 0:
                bots_to_remove.append(bot)
                # Track starvation event for display
                self.starvation_events.append((bot.position.x, bot.position.y, 60, getattr(bot, 'role', '')))
                self.bots_starved += 1
        
        # Add newly reproduced bots
        self.swarm_bots.extend(new_bots)
        
        # Update predators and handle kills
        for predator in self.predators[:]:
            if self.predator_fight_mode:
                # Predators hunt each other
                other_preds = [p for p in self.predators if p is not predator]
                predator.update(other_preds, self.food_list, self.predators, self.power_ups, self.obstacles, fight_mode=True)
            else:
                killed_bots = predator.update(self.swarm_bots, self.food_list, self.predators, self.power_ups, self.obstacles)
                for killed_bot in killed_bots:
                    if killed_bot in self.swarm_bots:
                        self.swarm_bots.remove(killed_bot)
                        self.historical_predator_kills += 1
                        self.bots_died += 1
                        # Award craft points for predator kills (1 or 2 randomly)
                        if hasattr(self.home, 'craft_points'):
                            points = random.choice([1, 2])
                            self.home.craft_points += points
                            print(f"[DEBUG] Home earned {points} craft point(s) for predator kill. Total: {self.home.craft_points}")
        # Remove dead predators and handle respawn/food drop
        handle_dead_predators(self)
        
        # Remove all dead bots and handle leader/harvester events
        remove_dead_bots(self, bots_to_remove)
        
        # Update power-ups
        for power_up in self.power_ups:
            power_up.update()
        
        # Update obstacles with collision
        for rock in self.obstacles:
            rock.update(SCREEN_WIDTH, SCREEN_HEIGHT, self.obstacles)
        
        # Check food collection
        for bot in self.swarm_bots:
            # Gatherer collection process
            if getattr(bot, 'role', None) == 'gatherer':
                # If gatherer is carrying food or ore and is close to Home, deposit
                if hasattr(bot, 'carrying_food') and bot.carrying_food > 0:
                    distance_to_home = (bot.position - self.home.position).magnitude()
                    if distance_to_home < bot.radius + getattr(self.home, 'radius', 40):
                        # Deposit food at Home
                        if not hasattr(self.home, 'food_collected'):
                            self.home.food_collected = 0
                        print(f"[DEBUG] Gatherer at {bot.position} delivered {bot.carrying_food} food to Home at {self.home.position}")
                        self.home.food_collected += bot.carrying_food
                        print(f"[DEBUG] Home food_collected is now {self.home.food_collected}")
                        bot.carrying_food = 0
                # --- NEW: If not carrying food and not eating, search for food if idle ---
                if (not hasattr(bot, 'carrying_food') or bot.carrying_food == 0) and bot.health >= 70:
                    # Find nearest food
                    nearest_food = None
                    min_dist = float('inf')
                    for food in self.food_list:
                        dist = (bot.position - food.position).magnitude()
                        if dist < min_dist:
                            min_dist = dist
                            nearest_food = food
                    # If food exists and is not very close, nudge bot toward it
                    if nearest_food and min_dist > bot.radius + 2:
                        direction = (nearest_food.position - bot.position).normalize()
                        # Nudge bot's velocity toward food (gentle, so it doesn't override avoidance/other logic)
                        if hasattr(bot, 'velocity'):
                            bot.velocity += direction * 0.2  # Small nudge
                            # Clamp velocity to max speed
                            if bot.velocity.magnitude() > bot.max_speed:
                                bot.velocity = bot.velocity.normalize() * bot.max_speed
                # If not carrying, collect food as usual
            # Check food consumption
            for food in self.food_list[:]:
                distance = (bot.position - food.position).magnitude()
                if distance < bot.radius + food.radius:
                    if getattr(bot, 'role', None) == 'gatherer':
                        if not hasattr(bot, 'carrying_food'):
                            bot.carrying_food = 0
                        # Eat if hungry and not carrying food
                        if bot.health < 70 and bot.carrying_food == 0:
                            print(f"[DEBUG] Gatherer at {bot.position} eats food at {food.position}")
                            bot.health = min(100, bot.health + food.health_value)
                            self.food_list.remove(food)
                            break
                        # If not hungry and not carrying, gather
                        elif bot.health >= 70 and bot.carrying_food == 0:
                            print(f"[DEBUG] Gatherer at {bot.position} picks up food at {food.position}")
                            bot.carrying_food = food.health_value
                            self.food_list.remove(food)
                            break
                        # Otherwise, do nothing (already carrying or not eligible)
                    elif getattr(bot, 'role', None) == 'scout':
                        # Scouts only eat if health < 60
                        if bot.health < 60:
                            bot.health = min(100, bot.health + food.health_value)
                            self.food_list.remove(food)
                            break
                    else:
                        bot.health = min(100, bot.health + food.health_value)
                        self.food_list.remove(food)
                        break
            
            # Check power-up collection
            for power_up in self.power_ups[:]:
                distance = (bot.position - power_up.position).magnitude()
                if distance < bot.radius + power_up.radius:
                    bot.health = min(100, bot.health + power_up.health_value)

                    # Apply power-up effects to ALL bots in the swarm (stacking)
                    if power_up.power_type == 'speed':
                        self.speed_buff_stacks += 1
                        self.speed_buff_timer = 300  # 5 seconds at 60 FPS (refresh duration)
                        for swarm_bot in self.swarm_bots:
                            swarm_bot.speed_boost_timer = 300
                            swarm_bot.max_speed = swarm_bot.base_max_speed * (1.5 ** self.speed_buff_stacks)
                    elif power_up.power_type == 'damage':
                        self.damage_buff_stacks += 1
                        self.damage_buff_timer = 300
                        for swarm_bot in self.swarm_bots:
                            swarm_bot.damage_boost_timer = 300
                    # Health power-ups still only affect the collector

                    self.power_ups.remove(power_up)
                    break
        
        # --- MINER LOGIC: Seek rocks, collect ore, deliver to Home ---
        for bot in self.swarm_bots:
            if getattr(bot, 'role', None) == 'miner':
                # If miner is carrying ore and is close to Home, deposit
                if hasattr(bot, 'carrying_ore') and bot.carrying_ore > 0:
                    distance_to_home = (bot.position - self.home.position).magnitude()
                    if distance_to_home < bot.radius + getattr(self.home, 'radius', 40):
                        if not hasattr(self.home, 'ore_collected'):
                            self.home.ore_collected = 0
                        print(f"[DEBUG] Miner at {bot.position} delivered {bot.carrying_ore} ore to Home at {self.home.position}")
                        self.home.ore_collected += bot.carrying_ore
                        bot.carrying_ore = 0
                # If not carrying max ore, seek nearest rock with ore
                if (not hasattr(bot, 'carrying_ore') or bot.carrying_ore < 2) and bot.health >= 70:
                    # Find nearest rock with ore
                    nearest_rock = None
                    min_dist = float('inf')
                    for rock in self.obstacles:
                        if hasattr(rock, 'ore_amount') and rock.ore_amount > 0:
                            dist = (bot.position - rock.position).magnitude()
                            if dist < min_dist:
                                min_dist = dist
                                nearest_rock = rock
                    # If rock exists and is not very close, nudge bot toward it
                    if nearest_rock and min_dist > bot.radius + nearest_rock.radius + 2:
                        direction = (nearest_rock.position - bot.position).normalize()
                        if hasattr(bot, 'velocity'):
                            bot.velocity += direction * 0.2
                            if bot.velocity.magnitude() > bot.max_speed:
                                bot.velocity = bot.velocity.normalize() * bot.max_speed
                # If not carrying max ore, collect ore from rock if close enough
                for rock in self.obstacles:
                    if hasattr(rock, 'ore_amount') and rock.ore_amount > 0:
                        distance = (bot.position - rock.position).magnitude()
                        if distance < bot.radius + rock.radius:
                            if not hasattr(bot, 'carrying_ore'):
                                bot.carrying_ore = 0
                            if bot.carrying_ore < 2:  # Limit ore collection to 2 per trip
                                ore_taken = min(1, rock.ore_amount, 2 - bot.carrying_ore)  # Collect 1 ore at a time
                                bot.carrying_ore += ore_taken
                                rock.ore_amount -= ore_taken
                                print(f"[DEBUG] Miner at {bot.position} mined {ore_taken} ore from rock at {rock.position} (carrying {bot.carrying_ore}/2)")
                                break
                # Heal miners when near Home
                distance_to_home = (bot.position - self.home.position).magnitude()
                if distance_to_home < bot.radius + getattr(self.home, 'radius', 40) + 10:
                    if bot.health < 100:
                        bot.health = min(100, bot.health + 0.5)
        
        # Heal gatherers when near Home
        for bot in self.swarm_bots:
            if getattr(bot, 'role', None) == 'gatherer':
                distance_to_home = (bot.position - self.home.position).magnitude()
                if distance_to_home < bot.radius + getattr(self.home, 'radius', 40) + 10:
                    if bot.health < 100:
                        bot.health = min(100, bot.health + 0.5)  # Heal 0.5 per frame near Home
        
        # Randomly spawn new food (increased spawn rate)
        if random.random() < 0.04:  # Increased from 2% to 4% chance per frame
            spawn_food(1, self.food_list)
        
        # Additional food spawning when food is scarce
        if len(self.food_list) < 15:  # Spawn extra food when below 15 items
            if random.random() < 0.06:  # 6% chance when food is scarce
                spawn_food(1, self.food_list)
        
        # Randomly spawn power-ups
        if random.random() < 0.005:  # 0.5% chance per frame
            power_type = random.choice(['energy', 'speed', 'damage'])
            spawn_powerup(power_type, self.power_ups)
        
        # Buff timer management
        if self.speed_buff_stacks > 0:
            self.speed_buff_timer -= 1
            if self.speed_buff_timer <= 0:
                self.speed_buff_stacks = 0
                for swarm_bot in self.swarm_bots:
                    swarm_bot.max_speed = swarm_bot.base_max_speed
        if self.damage_buff_stacks > 0:
            self.damage_buff_timer -= 1
            if self.damage_buff_timer <= 0:
                self.damage_buff_stacks = 0
        
        # Handle predator fight mode timer
        if self.predator_fight_mode:
            self.predator_fight_timer -= 1
            if self.predator_fight_timer <= 0:
                self.predator_fight_mode = False
        
        # Decrement leader down message timer if active
        if self.leader_down_message_timer > 0:
            self.leader_down_message_timer -= 1
        
        # Decrement screen flash timer if active (but don't use it for visual effects)
        if self.screen_flash_timer > 0:
            self.screen_flash_timer -= 1
    
    def draw(self) -> None:
        """Draw everything"""
        # Screen shake offset
        shake_x, shake_y = 0, 0
        
        # Only apply shake effects if we actually want screen shake
        if self.shake_timer > 0:
            # Apply screen shake offset
            shake_x = random.randint(-self.shake_magnitude, self.shake_magnitude)
            shake_y = random.randint(-self.shake_magnitude, self.shake_magnitude)
            self.shake_timer -= 1
            
            # Optional: Flash effect during shake (commented out to prevent flickering)
            # if self.shake_timer % 4 < 2:
            #     self.screen.fill((255, 0, 0))
            # else:
            #     self.screen.fill(BLACK)
        
        # Always fill with black background (stable, no flickering)
        self.screen.fill(BLACK)
        
        # Draw food
        for food in self.food_list:
            food.draw(self.screen, offset=(shake_x, shake_y))
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen, offset=(shake_x, shake_y))
        
        # Draw predators
        for predator in self.predators:
            predator.draw(self.screen, offset=(shake_x, shake_y))
            # Draw predator buffs above predator if active
            if hasattr(predator, 'buff_timers') and (predator.buff_timers.get('speed', 0) > 0 or predator.buff_timers.get('damage', 0) > 0):
                buff_texts = []
                buff_colors = []
                if predator.buff_timers.get('speed', 0) > 0:
                    speed_seconds = predator.buff_timers['speed'] // 60
                    buff_texts.append(f"SPD {speed_seconds}s")
                    buff_colors.append((0, 255, 255))
                if predator.buff_timers.get('damage', 0) > 0:
                    damage_seconds = predator.buff_timers['damage'] // 60
                    buff_texts.append(f"DMG {damage_seconds}s")
                    buff_colors.append((255, 165, 0))
                # Draw each buff text above predator, stacked vertically
                for i, (text, color) in enumerate(zip(buff_texts, buff_colors)):
                    buff_surface = self.font.render(text, True, color)
                    buff_rect = buff_surface.get_rect()  # type: ignore[attr-defined]
                    # Stack below the name label
                    buff_rect.center = (int(predator.position.x), int(predator.position.y - predator.radius - 26 - i * 18))
                    self.screen.blit(buff_surface, buff_rect)
        
        # Draw bots
        for bot in self.swarm_bots:
            bot.draw(self.screen, offset=(shake_x, shake_y))
            # Hunter-on-predator combat visual feedback
            if (
                getattr(bot, 'role', None) == 'hunter' and 
                hasattr(bot, 'attack_effect_timer') and bot.attack_effect_timer > 0 and 
                getattr(bot, 'last_attack_target_pos', None) is not None
            ):
                # Draw pulsing line from hunter to predator
                wx, wy = int(bot.position.x + shake_x), int(bot.position.y + shake_y)
                px, py = bot.last_attack_target_pos
                px, py = int(px + shake_x), int(py + shake_y)
                pulse = 180 + int(75 * abs(math.sin(bot.attack_effect_timer * 0.7)))
                color = (255, pulse, 80)
                width = 6 if bot.attack_effect_timer % 2 == 0 else 3
                pygame.draw.line(self.screen, color, (wx, wy), (px, py), width)
                # Draw impact flash at predator
                impact_radius = 18 + 2 * bot.attack_effect_timer
                impact_alpha = min(255, 120 + 20 * bot.attack_effect_timer)
                impact_color = (255, 255, 255) if bot.attack_effect_timer % 2 == 0 else (255, 0, 255)
                s = pygame.Surface((impact_radius*2, impact_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*impact_color, impact_alpha), (impact_radius, impact_radius), impact_radius)
                self.screen.blit(s, (px-impact_radius, py-impact_radius))
                # Pulse hunter outline
                outline_radius = bot.radius + 10 + bot.attack_effect_timer
                outline_color = (255, 0, 180) if bot.attack_effect_timer % 2 == 0 else (255, 255, 255)
                pygame.draw.circle(self.screen, outline_color, (wx, wy), outline_radius, 2)

        # Draw obstacles
        for rock in self.obstacles:
            rock.draw(self.screen, offset=(shake_x, shake_y))
        
        # Draw Home
        self.home.draw(self.screen, offset=(shake_x, shake_y))

        # Draw global stats (top right): ration, material, workunit, miner count, ticks
        stats_font = pygame.font.SysFont(None, 24)
        stats_lines = [
            f"Ration: {getattr(self, 'ration', 0)}",
            f"Material: {getattr(self, 'material', 0)}",
            f"Craftsmanship: {getattr(self, 'craftsmanship', 0)}",
            f"Miners: {sum(1 for b in self.swarm_bots if getattr(b, 'role', None) == 'miner')}"
        ]
        for i, line in enumerate(stats_lines):
            stats_surf = stats_font.render(line, True, (255, 255, 0))
            stats_rect = stats_surf.get_rect(topright=(self.screen.get_width() - 12, 12 + i * 26))
            self.screen.blit(stats_surf, stats_rect)
        # Draw Ticks counter below global stats
        ticks_font = pygame.font.SysFont(None, 22)
        ticks_surf = ticks_font.render(f"Ticks: {getattr(self, 'tick_count', 0)}", True, (200, 200, 255))
        ticks_rect = ticks_surf.get_rect(topright=(self.screen.get_width() - 12, 12 + len(stats_lines) * 26 + 8))
        self.screen.blit(ticks_surf, ticks_rect)

        # --- UI ---
        self.ui.draw(self.screen, self, SCREEN_HEIGHT, SCREEN_WIDTH)
        pygame.display.flip()
    
    def show_game_over_screen(self):
        """Display a Game Over screen and wait for user input, with play field visible in background."""
        game_over_font = pygame.font.Font(None, 120)
        info_font = pygame.font.Font(None, 40)
        screen = self.screen
        screen_width, screen_height = screen.get_width(), screen.get_height()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return 'restart'
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
            # Draw the play field in the background
            self.draw()
            # Overlay a semi-transparent black rectangle
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # 180 alpha for strong but not full opacity
            screen.blit(overlay, (0, 0))
            # Draw GAME OVER text and info
            text = game_over_font.render("GAME OVER", True, (255, 60, 60))
            text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2 - 40))
            screen.blit(text, text_rect)
            info = info_font.render("Press R to Restart or ESC to Quit", True, (255, 255, 255))
            info_rect = info.get_rect(center=(screen_width // 2, screen_height // 2 + 60))
            screen.blit(info, info_rect)
            pygame.display.flip()
            self.clock.tick(30)

    def run(self) -> str | None:
        """Main game loop"""
        running = True
        while running:
            result = self.handle_events()
            if result == 'restart':
                return 'restart'
            running = result
            self.update()
            self.frame_count += 1
            if self.frame_count % TICK_FRAMES == 0:
                tick_eval(self)  # Call tick evaluation
            # End the game if no bots remain
            if len(self.swarm_bots) == 0:
                print("All bots have died. Game over.")
                restart = self.show_game_over_screen()
                if restart == 'restart':0
            if self.home.hitpoints <= 0:
                print("Home has been destroyed. Game over.")
                restart = self.show_game_over_screen()
                if restart == 'restart':
                    return 'restart'
                break
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        return None


def main() -> None:
    """Entry point for the swarm tank simulation."""
    while True:
        game = Game()
        result = game.run()
        if result != 'restart':
            break


if __name__ == "__main__":
    main()

def tick_eval(game: 'Game') -> None:
    """Perform tick-based evaluation. Called every TICK_FRAMES frames from the main game loop."""
    # Increment tick count
    game.tick_count += 1
    
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
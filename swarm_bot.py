"""
SwarmBot class - Individual bot in the swarm
"""
from __future__ import annotations
import random
import math
import pygame
from typing import List, Tuple, TYPE_CHECKING

from vector2d import Vector2D
from roles import BOT_ROLES, ROLE_WEIGHTS
# Removed unused import: from rock import Rock

if TYPE_CHECKING:
    from entities import Food, PowerUp, Predator, Home


class SwarmBot:
    """Individual bot in the swarm"""
    def __init__(self, x: float, y: float, role: str | None = None, screen_width: int = 1200, screen_height: int = 800):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(random.uniform(-2, 2), random.uniform(-2, 2))
        self.acceleration = Vector2D(0, 0)
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Assign role
        if role is None:
            role = self.assign_random_role()
        self.role = role
        self.role_data = BOT_ROLES[role]
        
        # Role-based attributes
        self.base_max_speed: float = self.role_data.max_speed
        self.max_speed: float = self.base_max_speed
        self.max_force: float = self.role_data.max_force
        self.color = self.role_data.color
        self.radius = 3
        self.health = 100.0
        self.trail: List[Tuple[float, float]] = []
        self.trail_length = 10
        
        # Power-up effects
        self.speed_boost_timer = 0
        self.damage_boost_timer = 0
        self.base_attack_damage = self.role_data.get('attack_damage', 20)
        
        # Scout shout mechanism
        self.shout_cooldown = 0
        self.shouted_food: set[int] = set()
        self.target_food: Food | None = None
        
        # Hunter taunt mechanism
        self.taunt_cooldown = 0
        self.taunt_effect_timer = 0
        
        # Harvester priority targeting
        self.food_burst_active = False
        self.closest_food_distance = float('inf')
        self.priority_food_target: Food | PowerUp | None = None
        
        # Reproduction system
        self.reproduction_cooldown = 0
        self.reproduction_health_threshold = 70.0  # Reduced from 80.0 to 70.0
    
        # For visual feedback
        self.last_attack_target_pos = None
        # --- Gatherer food carrying ---
        if self.role == 'gatherer':
            self.carrying_food = 0  # Amount of food being carried (health value)
        # --- Miner ore carrying ---
        if self.role == 'miner':
            self.carrying_ore = 0  # Amount of ore being carried
    
    def assign_random_role(self) -> str:
        """Assign a random role based on weights"""
        roles = list(ROLE_WEIGHTS.keys())
        weights = list(ROLE_WEIGHTS.values())
        return random.choices(roles, weights=weights)[0]
    
    def update_harvester_priority_targeting(self, food_list: List['Food'], power_ups: List['PowerUp']) -> None:
        """Update harvester/gatherer priority targeting and burst speed"""
        if self.role not in ('harvester', 'gatherer'):
            return
            
        closest_target = None
        closest_distance = float('inf')
        priority_range = float(self.role_data.get('priority_food_range', 60))
        
        # Find closest food/power-up
        for target in list(food_list) + list(power_ups):
            distance = math.sqrt((self.position.x - target.position.x)**2 + 
                               (self.position.y - target.position.y)**2)
            if distance < closest_distance:
                closest_distance = distance
                closest_target = target
        
        self.closest_food_distance = closest_distance
        self.priority_food_target = closest_target
        
        # Apply burst speed when food is within priority range
        was_burst_active = self.food_burst_active
        self.food_burst_active = bool(closest_target and closest_distance <= priority_range)
        
        if self.food_burst_active and not was_burst_active:
            self.max_speed = self.base_max_speed * float(self.role_data.get('burst_speed_multiplier', 1.8))
        elif not self.food_burst_active and was_burst_active:
            self.max_speed = self.base_max_speed
    
    def shout_food_discovery(self, food: 'Food', nearby_bots: List['SwarmBot']) -> None:
        """Scout shouts about discovered food to nearby bots"""
        if self.role != 'scout' or self.shout_cooldown > 0:
            return
        
        food_id = id(food)
        if food_id in self.shouted_food:
            return
        
        shout_range = float(self.role_data.get('shout_range', 80))
        shouted_to_count = 0
        
        for bot in nearby_bots:
            if bot is self:
                continue
                
            distance = math.sqrt((self.position.x - bot.position.x)**2 + 
                               (self.position.y - bot.position.y)**2)
            
            if distance <= shout_range:
                bot.receive_food_shout(food)
                shouted_to_count += 1
        
        if shouted_to_count > 0:
            self.shouted_food.add(food_id)
            self.shout_cooldown = 60

    def receive_food_shout(self, food: 'Food') -> None:
        """Receive a shout about food location from a scout"""
        if self.target_food is None:
            self.target_food = food
        else:
            current_distance = math.sqrt((self.position.x - self.target_food.position.x)**2 + 
                                       (self.position.y - self.target_food.position.y)**2)
            new_distance = math.sqrt((self.position.x - food.position.x)**2 + 
                                   (self.position.y - food.position.y)**2)
            if new_distance < current_distance:
                self.target_food = food
    
    def shout_predator_discovery(self, predator: 'Predator', nearby_bots: List['SwarmBot']) -> None:
        """Scout shouts about discovered predator to nearby bots"""
        if self.role != 'scout' or getattr(self, 'predator_shout_cooldown', 0) > 0:
            return
        pred_id = id(predator)
        if not hasattr(self, 'shouted_predators'):
            self.shouted_predators = set()
        if pred_id in self.shouted_predators:
            return
        shout_range = float(self.role_data.get('shout_range', 80))
        shouted_to_count = 0
        for bot in nearby_bots:
            if bot is self:
                continue
            distance = math.sqrt((self.position.x - bot.position.x)**2 + (self.position.y - bot.position.y)**2)
            if distance <= shout_range:
                bot.receive_predator_shout(predator)
                shouted_to_count += 1
        if shouted_to_count > 0:
            self.shouted_predators.add(pred_id)
            self.predator_shout_cooldown = 90  # Slightly longer cooldown for predator shouts

    def receive_predator_shout(self, predator: 'Predator') -> None:
        """Receive a shout about predator location from a scout"""
        # Bots can use this info to avoid the predator more aggressively
        if not hasattr(self, 'known_predators'):
            self.known_predators = set()
        self.known_predators.add(id(predator))
        # Optionally, could set a temporary avoidance boost or panic state
        self.avoid_predator_boost_timer = getattr(self, 'avoid_predator_boost_timer', 0) + 60

    def taunt_enemies(self, predators: List['Predator']) -> bool:
        """Hunter taunts nearby predators to draw them away from the swarm"""
        if self.role != 'hunter' or self.taunt_cooldown > 0:
            return False
        
        taunt_range = float(self.role_data.get('taunt_range', 60)) * 2  # Doubled aggro range
        taunt_force = float(self.role_data.get('taunt_force', 0.8))
        taunted_count = 0
        
        for predator in predators:
            distance = math.sqrt((self.position.x - predator.position.x)**2 + 
                               (self.position.y - predator.position.y)**2)
            
            if distance <= taunt_range:
                taunt_direction = self.position - predator.position
                if taunt_direction.magnitude() > 0:
                    taunt_direction = taunt_direction.normalize()
                    taunt_velocity = taunt_direction * taunt_force
                    predator.velocity = predator.velocity + taunt_velocity
                    
                    # Hunters can damage predators when very close
                    attack_range = float(self.role_data.get('attack_range', 15))
                    if distance <= attack_range:
                        attack_damage = float(self.role_data.get('attack_damage', 20))
                        
                        # Apply damage boost if active
                        if self.damage_boost_timer > 0:
                            attack_damage *= 2.0  # Double damage when boosted
                        
                        predator.health -= attack_damage  # Apply all damage to health
                    
                    taunted_count += 1
        
        if taunted_count > 0:
            self.taunt_cooldown = 120
            self.taunt_effect_timer = 30
            return True
        
        return False
    
    def attempt_reproduction(self, swarm_bots: List['SwarmBot']) -> SwarmBot | None:
        """Harvester/Gatherer attempts to reproduce when conditions are favorable"""
        if (self.role not in ('harvester', 'gatherer') or 
            self.reproduction_cooldown > 0 or 
            self.health < self.reproduction_health_threshold):
            return None
        
        # Check if there's food nearby (encourages reproduction near resources)
        if self.closest_food_distance > 80:  # Increased from 50 to 80
            return None
        
        # Check reproduction chance
        reproduction_chance = float(self.role_data.get('reproduction_chance', 0.25))
        if random.random() > reproduction_chance:
            return None
        
        # Find suitable reproduction location (away from other bots but not too far)
        reproduction_attempts = 10
        for _ in range(reproduction_attempts):
            # Try to spawn near the parent but with some distance
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(30, 60)
            spawn_x = self.position.x + math.cos(angle) * distance
            spawn_y = self.position.y + math.sin(angle) * distance
            
            # Keep within screen bounds
            spawn_x = max(20, min(self.screen_width - 20, spawn_x))
            spawn_y = max(20, min(self.screen_height - 20, spawn_y))
            
            # Check if location is not too crowded
            too_crowded = False
            min_spawn_distance = 25
            for other_bot in swarm_bots:
                dist = math.sqrt((spawn_x - other_bot.position.x)**2 + 
                               (spawn_y - other_bot.position.y)**2)
                if dist < min_spawn_distance:
                    too_crowded = True
                    break
            
            if not too_crowded:
                # Create new bot (could be any role, but slight bias toward harvester/gatherer)
                # 35% drone, 20% harvester, 40% gatherer, 5% random
                roll = random.random()
                if roll < 0.35:
                    new_role = 'drone'
                elif roll < 0.55:
                    new_role = 'harvester'
                elif roll < 0.95:
                    new_role = 'gatherer'
                else:
                    new_role = None  # Random role
                
                new_bot = SwarmBot(spawn_x, spawn_y, new_role, self.screen_width, self.screen_height)
                new_bot.health = 60.0  # Start with decent health
                
                # Inherit any active swarm buffs from parent
                if self.speed_boost_timer > 0:
                    new_bot.speed_boost_timer = self.speed_boost_timer
                    new_bot.max_speed = new_bot.base_max_speed * 1.5
                if self.damage_boost_timer > 0:
                    new_bot.damage_boost_timer = self.damage_boost_timer
                
                # Parent pays health cost for reproduction
                self.health -= 35.0  # Reduced from 40.0 to 35.0
                self.reproduction_cooldown = 180  # Reduced from 300 to 180 (3 seconds at 60 FPS)
                
                return new_bot
        
        return None
    
    def update(self, swarm_bots: List['SwarmBot'], food_list: List['Food'], 
               power_ups: List['PowerUp'], predators: List['Predator'], rocks: list = None, home: 'Home' = None) -> None:
        """Update bot position and behavior"""
        # Update cooldowns
        if self.shout_cooldown > 0:
            self.shout_cooldown -= 1
        if self.taunt_cooldown > 0:
            self.taunt_cooldown -= 1
        if self.taunt_effect_timer > 0:
            self.taunt_effect_timer -= 1
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1
        
        # Update power-up buff timers
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer == 0:
                self.max_speed = self.base_max_speed  # Reset speed when buff expires
        
        if self.damage_boost_timer > 0:
            self.damage_boost_timer -= 1
        
        # Hunter auto-taunt
        if (self.role == 'hunter' and self.taunt_cooldown == 0 and predators):
            for predator in predators:
                distance = math.sqrt((self.position.x - predator.position.x)**2 + 
                                   (self.position.y - predator.position.y)**2)
                if distance < float(self.role_data.get('taunt_range', 60)):
                    self.taunt_enemies(predators)
                    break
        # Reset acceleration
        self.acceleration = Vector2D(0, 0)

        # --- HUNTER: prioritize attacking predators over eating ---
        if self.role == 'hunter' and predators:
            # Find closest predator within hunt/aggro range
            hunt_range = float(self.role_data.get('taunt_range', 60)) * 8  # quadruple range
            closest_pred = None
            closest_dist = float('inf')
            for predator in predators:
                dist = math.sqrt((self.position.x - predator.position.x)**2 + (self.position.y - predator.position.y)**2)
                if dist < hunt_range and dist < closest_dist:
                    closest_dist = dist
                    closest_pred = predator
            if closest_pred is not None:
                # Seek the predator directly (override seek_food)
                sep = self.separate(swarm_bots) * 4.0  # Stronger separation for hunters
                ali = self.align(swarm_bots) * 1.0
                coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                avoid_predators = Vector2D(0, 0)  # Hunters don't avoid
                seek_pred = (closest_pred.position - self.position).normalize() * self.max_speed
                self.acceleration = self.acceleration + sep + ali + coh + (seek_pred - self.velocity).limit(self.max_force) + avoid_predators
                # ...skip food seeking...
            else:
                # No predator in range, fallback to normal food seeking
                sep = self.separate(swarm_bots) * 4.0  # Stronger separation for hunters
                ali = self.align(swarm_bots) * 1.0
                coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                seek_food = self.seek_food(food_list, power_ups, swarm_bots) * float(self.role_data.get('food_seek_weight', 2.5))
                avoid_predators = Vector2D(0, 0)
                self.acceleration = self.acceleration + sep + ali + coh + seek_food + avoid_predators
        else:
            # Harvester, Gatherer, Miner priority targeting
            if self.role in ('harvester', 'gatherer'):
                self.update_harvester_priority_targeting(food_list, power_ups)
            # Miner: ore targeting
            if self.role == 'miner':
                self.update_miner_priority_targeting(rocks)
            # Apply swarm behaviors
            sep = self.separate(swarm_bots) * (2.0 if self.role != 'hunter' else 4.0)
            ali = self.align(swarm_bots) * 1.0
            coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
            if self.role == 'miner':
                seek_ore = self.seek_ore(rocks) * float(self.role_data.get('ore_seek_weight', 2.5))
            else:
                seek_ore = Vector2D(0, 0)
            seek_food = self.seek_food(food_list, power_ups, swarm_bots) * float(self.role_data.get('food_seek_weight', 2.5))
            # Only non-hunters avoid predators
            if self.role != 'hunter':
                avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
            else:
                avoid_predators = Vector2D(0, 0)
            # Harvester/Gatherer burst mode adjustments
            if self.role in ('harvester', 'gatherer') and self.food_burst_active:
                ali = ali * 0.3
                coh = coh * 0.2
                seek_food = seek_food * 1.5
            # Miner burst mode
            if self.role == 'miner' and self.ore_burst_active:
                ali = ali * 0.3
                coh = coh * 0.2
                seek_ore = seek_ore * 1.5
            self.acceleration = self.acceleration + sep + ali + coh + seek_food + seek_ore + avoid_predators
        # Gatherer delivery logic
        if self.role == 'gatherer':
            # If carrying food, seek Home
            if getattr(self, 'carrying_food', 0) > 0 and home is not None:
                # Seek Home instead of food
                sep = self.separate(swarm_bots) * 2.0
                ali = self.align(swarm_bots) * 1.0
                coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                seek_home = (home.position - self.position).normalize() * self.max_speed
                avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
                self.acceleration = sep + ali + coh + (seek_home - self.velocity).limit(self.max_force) + avoid_predators
            else:
                # Only pick up food if not carrying and health >= 70
                if getattr(self, 'carrying_food', 0) == 0:
                    for food in list(food_list):
                        distance = math.sqrt((self.position.x - food.position.x)**2 + (self.position.y - food.position.y)**2)
                        if distance < self.radius + food.radius:
                            if self.health < 70:
                                self.health = min(100, self.health + food.health_value)
                                food_list.remove(food)
                                break
                            else:
                                self.carrying_food = food.health_value
                                food_list.remove(food)
                                break
                # Only seek food if not carrying
                if getattr(self, 'carrying_food', 0) == 0:
                    # ...existing code for swarm behaviors and food seeking...
                    sep = self.separate(swarm_bots) * 2.0
                    ali = self.align(swarm_bots) * 1.0
                    coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                    seek_food = self.seek_food(food_list, power_ups, swarm_bots) * float(self.role_data.get('food_seek_weight', 2.5))
                    avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
                    if self.food_burst_active:
                        ali = ali * 0.3
                        coh = coh * 0.2
                        seek_food = seek_food * 1.5
                    self.acceleration = sep + ali + coh + seek_food + avoid_predators
        # Miner delivery logic
        if self.role == 'miner':
            # If carrying ore, seek Home
            if getattr(self, 'carrying_ore', 0) > 0 and home is not None:
                sep = self.separate(swarm_bots) * 2.0
                ali = self.align(swarm_bots) * 1.0
                coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                seek_home = (home.position - self.position).normalize() * self.max_speed
                avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
                self.acceleration = sep + ali + coh + (seek_home - self.velocity).limit(self.max_force) + avoid_predators
            else:
                # Only pick up ore if not carrying
                if getattr(self, 'carrying_ore', 0) == 0:
                    for rock in list(rocks):
                        offset = self.position - rock.position
                        distance = offset.magnitude()
                        if distance < self.radius + getattr(rock, 'radius', 12) + 2:
                            # Pick up ore from rock
                            self.carrying_ore = 10  # Each rock gives 10 ore per pickup
                            if hasattr(rock, 'on_mined'):
                                rock.on_mined()
                            break
                # Only seek ore if not carrying
                if getattr(self, 'carrying_ore', 0) == 0:
                    sep = self.separate(swarm_bots) * 2.0
                    ali = self.align(swarm_bots) * 1.0
                    coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
                    seek_ore = self.seek_ore(rocks) * float(self.role_data.get('ore_seek_weight', 2.5))
                    avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
                    if self.ore_burst_active:
                        ali = ali * 0.3
                        coh = coh * 0.2
                        seek_ore = seek_ore * 1.5
                    self.acceleration = sep + ali + coh + seek_ore + avoid_predators
        # Update velocity and position
        # Smooth turning: blend new velocity with previous velocity
        smoothing = 0.7  # Higher = smoother, but less responsive
        new_velocity = self.velocity + self.acceleration
        new_velocity = new_velocity.limit(self.max_speed)
        self.velocity = self.velocity * smoothing + new_velocity * (1 - smoothing)
        self.velocity = self.velocity.limit(self.max_speed)
        self.position = self.position + self.velocity
        
        # Wrap around screen edges
        self.wrap_around()
        
        # Update trail
        self.trail.append((self.position.x, self.position.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        
        # Decrease health
        self.health -= 0.1
        if self.health < 0:
            self.health = 0

        # PredatorFood collection (edible by both bots and predators)
        from predator_food import PredatorFood
        for food in list(food_list):
            if isinstance(food, PredatorFood):
                distance = math.sqrt((self.position.x - food.position.x)**2 + (self.position.y - food.position.y)**2)
                if distance < self.radius + food.radius:
                    self.health = min(100, self.health + food.health_value)
                    food_list.remove(food)
                    break

        # Attempt reproduction (harvesters and gatherers only)
        if self.role in ('harvester', 'gatherer'):
            new_bot = self.attempt_reproduction(swarm_bots)
            if new_bot is not None:
                swarm_bots.append(new_bot)
        
        # Avoid rocks or take damage if colliding
        if rocks:
            for rock in rocks:
                offset = self.position - rock.position
                dist = offset.magnitude()
                min_dist = self.radius + rock.radius + 2
                # --- SOFT OBSTACLE LOGIC FOR HOME ---
                is_home = hasattr(rock, 'is_home') and getattr(rock, 'is_home', False)
                if is_home:
                    # Only gently repel, no damage, and allow gatherers to pass through
                    if self.role == 'gatherer':
                        if dist < min_dist - 8:
                            # Gently push out, no damage
                            if dist > 0:
                                push = offset.normalize() * (min_dist - dist + 1)
                                self.position += push * 0.5  # Softer push
                        continue  # No damage for gatherers
                    else:
                        if dist < min_dist:
                            # Gently push out, no damage
                            if dist > 0:
                                push = offset.normalize() * (min_dist - dist + 1)
                                self.position += push * 0.5
                            continue  # No damage for any bot on Home
                # --- END SOFT OBSTACLE LOGIC ---
                if dist < min_dist:
                    self.health -= 2.0  # Increased damage per frame in rock
                    if dist > 0:
                        push = offset.normalize() * (min_dist - dist + 1)
                        self.position += push
                        if hasattr(rock, 'impact'):
                            rock.impact(-push * 0.05)
                    if hasattr(rock, 'flash'):
                        rock.flash()
                elif dist < min_dist + 30:
                    avoid_force = offset.normalize() * (1.5 * (min_dist + 30 - dist) / 30)
                    self.acceleration += avoid_force
    
    def default_repair_action(self, home: 'Home') -> bool:
        # Drones repair Home if it's damaged and not on cooldown
        if self.role == 'drone' and home.hitpoints < home.max_hitpoints and home.repair_cooldown == 0:
            repair_amount = 50  # Drones repair 50 HP per action
            home.repair(repair_amount)
            return True
        return False
    
    def wrap_around(self):
        # Screen wrap-around logic
        if self.position.x < 0:
            self.position.x += self.screen_width
        elif self.position.x > self.screen_width:
            self.position.x -= self.screen_width
        if self.position.y < 0:
            self.position.y += self.screen_height
        elif self.position.y > self.screen_height:
            self.position.y -= self.screen_height

    def avoid_predators(self, predators) -> 'Vector2D':
        # Return a steering vector away from nearby predators
        steer = Vector2D(0, 0)
        count = 0
        for predator in predators:
            diff = self.position - predator.position
            dist = diff.magnitude()
            if dist < 80 and dist > 0:
                steer += diff.normalize() / dist
                count += 1
        if count > 0:
            steer = steer / count
            if steer.magnitude() > 0:
                steer = steer.normalize() * self.max_speed - self.velocity
                if steer.magnitude() > self.max_force:
                    steer = steer.normalize() * self.max_force
        return steer

    def seek_ore(self, rocks: list) -> 'Vector2D':
        # Seek the nearest rock with ore
        if not rocks:
            return Vector2D(0, 0)
        closest_rock = None
        closest_distance = float('inf')
        for rock in rocks:
            distance = (self.position - rock.position).magnitude()
            if distance < closest_distance:
                closest_distance = distance
                closest_rock = rock
        if closest_rock is not None:
            desired = closest_rock.position - self.position
            if desired.magnitude() > 0:
                return desired.normalize() * self.max_speed
        return Vector2D(0, 0)
    
    def separate(self, swarm_bots: List['SwarmBot']) -> 'Vector2D':
        # Steer to avoid crowding neighbors
        desired_separation = 18.0
        steer = Vector2D(0, 0)
        count = 0
        for other in swarm_bots:
            if other is self:
                continue
            d = (self.position - other.position).magnitude()
            if 0 < d < desired_separation:
                diff = (self.position - other.position).normalize()
                steer += diff / d
                count += 1
        if count > 0:
            steer = steer / count
        if steer.magnitude() > 0:
            steer = steer.normalize() * self.max_speed - self.velocity
            steer = steer.limit(self.max_force)
        return steer

    def align(self, swarm_bots: List['SwarmBot']) -> 'Vector2D':
        # Steer towards the average heading of local flockmates
        neighbor_dist = 40.0
        sum_vel = Vector2D(0, 0)
        count = 0
        for other in swarm_bots:
            if other is self:
                continue
            d = (self.position - other.position).magnitude()
            if 0 < d < neighbor_dist:
                sum_vel += other.velocity
                count += 1
        if count > 0:
            avg_vel = sum_vel / count
            avg_vel = avg_vel.normalize() * self.max_speed
            steer = avg_vel - self.velocity
            steer = steer.limit(self.max_force)
            return steer
        return Vector2D(0, 0)

    def cohesion(self, swarm_bots: List['SwarmBot']) -> 'Vector2D':
        # Steer to move toward the average position of local flockmates
        neighbor_dist = 40.0
        sum_pos = Vector2D(0, 0)
        count = 0
        for other in swarm_bots:
            if other is self:
                continue
            d = (self.position - other.position).magnitude()
            if 0 < d < neighbor_dist:
                sum_pos += other.position
                count += 1
        if count > 0:
            avg_pos = sum_pos / count
            desired = avg_pos - self.position
            if desired.magnitude() > 0:
                desired = desired.normalize() * self.max_speed
                steer = desired - self.velocity
                steer = steer.limit(self.max_force)
                return steer
        return Vector2D(0, 0)

    def seek_food(self, food_list: List['Food'], power_ups: List['PowerUp'], swarm_bots: List['SwarmBot']) -> 'Vector2D':
        # Seek the nearest food or power-up
        closest = None
        closest_dist = float('inf')
        for food in list(food_list) + list(power_ups):
            d = (self.position - food.position).magnitude()
            if d < closest_dist:
                closest_dist = d
                closest = food
        if closest is not None:
            desired = closest.position - self.position
            if desired.magnitude() > 0:
                return desired.normalize() * self.max_speed
        return Vector2D(0, 0)

    def update_miner_priority_targeting(self, rocks: list) -> None:
        # Update miner's ore targeting and burst mode
        if self.role != 'miner':
            return
        closest_rock = None
        closest_distance = float('inf')
        priority_range = float(self.role_data.get('priority_ore_range', 60))
        for rock in rocks or []:
            if hasattr(rock, 'ore_amount') and rock.ore_amount > 0:
                distance = (self.position - rock.position).magnitude()
                if distance < closest_distance:
                    closest_distance = distance
                    closest_rock = rock
        self.closest_ore_distance = closest_distance
        self.priority_ore_target = closest_rock
        was_burst_active = getattr(self, 'ore_burst_active', False)
        self.ore_burst_active = bool(closest_rock and closest_distance <= priority_range)
        if self.ore_burst_active and not was_burst_active:
            self.max_speed = self.base_max_speed * float(self.role_data.get('burst_speed_multiplier', 1.8))
        elif not self.ore_burst_active and was_burst_active:
            self.max_speed = self.base_max_speed

    def attack_predators(self, predators: List['Predator']) -> None:
        # Only hunters attack predators
        if self.role != 'hunter' or not predators:
            return
        attack_range = float(self.role_data.get('attack_range', 15))
        attack_damage = float(self.role_data.get('attack_damage', 20))
        if self.damage_boost_timer > 0:
            attack_damage *= 2.0  # Double damage when boosted
        for predator in predators:
            distance = (self.position - predator.position).magnitude()
            if distance <= attack_range:
                predator.health -= attack_damage
                # Visual feedback for attack
                self.last_attack_target_pos = (predator.position.x, predator.position.y)
                self.attack_effect_timer = 8  # Frames to show effect
                break

    def draw(self, screen: pygame.Surface, offset=(0, 0)) -> None:
        """Draw the bot on the screen"""
        ox, oy = offset
        
        # Draw trail first (behind the bot)
        if len(self.trail) > 1:
            trail_color = tuple(max(0, c - 150) for c in self.color)  # Darker version of bot color
            for i in range(1, len(self.trail)):
                alpha = int(255 * (i / len(self.trail)))  # Fade out older trail points
                start_pos = (int(self.trail[i-1][0]) + ox, int(self.trail[i-1][1]) + oy)
                end_pos = (int(self.trail[i][0]) + ox, int(self.trail[i][1]) + oy)
                
                # Create a surface with alpha for trail
                trail_surface = pygame.Surface((abs(end_pos[0] - start_pos[0]) + 4, abs(end_pos[1] - start_pos[1]) + 4), pygame.SRCALPHA)
                pygame.draw.line(trail_surface, (*trail_color, alpha), 
                               (2, 2), (end_pos[0] - start_pos[0] + 2, end_pos[1] - start_pos[1] + 2), 2)
                screen.blit(trail_surface, (min(start_pos[0], end_pos[0]) - 2, min(start_pos[1], end_pos[1]) - 2))
        
        # Main bot color
        bot_color = self.color
        
        # Color modifications based on state
        if hasattr(self, 'attack_effect_timer') and self.attack_effect_timer > 0:
            # Flash when attacking
            bot_color = (255, 255, 255) if self.attack_effect_timer % 2 == 0 else self.color
            self.attack_effect_timer -= 1
        elif self.health < 30:
            # Red tint when low health
            bot_color = tuple(min(255, c + 50) if i == 0 else max(0, c - 50) for i, c in enumerate(self.color))
        elif self.speed_boost_timer > 0 or self.damage_boost_timer > 0:
            # Bright glow when buffed
            bot_color = tuple(min(255, c + 30) for c in self.color)
        
        # Draw bot circle
        center = (int(self.position.x) + ox, int(self.position.y) + oy)
        pygame.draw.circle(screen, bot_color, center, self.radius)
        
        # Draw role-specific indicators
        if self.role == 'leader':
            # Leader gets a crown/star
            pygame.draw.circle(screen, (255, 255, 0), center, self.radius + 3, 2)
        elif self.role == 'hunter':
            # Hunter gets spikes
            pygame.draw.circle(screen, (255, 100, 100), center, self.radius + 2, 1)
        elif self.role == 'scout':
            # Scout gets extended vision circle
            pygame.draw.circle(screen, (100, 255, 255), center, self.radius + 1, 1)
        elif self.role in ('gatherer', 'harvester'):
            # Gatherer/Harvester shows what they're carrying
            if hasattr(self, 'carrying_food') and self.carrying_food > 0:
                pygame.draw.circle(screen, (0, 255, 0), center, self.radius + 2, 1)
        elif self.role == 'miner':
            # Miner shows ore carrying
            if hasattr(self, 'carrying_ore') and self.carrying_ore > 0:
                pygame.draw.circle(screen, (139, 69, 19), center, self.radius + 2, 1)  # Brown for ore
        
        # Draw health bar if damaged
        if self.health < 100:
            bar_width = self.radius * 2
            bar_height = 3
            bar_x = center[0] - self.radius
            bar_y = center[1] - self.radius - 6
            
            # Background (red)
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            
            # Health (green to red gradient)
            health_ratio = self.health / 100.0
            health_width = int(bar_width * health_ratio)
            if health_ratio > 0.6:
                health_color = (0, 255, 0)
            elif health_ratio > 0.3:
                health_color = (255, 255, 0)
            else:
                health_color = (255, 0, 0)
            
            if health_width > 0:
                pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Draw direction indicator
        if self.velocity.magnitude() > 0.1:
            direction = self.velocity.normalize() * (self.radius + 3)
            end_x = self.position.x + ox + direction.x
            end_y = self.position.y + oy + direction.y
            pygame.draw.line(screen, (255, 255, 255), center, (int(end_x), int(end_y)), 1)
"""
SwarmBot class - Individual bot in the swarm
"""
from __future__ import annotations
import pygame
import random
import math
from typing import List, Tuple, TYPE_CHECKING

from vector2d import Vector2D
from roles import BOT_ROLES, ROLE_WEIGHTS, WHITE, RED, ORANGE, YELLOW, CYAN

if TYPE_CHECKING:
    from entities import Food, PowerUp, Predator


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
        self.energy = 100.0
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
        
        # Warrior taunt mechanism
        self.taunt_cooldown = 0
        self.taunt_effect_timer = 0
        
        # Harvester priority targeting
        self.food_burst_active = False
        self.closest_food_distance = float('inf')
        self.priority_food_target: Food | PowerUp | None = None
        
        # Reproduction system
        self.reproduction_cooldown = 0
        self.reproduction_energy_threshold = 70.0  # Reduced from 80.0 to 70.0
    
    def assign_random_role(self) -> str:
        """Assign a random role based on weights"""
        roles = list(ROLE_WEIGHTS.keys())
        weights = list(ROLE_WEIGHTS.values())
        return random.choices(roles, weights=weights)[0]
    
    def update_harvester_priority_targeting(self, food_list: List['Food'], power_ups: List['PowerUp']) -> None:
        """Update harvester priority targeting and burst speed"""
        if self.role != 'harvester':
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
    
    def taunt_enemies(self, predators: List['Predator']) -> bool:
        """Warrior taunts nearby predators to draw them away from the swarm"""
        if self.role != 'warrior' or self.taunt_cooldown > 0:
            return False
        
        taunt_range = float(self.role_data.get('taunt_range', 60))
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
                    
                    # Warriors can damage predators when very close
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
        """Harvester attempts to reproduce when conditions are favorable"""
        if (self.role != 'harvester' or 
            self.reproduction_cooldown > 0 or 
            self.energy < self.reproduction_energy_threshold):
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
                # Create new bot (could be any role, but slight bias toward harvester)
                # 65% drone, 25% harvester, 10% random
                roll = random.random()
                if roll < 0.65:
                    new_role = 'drone'
                elif roll < 0.90:
                    new_role = 'harvester'
                else:
                    new_role = None  # Random role
                
                new_bot = SwarmBot(spawn_x, spawn_y, new_role, self.screen_width, self.screen_height)
                new_bot.energy = 60.0  # Start with decent energy
                
                # Inherit any active swarm buffs from parent
                if self.speed_boost_timer > 0:
                    new_bot.speed_boost_timer = self.speed_boost_timer
                    new_bot.max_speed = new_bot.base_max_speed * 1.5
                if self.damage_boost_timer > 0:
                    new_bot.damage_boost_timer = self.damage_boost_timer
                
                # Parent pays energy cost for reproduction
                self.energy -= 35.0  # Reduced from 40.0 to 35.0
                self.reproduction_cooldown = 180  # Reduced from 300 to 180 (3 seconds at 60 FPS)
                
                return new_bot
        
        return None
    
    def update(self, swarm_bots: List['SwarmBot'], food_list: List['Food'], 
               power_ups: List['PowerUp'], predators: List['Predator'], obstacles: list = None) -> None:
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
        
        # Warrior auto-taunt
        if (self.role == 'warrior' and self.taunt_cooldown == 0 and predators):
            for predator in predators:
                distance = math.sqrt((self.position.x - predator.position.x)**2 + 
                                   (self.position.y - predator.position.y)**2)
                if distance < float(self.role_data.get('taunt_range', 60)):
                    self.taunt_enemies(predators)
                    break
        
        # Reset acceleration
        self.acceleration = Vector2D(0, 0)
        
        # Harvester priority targeting
        if self.role == 'harvester':
            self.update_harvester_priority_targeting(food_list, power_ups)
        
        # Apply swarm behaviors
        sep = self.separate(swarm_bots) * 2.0
        ali = self.align(swarm_bots) * 1.0
        coh = self.cohesion(swarm_bots) * float(self.role_data.get('cohesion_weight', 1.0))
        seek_food = self.seek_food(food_list, power_ups, swarm_bots) * float(self.role_data.get('food_seek_weight', 2.5))
        # Only non-warriors avoid predators
        if self.role != 'warrior':
            avoid_predators = self.avoid_predators(predators) * float(self.role_data.get('predator_avoid_weight', 4.0))
        else:
            avoid_predators = Vector2D(0, 0)
        # Harvester burst mode adjustments
        if self.role == 'harvester' and self.food_burst_active:
            ali = ali * 0.3
            coh = coh * 0.2
            seek_food = seek_food * 1.5
        
        # Apply forces
        self.acceleration = self.acceleration + sep + ali + coh + seek_food + avoid_predators
        
        # Update velocity and position
        self.velocity = self.velocity + self.acceleration
        self.velocity = self.velocity.limit(self.max_speed)
        self.position = self.position + self.velocity
        
        # Wrap around screen edges
        self.wrap_around()
        
        # Update trail
        self.trail.append((self.position.x, self.position.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        
        # Decrease energy
        self.energy -= 0.1
        if self.energy < 0:
            self.energy = 0

        # PredatorFood collection (edible by both bots and predators)
        from predator_food import PredatorFood
        for food in list(food_list):
            if isinstance(food, PredatorFood):
                distance = math.sqrt((self.position.x - food.position.x)**2 + (self.position.y - food.position.y)**2)
                if distance < self.radius + food.radius:
                    self.energy = min(100, self.energy + food.energy_value)
                    food_list.remove(food)
                    break

        # Attempt reproduction (harvesters only)
        if self.role == 'harvester':
            new_bot = self.attempt_reproduction(swarm_bots)
            if new_bot is not None:
                swarm_bots.append(new_bot)
        
        # Avoid obstacles or take damage if colliding
        if obstacles:
            for obstacle in obstacles:
                offset = self.position - obstacle.position
                dist = offset.magnitude()
                min_dist = self.radius + obstacle.radius + 2
                if dist < min_dist:
                    # Take damage if colliding
                    self.energy -= 2.0  # Increased damage per frame in obstacle
                    # Push bot out of obstacle
                    if dist > 0:
                        push = offset.normalize() * (min_dist - dist + 1)
                        self.position += push
                        # Apply impact to obstacle (momentum transfer)
                        if hasattr(obstacle, 'impact'):
                            obstacle.impact(-push * 0.05)  # Much smaller velocity change
                    # Flash obstacle
                    if hasattr(obstacle, 'flash'):
                        obstacle.flash()
                elif dist < min_dist + 30:
                    # Steer away if near
                    avoid_force = offset.normalize() * (1.5 * (min_dist + 30 - dist) / 30)
                    self.acceleration += avoid_force
    
    def separate(self, neighbors: List['SwarmBot']) -> Vector2D:
        """Separation: steer to avoid crowding local flockmates"""
        desired_separation = 25
        steer = Vector2D(0, 0)
        count = 0
        
        for other in neighbors:
            distance = math.sqrt((self.position.x - other.position.x)**2 + 
                               (self.position.y - other.position.y)**2)
            if 0 < distance < desired_separation:
                diff = self.position - other.position
                diff = diff.normalize()
                diff = diff * (1.0 / distance)
                steer = steer + diff
                count += 1
        
        if count > 0:
            steer = steer * (1.0 / count)
            steer = steer.normalize()
            steer = steer * self.max_speed
            steer = steer - self.velocity
            steer = steer.limit(self.max_force)
        
        return steer
    
    def align(self, neighbors: List['SwarmBot']) -> Vector2D:
        """Alignment: steer towards the average heading of neighbors"""
        neighbor_dist = 50
        sum_vel = Vector2D(0, 0)
        count = 0
        
        for other in neighbors:
            distance = math.sqrt((self.position.x - other.position.x)**2 + 
                               (self.position.y - other.position.y)**2)
            if 0 < distance < neighbor_dist:
                sum_vel = sum_vel + other.velocity
                count += 1
        
        if count > 0:
            sum_vel = sum_vel * (1.0 / count)
            sum_vel = sum_vel.normalize()
            sum_vel = sum_vel * self.max_speed
            steer = sum_vel - self.velocity
            steer = steer.limit(self.max_force)
            return steer
        
        return Vector2D(0, 0)
    
    def cohesion(self, neighbors: List['SwarmBot']) -> Vector2D:
        """Cohesion: steer to move toward the average position of neighbors"""
        neighbor_dist = 50
        sum_pos = Vector2D(0, 0)
        count = 0
        
        for other in neighbors:
            distance = math.sqrt((self.position.x - other.position.x)**2 + 
                               (self.position.y - other.position.y)**2)
            if 0 < distance < neighbor_dist:
                sum_pos = sum_pos + other.position
                count += 1
        
        if count > 0:
            sum_pos = sum_pos * (1.0 / count)
            return self.seek(sum_pos)
        
        return Vector2D(0, 0)
    
    def seek(self, target: Vector2D) -> Vector2D:
        """Seek a target position"""
        desired = target - self.position
        desired = desired.normalize()
        desired = desired * self.max_speed
        
        steer = desired - self.velocity
        steer = steer.limit(self.max_force)
        return steer
    
    def seek_food(self, food_list: List['Food'], power_ups: List['PowerUp'], nearby_bots: List['SwarmBot'] | None = None) -> Vector2D:
        """Seek the nearest food or power-up, prioritizing PredatorFood at double range"""
        from predator_food import PredatorFood
        if not food_list and not power_ups:
            return Vector2D(0, 0)
        closest_target: Food | PowerUp | None = None
        closest_distance = float('inf')
        # Priority for shouted food
        if self.target_food is not None and self.target_food in food_list:
            distance = math.sqrt((self.position.x - self.target_food.position.x)**2 + 
                               (self.position.y - self.target_food.position.y)**2)
            closest_distance = distance * 0.5  # High priority
            closest_target = self.target_food
        # Harvester priority target
        if (self.role == 'harvester' and self.priority_food_target is not None and 
            (self.priority_food_target in food_list or self.priority_food_target in power_ups)):
            distance = math.sqrt((self.position.x - self.priority_food_target.position.x)**2 + 
                               (self.position.y - self.priority_food_target.position.y)**2)
            weighted_distance = distance * 0.3
            if weighted_distance < closest_distance:
                closest_distance = weighted_distance
                closest_target = self.priority_food_target
        # 1. PredatorFood at double range, always highest priority
        predator_foods = [f for f in food_list if isinstance(f, PredatorFood)]
        if predator_foods:
            hunt_radius = float(self.role_data.get('priority_food_range', 60)) if self.role == 'harvester' else 60
            for pf in predator_foods:
                distance = math.sqrt((self.position.x - pf.position.x)**2 + (self.position.y - pf.position.y)**2)
                if distance < hunt_radius * 2 and distance < closest_distance:
                    closest_distance = distance
                    closest_target = pf
        # 2. Power-ups
        for power_up in power_ups:
            distance = math.sqrt((self.position.x - power_up.position.x)**2 + 
                               (self.position.y - power_up.position.y)**2)
            weighted_distance = distance * 0.7
            if weighted_distance < closest_distance:
                closest_distance = weighted_distance
                closest_target = power_up
        # 3. Regular food
        for food in food_list:
            if isinstance(food, PredatorFood):
                continue
            distance = math.sqrt((self.position.x - food.position.x)**2 + 
                               (self.position.y - food.position.y)**2)
            if distance < closest_distance:
                closest_distance = distance
                closest_target = food
        if closest_target is not None:
            desired = closest_target.position - self.position
            if desired.magnitude() > 0:
                return desired.normalize() * self.max_speed
        return Vector2D(0, 0)
    
    def avoid_predators(self, predators: List['Predator']) -> Vector2D:
        """Avoid predators with enhanced fear response and anti-clumping jitter"""
        steer = Vector2D(0, 0)
        jitter_strength = 0.2  # Small random jitter to break up clumps
        for predator in predators:
            distance = math.sqrt((self.position.x - predator.position.x)**2 + 
                               (self.position.y - predator.position.y)**2)
            # Stronger base avoidance and panic multipliers
            avoid_distance = 160  # Increased from 120
            if distance < 40:
                avoid_distance = 240
                panic_multiplier = 4.0  # Increased
            elif distance < 80:
                avoid_distance = 180
                panic_multiplier = 2.5  # Increased
            else:
                panic_multiplier = 1.2  # Slightly increased
            if distance < avoid_distance and distance > 0:
                diff = self.position - predator.position
                diff = diff.normalize()
                # Stronger avoidance force when closer
                force_multiplier = (avoid_distance - distance) / avoid_distance
                force_multiplier *= panic_multiplier
                # Add random jitter to break up clumps
                jitter = Vector2D(random.uniform(-jitter_strength, jitter_strength), random.uniform(-jitter_strength, jitter_strength))
                diff = (diff + jitter).normalize()
                diff = diff * force_multiplier
                steer = steer + diff
        if steer.magnitude() > 0:
            steer = steer.normalize()
            steer = steer * self.max_speed
            steer = steer - self.velocity
            steer = steer.limit(self.max_force * 3.5)  # Allow even stronger avoidance force
        return steer
    
    def wrap_around(self) -> None:
        """Wrap around screen edges"""
        if self.position.x < 0:
            self.position.x = self.screen_width
        elif self.position.x > self.screen_width:
            self.position.x = 0
        
        if self.position.y < 0:
            self.position.y = self.screen_height
        elif self.position.y > self.screen_height:
            self.position.y = 0
    
    def draw(self, screen: pygame.Surface, offset=(0, 0)) -> None:
        """Draw the bot"""
        ox, oy = offset
        # Draw trail
        if len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                alpha = i / len(self.trail)
                trail_color = (int(CYAN[0] * alpha), int(CYAN[1] * alpha), int(CYAN[2] * alpha))
                if i > 0:
                    x1, y1 = self.trail[i-1][0] + ox, self.trail[i-1][1] + oy
                    x2, y2 = self.trail[i][0] + ox, self.trail[i][1] + oy
                    pygame.draw.line(screen, trail_color, (x1, y1), (x2, y2), 1)
        # Draw bot
        color = self.color
        if self.energy <= 10:
            color = RED
        elif self.energy < 30:
            color = ORANGE
        pygame.draw.circle(screen, color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius)
        # Draw power-up buff effects
        if self.speed_boost_timer > 0:
            pulse_alpha = int(128 + 127 * math.sin(self.speed_boost_timer * 0.3))
            speed_color = (0, pulse_alpha, 255)
            pygame.draw.circle(screen, speed_color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 8, 2)
        if self.damage_boost_timer > 0:
            pulse_alpha = int(128 + 127 * math.sin(self.damage_boost_timer * 0.3))
            damage_color = (255, pulse_alpha, 0)
            pygame.draw.circle(screen, damage_color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 6, 2)
        # Scout shouting: pulsing yellow ring and radiating lines when shout_cooldown just set
        if self.role == 'scout' and self.shout_cooldown > 50:
            shout_radius = int((60 - self.shout_cooldown) * 2)
            pygame.draw.circle(screen, YELLOW, (int(self.position.x)+ox, int(self.position.y)+oy), shout_radius, 2)
            num_lines = 8
            for i in range(num_lines):
                angle = (2 * math.pi / num_lines) * i
                x1 = self.position.x + ox + math.cos(angle) * (self.radius + 2)
                y1 = self.position.y + oy + math.sin(angle) * (self.radius + 2)
                x2 = self.position.x + ox + math.cos(angle) * (shout_radius + 4)
                y2 = self.position.y + oy + math.sin(angle) * (shout_radius + 4)
                pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 2)
        
        if self.role == 'warrior' and self.taunt_effect_timer > 0:
            # Enhanced taunt effect: pulsing magenta ring and exclamation icon
            pulse_phase = (30 - self.taunt_effect_timer) / 30.0
            base_radius = 15
            max_radius = 28
            ring_radius = int(base_radius + (max_radius - base_radius) * pulse_phase)
            alpha = int(180 * (1 - pulse_phase) + 60)
            # Draw pulsing ring (simulate alpha by drawing multiple rings)
            for i in range(3):
                pygame.draw.circle(
                    screen,
                    (255, 0, 180),
                    (int(self.position.x)+ox, int(self.position.y)+oy),
                    ring_radius + i * 2,
                    2
                )
            # Draw exclamation mark above the bot
            font = pygame.font.SysFont(None, 28)
            ex_mark = font.render('!', True, (255, 0, 180))
            ex_rect = ex_mark.get_rect(center=(int(self.position.x)+ox, int(self.position.y)+oy - self.radius - 18))
            screen.blit(ex_mark, ex_rect)
        
        if self.role == 'harvester' and self.food_burst_active:
            burst_color = (0, 255, 100)
            pygame.draw.circle(screen, burst_color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 5, 2)
            if self.priority_food_target:
                pygame.draw.line(screen, burst_color, 
                               (int(self.position.x)+ox, int(self.position.y)+oy),
                               (int(self.priority_food_target.position.x)+ox, int(self.priority_food_target.position.y)+oy), 1)
        
        # Show reproduction readiness for harvesters
        if (self.role == 'harvester' and 
            self.reproduction_cooldown == 0 and 
            self.energy >= self.reproduction_energy_threshold and
            self.closest_food_distance <= 50):
            reproduction_color = (255, 255, 100)  # Bright yellow
            pygame.draw.circle(screen, reproduction_color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 8, 3)
        
        # Direction indicator
        direction = self.velocity.normalize() * 10
        end_x = self.position.x + direction.x
        end_y = self.position.y + direction.y
        pygame.draw.line(screen, WHITE, (self.position.x, self.position.y), (end_x, end_y), 1)

        # Warrior attack visual effect
        if self.role == 'warrior' and hasattr(self, 'attack_effect_timer') and self.attack_effect_timer > 0:
            # Draw a red arc/slash in the direction of attack
            attack_color = (255, 60, 60)
            arc_radius = self.radius + 12
            arc_width = 4
            # Draw arc in direction of velocity
            angle = math.atan2(self.velocity.y, self.velocity.x)
            start_angle = angle - 0.5
            end_angle = angle + 0.5
            center = (int(self.position.x), int(self.position.y))
            rect = pygame.Rect(center[0] - arc_radius, center[1] - arc_radius, arc_radius * 2, arc_radius * 2)
            pygame.draw.arc(screen, attack_color, rect, start_angle, end_angle, arc_width)
    
    def attack_predators(self, predators: List['Predator']) -> None:
        """Warrior actively attacks nearby predators if in range"""
        if self.role != 'warrior':
            return
        # Add attack cooldown
        if not hasattr(self, 'attack_cooldown'):
            self.attack_cooldown = 0
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            return
        attack_range = float(self.role_data.get('attack_range', 25))  # Use updated default
        attack_damage = float(self.role_data.get('attack_damage', 20))
        if self.damage_boost_timer > 0:
            attack_damage *= 2.0
        attacked = False
        for predator in predators:
            distance = math.sqrt((self.position.x - predator.position.x)**2 + (self.position.y - predator.position.y)**2)
            if distance <= attack_range:
                predator.health -= attack_damage
                # Flash predator for feedback
                if hasattr(predator, 'fight_flash_timer'):
                    predator.fight_flash_timer = max(predator.fight_flash_timer, 8)
                attacked = True
        if attacked:
            self.attack_cooldown = 15  # 15 frames cooldown
            self.attack_effect_timer = 6  # Show for 6 frames (0.1s at 60 FPS)
        # Decrement attack effect timer if active
        if hasattr(self, 'attack_effect_timer') and self.attack_effect_timer > 0:
            self.attack_effect_timer -= 1

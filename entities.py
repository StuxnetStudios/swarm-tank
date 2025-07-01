"""
Game entities: Food, PowerUp, and Predator classes
"""
from __future__ import annotations
import pygame
import random
import math
from typing import List, TYPE_CHECKING

from vector2d import Vector2D
from roles import RED, WHITE, GREEN

if TYPE_CHECKING:
    from swarm_bot import SwarmBot


class Food:
    """Food that the swarm can collect"""
    def __init__(self, x: float, y: float):
        self.position = Vector2D(x, y)
        self.radius = 5
        self.health_value = 20
        self.color = GREEN
    
    def draw(self, screen: pygame.Surface, offset=(0, 0)) -> None:
        ox, oy = offset
        pygame.draw.circle(screen, self.color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius)
        pygame.draw.circle(screen, (0, 200, 0), (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 2, 1)


class PowerUp:
    """Special power-up that provides enhanced benefits"""
    def __init__(self, x: float, y: float, power_type: str = 'health'):
        self.position = Vector2D(x, y)
        self.radius = 8
        self.power_type = power_type
        self.glow_intensity = 0
        self.glow_direction = 1
        
        if power_type == 'health':
            self.color = (0, 255, 0)
            self.health_value = 50
        elif power_type == 'speed':
            self.color = (0, 200, 255)
            self.health_value = 30
        elif power_type == 'damage':
            self.color = (255, 120, 0)
            self.health_value = 30
        else:
            self.color = (255, 255, 255)
    
    def update(self) -> None:
        """Update visual effects"""
        self.glow_intensity += self.glow_direction * 3
        if self.glow_intensity >= 100:
            self.glow_intensity = 100
            self.glow_direction = -1
        elif self.glow_intensity <= 0:
            self.glow_intensity = 0
            self.glow_direction = 1
    
    def draw(self, screen: pygame.Surface, offset=(0, 0)) -> None:
        ox, oy = offset
        # Draw glow effect
        for i in range(3):
            ring_radius = self.radius + 3 + (i * 2)
            pygame.draw.circle(screen, self.color, (int(self.position.x)+ox, int(self.position.y)+oy), ring_radius, 2)
        
        # Draw main power-up
        pygame.draw.circle(screen, self.color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius - 2, 1)


class Predator:
    """Predator that chases the swarm"""
    _predator_count = 0  # Class variable for unique naming

    def __init__(self, x: float, y: float, screen_width: int = 1200, screen_height: int = 800):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(random.uniform(-1, 1), random.uniform(-1, 1))
        self.acceleration = Vector2D(0, 0)  # For steering/forces
        self.radius = 10  # Larger predators
        self.max_speed = 4.0  # Set to 4.0 for balanced speed
        self.base_max_speed = self.max_speed  # For speed buffs
        self.max_force = 0.18  # Slightly increased for better maneuverability
        self.color = RED
        self.hunt_radius = 150  # Restore original detection range
        self.kill_radius = 12  # Distance at which they can kill bots
        self.max_health = 100.0
        self.health = 80.0  # Start at 80% health
        self.attack_cooldown = 0
        self.kills = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buff_timers = {'speed': 0, 'damage': 0}  # For power-up buffs
        self.fight_flash_timer = 0  # Frames to flash when fighting
        Predator._predator_count += 1
        self.name = f"Predator {Predator._predator_count}"

    def apply_force(self, force: Vector2D) -> None:
        """Apply a force to the predator (adds to acceleration)"""
        if not hasattr(self, 'acceleration'):
            self.acceleration = Vector2D(0, 0)
        self.acceleration += force

    def update(self, swarm_bots: List['SwarmBot'], food_list: list = None, all_predators: list = None, power_ups: list = None, rocks: list = None, fight_mode: bool = False) -> List['SwarmBot']:
        """Update predator behavior and return list of killed bots (or predators if fight_mode)"""
        killed_bots: List['SwarmBot'] = []
        if fight_mode:
            # Predator-vs-predator fight mode: hunt and attack other predators
            if not swarm_bots:
                return killed_bots
            # Find closest predator (excluding self)
            closest_pred = None
            closest_distance = float('inf')
            for pred in swarm_bots:
                if pred is self:
                    continue
                dist = (self.position - pred.position).magnitude()
                if dist < closest_distance:
                    closest_distance = dist
                    closest_pred = pred
            if closest_pred and closest_distance < self.hunt_radius:
                # Move toward and attack the closest predator
                desired = (closest_pred.position - self.position).normalize() * self.max_speed
                steer = desired - self.velocity
                steer = steer.limit(self.max_force)
                self.apply_force(steer)
                if closest_distance < self.kill_radius and self.attack_cooldown == 0:
                    # Attack! Deal damage and flash
                    closest_pred.health -= 40  # Dramatic damage
                    self.fight_flash_timer = 8
                    self.attack_cooldown = 12
                    if closest_pred.health <= 0:
                        # Remove defeated predator (handled in cleanup)
                        self.kills += 1
            # Usual movement update
            self.velocity += self.acceleration
            self.velocity = self.velocity.limit(self.max_speed)
            self.position += self.velocity
            self.acceleration = Vector2D(0, 0)
            # Clamp to screen
            self.position.x = max(0, min(self.position.x, self.screen_width))
            self.position.y = max(0, min(self.position.y, self.screen_height))
            # Cooldown
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
            # --- Ensure close-range dramatic fight/bounce always runs in fight mode ---
            if all_predators is not None:
                for other in all_predators:
                    if other is self:
                        continue
                    dist = (self.position - other.position).magnitude()
                    fight_range = 14  # much shorter range than before
                    min_dist = self.radius + other.radius
                    if dist < fight_range and dist > 0:
                        # Both lose more health (dramatic fight damage)
                        self.health -= 18.0
                        other.health -= 18.0
                        # Dramatic bounce apart
                        push = (self.position - other.position).normalize() * (fight_range - dist + 4)
                        self.position += push
                        other.position -= push
                        # Both get a longer attack cooldown to prevent rapid fighting
                        self.attack_cooldown = max(self.attack_cooldown, 18)
                        other.attack_cooldown = max(other.attack_cooldown, 18)
                        # Flash both predators magenta for longer
                        self.fight_flash_timer = 18
                        other.fight_flash_timer = 18
            return killed_bots
        
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Find closest bot with priority for low-health bots
        closest_bot = None
        closest_distance = float('inf')
        
        # Prioritize chasing leaders if any are present
        leader_bots = [bot for bot in swarm_bots if bot.role == 'leader']
        if leader_bots:
            # Find closest leader
            closest_leader = min(leader_bots, key=lambda b: (self.position - b.position).magnitude())
            leader_distance = (self.position - closest_leader.position).magnitude()
            if leader_distance < self.hunt_radius:
                # Chase leader directly
                future_pos = closest_leader.position + (closest_leader.velocity * 3)
                desired = future_pos - self.position
                desired = desired.normalize()
                speed_multiplier = 1.2 if leader_distance < 50 else 1.0
                desired = desired * (self.max_speed * speed_multiplier)
                steer = desired - self.velocity
                steer = steer.limit(self.max_force)
                self.velocity = self.velocity + steer
                # Kill leader if close enough and attack is ready
                if leader_distance < self.kill_radius and self.attack_cooldown == 0:
                    killed_bots.append(closest_leader)
                    self.kills += 1
                    self.health = min(self.max_health, self.health + 15)
                    self.attack_cooldown = 30
                return killed_bots
        
        for bot in swarm_bots:
            distance = math.sqrt((self.position.x - bot.position.x)**2 + 
                               (self.position.y - bot.position.y)**2)
            
            # Prioritize weak/low-health bots
            priority_multiplier = 1.0
            if bot.health < 30:
                priority_multiplier = 0.5  # Make weak bots more attractive targets
            elif bot.health < 50:
                priority_multiplier = 0.8
            
            adjusted_distance = distance * priority_multiplier
            
            if adjusted_distance < closest_distance:
                closest_distance = distance  # Use real distance for actual calculations
                closest_bot = bot
        
        # Enhanced hunting behavior
        from predator_food import PredatorFood
        # 1. Prioritize PredatorFood at double hunt radius
        predator_foods = [f for f in food_list if isinstance(f, PredatorFood)] if food_list else []
        if predator_foods:
            closest_pred_food = min(predator_foods, key=lambda f: (self.position - f.position).magnitude())
            pred_food_dist = (self.position - closest_pred_food.position).magnitude()
            if pred_food_dist < self.hunt_radius * 2:
                to_pred_food = closest_pred_food.position - self.position
                if to_pred_food.magnitude() > 0:
                    desired = to_pred_food.normalize() * self.max_speed
                    steer = desired - self.velocity
                    steer = steer.limit(self.max_force)
                    self.velocity = self.velocity + steer
        elif closest_bot and closest_distance < self.hunt_radius:
            # Predict bot movement for better interception
            future_pos = closest_bot.position + (closest_bot.velocity * 3)
            desired = future_pos - self.position
            desired = desired.normalize()
            
            # Speed boost when closing in on target
            speed_multiplier = 1.0
            if closest_distance < 50:
                speed_multiplier = 1.3  # 30% speed boost when close
            elif closest_distance < 80:
                speed_multiplier = 1.15  # 15% speed boost when medium range
            
            desired = desired * (self.max_speed * speed_multiplier)
            
            steer = desired - self.velocity
            steer = steer.limit(self.max_force)
            self.velocity = self.velocity + steer
            
            # Kill bot if close enough and attack is ready
            if closest_distance < self.kill_radius and self.attack_cooldown == 0:
                killed_bots.append(closest_bot)
                self.kills += 1
                self.health = min(self.max_health, self.health + 15)  # Gain health from kills
                self.attack_cooldown = 30  # Prevent instant multiple kills
                
                # Health boost from successful hunt (increased from 5 to 15)
                self.health = min(self.max_health, self.health + 15)
        elif power_ups and len(power_ups) > 0:
            # Prioritize collecting the closest power-up
            closest_powerup = min(power_ups, key=lambda p: (self.position - p.position).magnitude())
            to_powerup = closest_powerup.position - self.position
            dist = to_powerup.magnitude()
            if dist > 0:
                desired = to_powerup.normalize() * self.max_speed
                steer = desired - self.velocity
                steer = steer.limit(self.max_force)
                self.velocity = self.velocity + steer
        elif food_list and len(food_list) > 0:
            closest_food = min(food_list, key=lambda f: (self.position - f.position).magnitude())
            patrol_target = closest_food.position
            to_target = patrol_target - self.position
            dist = to_target.magnitude()
            if dist > 0:
                desired = to_target.normalize() * (self.max_speed * 0.6)
                steer = desired - self.velocity
                steer = steer.limit(self.max_force * 0.5)
                self.velocity = self.velocity + steer
        elif swarm_bots:
            center_x = sum(bot.position.x for bot in swarm_bots) / len(swarm_bots)
            center_y = sum(bot.position.y for bot in swarm_bots) / len(swarm_bots)
            patrol_target = Vector2D(center_x, center_y)
            to_target = patrol_target - self.position
            dist = to_target.magnitude()
            if dist > 0:
                desired = to_target.normalize() * (self.max_speed * 0.6)
                steer = desired - self.velocity
                steer = steer.limit(self.max_force * 0.5)
                self.velocity = self.velocity + steer

        # Avoid other predators
        if all_predators is not None:
            avoid_radius = 40
            avoid_force = Vector2D(0, 0)
            for other in all_predators:
                if other is self:
                    continue
                dist = (self.position - other.position).magnitude()
                if dist < avoid_radius and dist > 0:
                    diff = (self.position - other.position).normalize()
                    avoid_force = avoid_force + (diff / dist)
            if avoid_force.magnitude() > 0:
                avoid_force = avoid_force.normalize() * self.max_force
                self.velocity = self.velocity + avoid_force
        
        # Avoid rocks or take damage if colliding
        if rocks:
            for rock in rocks:
                offset = self.position - rock.position
                dist = offset.magnitude()
                min_dist = self.radius + rock.radius + 2
                if dist < min_dist:
                    self.health -= 2.0  # Increased damage per frame in rock
                    # Push predator out of rock
                    if dist > 0:
                        push = offset.normalize() * (min_dist - dist + 1)
                        self.position += push
                        # Apply impact to rock (momentum transfer)
                        if hasattr(rock, 'impact'):
                            rock.impact(-push * 0.07)
                    # Flash rock
                    if hasattr(rock, 'flash'):
                        rock.flash()
                elif dist < min_dist + 30:
                    # Steer away if near
                    avoid_force = offset.normalize() * (1.5 * (min_dist + 30 - dist) / 30)
                    self.acceleration += avoid_force

        # Predator vs Predator FIGHT: if colliding, both lose health and bounce (more dramatic, shorter range)
        if all_predators is not None:
            for other in all_predators:
                if other is self:
                    continue
                dist = (self.position - other.position).magnitude()
                fight_range = 14  # much shorter range than before
                min_dist = self.radius + other.radius
                if dist < fight_range and dist > 0:
                    # Both lose more health (dramatic fight damage)
                    self.health -= 18.0
                    other.health -= 18.0
                    # Dramatic bounce apart
                    push = (self.position - other.position).normalize() * (fight_range - dist + 4)
                    self.position += push
                    other.position -= push
                    # Both get a longer attack cooldown to prevent rapid fighting
                    self.attack_cooldown = max(self.attack_cooldown, 18)
                    other.attack_cooldown = max(other.attack_cooldown, 18)
                    # Flash both predators magenta for longer
                    self.fight_flash_timer = 18
                    other.fight_flash_timer = 18
                    # Optionally: trigger a global screen shake or flash (if desired, e.g. game.screen_flash_timer = max(...))

        # Predator power-up collection (moved from Game.update)
        if power_ups:
            for power_up in power_ups[:]:
                distance = (self.position - power_up.position).magnitude()
                if distance < self.radius + power_up.radius:
                    if not hasattr(self, 'buff_timers'):
                        self.buff_timers = {'speed': 0, 'damage': 0}
                        self.base_max_speed = self.max_speed
                    if power_up.power_type == 'speed':
                        self.buff_timers['speed'] = 300  # 5 seconds
                        self.max_speed = self.base_max_speed * 1.5
                    elif power_up.power_type == 'damage':
                        self.buff_timers['damage'] = 300
                        self.attack_cooldown = max(0, self.attack_cooldown - 10)
                    elif power_up.power_type == 'health':
                        self.health = min(self.max_health, self.health + power_up.health_value)
                    power_ups.remove(power_up)
                    break
        # PredatorFood collection (edible by both bots and predators)
        from predator_food import PredatorFood
        for food in list(food_list):
            if isinstance(food, PredatorFood):
                distance = (self.position - food.position).magnitude()
                if distance < self.radius + food.radius:
                    self.health = min(self.max_health, self.health + food.health_value)
                    food_list.remove(food)
                    break
        # Predator buff timer management
        if hasattr(self, 'buff_timers'):
            if self.buff_timers['speed'] > 0:
                self.buff_timers['speed'] -= 1
                if self.buff_timers['speed'] == 0:
                    self.max_speed = self.base_max_speed
            if self.buff_timers['damage'] > 0:
                self.buff_timers['damage'] -= 1

        # Update position
        self.velocity = self.velocity.limit(self.max_speed)
        self.position = self.position + self.velocity
        
        # Lose health over time (predators need to hunt to survive)
        self.health -= 0.08  # Use health instead of energy
        if self.health < 0:
            self.health = 0
        
        # Wrap around edges
        if self.position.x < 0:
            self.position.x = self.screen_width
        elif self.position.x > self.screen_width:
            self.position.x = 0
        if self.position.y < 0:
            self.position.y = self.screen_height
        elif self.position.y > self.screen_height:
            self.position.y = 0
        
        # --- Home attack logic: if 2+ predators are in range, attack Home ---
        home = None
        if rocks:
            for r in rocks:
                if hasattr(r, 'hitpoints') and hasattr(r, 'take_damage'):
                    home = r
                    break
        if home is not None:
            # Count predators in range of Home
            predators_in_range = 0
            for pred in all_predators or []:
                if pred is self:
                    continue
                dist = (pred.position - home.position).magnitude()
                if dist < home.radius + self.radius + 30:
                    predators_in_range += 1
            # If 2+ predators in range, attack Home
            if predators_in_range >= 2:
                dist_to_home = (self.position - home.position).magnitude()
                if dist_to_home < home.radius + self.radius + 30 and self.attack_cooldown == 0:
                    home.take_damage(60)  # Deal 60 damage per attack
                    self.attack_cooldown = 30

        return killed_bots
    
    def draw(self, screen: pygame.Surface, offset=(0, 0)) -> None:
        ox, oy = offset
        color = self.color
        if self.fight_flash_timer > 0:
            color = (255, 0, 255)  # Magenta flash when fighting
        elif self.health < 20:
            color = (150, 0, 0)  # Darker red when low health
        elif self.attack_cooldown > 0:
            color = (255, 50, 50)  # Bright red when recently attacked

        pygame.draw.circle(screen, color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius)
        pygame.draw.circle(screen, (255, 100, 100), (int(self.position.x)+ox, int(self.position.y)+oy), self.radius + 2, 1)

        # Draw name label above predator (topmost)
        font = pygame.font.Font(None, 20)
        name_surface = font.render(self.name, True, (255, 255, 255))
        name_rect = name_surface.get_rect()
        name_rect.center = (int(self.position.x)+ox, int(self.position.y)+oy - self.radius - 28)
        screen.blit(name_surface, name_rect)

        # Draw health bar above predator (below name)
        bar_width = 30
        bar_height = 4
        bar_x = int(self.position.x + ox - bar_width // 2)
        bar_y = int(self.position.y + oy - self.radius - 18)

        # Background bar (red)
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Health bar (green to red gradient based on health percentage)
        health_percentage = self.health / self.max_health
        health_width = int(bar_width * health_percentage)

        if health_percentage > 0.6:
            health_color = (0, 255, 0)  # Green
        elif health_percentage > 0.3:
            health_color = (255, 255, 0)  # Yellow
        else:
            health_color = (255, 0, 0)  # Red

        if health_width > 0:
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))

        # Health bar border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

        # Show kills count with text above predator (below health bar)
        if self.kills > 0:
            font = pygame.font.Font(None, 18)
            kill_text = f"Kills: {self.kills}"
            text_surface = font.render(kill_text, True, (255, 255, 0))  # Yellow text
            text_rect = text_surface.get_rect()
            text_rect.center = (int(self.position.x)+ox, int(self.position.y)+oy - self.radius - 8)
            screen.blit(text_surface, text_rect)

        # Draw kill radius when hunting (using regular red)
        if self.attack_cooldown == 0:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.position.x)+ox, int(self.position.y)+oy), self.kill_radius, 1)

        # Draw hunt radius (faded red)
        pygame.draw.circle(screen, (100, 0, 0), (int(self.position.x)+ox, int(self.position.y)+oy), min(self.hunt_radius, 80), 1)

        # Direction indicator (predator facing direction)
        direction = self.velocity.normalize() * 15
        end_x = self.position.x + ox + direction.x
        end_y = self.position.y + oy + direction.y
        pygame.draw.line(screen, WHITE, (self.position.x+ox, self.position.y+oy), (end_x, end_y), 2)

        # At end of draw, decrement fight_flash_timer
        if self.fight_flash_timer > 0:
            self.fight_flash_timer -= 1

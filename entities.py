"""
Game entities: Food, PowerUp, and Predator classes
"""
from __future__ import annotations
import pygame
import random
import math
from typing import List, TYPE_CHECKING

from vector2d import Vector2D
from roles import RED, WHITE, GREEN, MAGENTA, CYAN, ORANGE

if TYPE_CHECKING:
    from swarm_bot import SwarmBot


class Food:
    """Food that the swarm can collect"""
    def __init__(self, x: float, y: float):
        self.position = Vector2D(x, y)
        self.radius = 5
        self.energy_value = 20
        self.color = GREEN
    
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius)
        pygame.draw.circle(screen, (0, 200, 0), (int(self.position.x), int(self.position.y)), self.radius + 2, 1)


class PowerUp:
    """Special power-up that provides enhanced benefits"""
    def __init__(self, x: float, y: float, power_type: str = 'energy'):
        self.position = Vector2D(x, y)
        self.radius = 8
        self.power_type = power_type
        self.glow_intensity = 0
        self.glow_direction = 1
        
        if power_type == 'energy':
            self.color = MAGENTA
            self.energy_value = 50
        elif power_type == 'speed':
            self.color = CYAN
            self.energy_value = 30
        elif power_type == 'damage':
            self.color = ORANGE
            self.energy_value = 30
    
    def update(self) -> None:
        """Update visual effects"""
        self.glow_intensity += self.glow_direction * 3
        if self.glow_intensity >= 100:
            self.glow_intensity = 100
            self.glow_direction = -1
        elif self.glow_intensity <= 0:
            self.glow_intensity = 0
            self.glow_direction = 1
    
    def draw(self, screen: pygame.Surface) -> None:
        # Draw glow effect
        for i in range(3):
            ring_radius = self.radius + 3 + (i * 2)
            pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), ring_radius, 2)
        
        # Draw main power-up
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.position.x), int(self.position.y)), self.radius - 2, 1)


class Predator:
    """Predator that chases the swarm"""
    def __init__(self, x: float, y: float, screen_width: int = 1200, screen_height: int = 800):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(random.uniform(-1, 1), random.uniform(-1, 1))
        self.radius = 10  # Larger predators
        self.max_speed = 4.5  # Faster than most bots
        self.max_force = 0.15  # Better maneuverability
        self.color = RED
        self.hunt_radius = 150  # Larger detection range
        self.kill_radius = 12  # Distance at which they can kill bots
        self.max_health = 100.0
        self.health = 50.0  # Start at half max health
        self.attack_cooldown = 0
        self.kills = 0
        self.energy = 80.0  # Predators have energy that increases with kills
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def update(self, swarm_bots: List['SwarmBot']) -> List['SwarmBot']:
        """Update predator behavior and return list of killed bots"""
        killed_bots: List['SwarmBot'] = []
        
        if not swarm_bots:
            return killed_bots
        
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Find closest bot with priority for low-energy bots
        closest_bot = None
        closest_distance = float('inf')
        
        for bot in swarm_bots:
            distance = math.sqrt((self.position.x - bot.position.x)**2 + 
                               (self.position.y - bot.position.y)**2)
            
            # Prioritize weak/low-energy bots
            priority_multiplier = 1.0
            if bot.energy < 30:
                priority_multiplier = 0.5  # Make weak bots more attractive targets
            elif bot.energy < 50:
                priority_multiplier = 0.8
            
            adjusted_distance = distance * priority_multiplier
            
            if adjusted_distance < closest_distance:
                closest_distance = distance  # Use real distance for actual calculations
                closest_bot = bot
        
        # Enhanced hunting behavior
        if closest_bot and closest_distance < self.hunt_radius:
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
                self.energy = min(100, self.energy + 15)  # Gain energy from kills
                self.attack_cooldown = 30  # Prevent instant multiple kills
                
                # Health boost from successful hunt (increased from 5 to 15)
                self.health = min(self.max_health, self.health + 15)
        else:
            # Patrol behavior when no targets - move towards center of swarm
            if swarm_bots:
                center_x = sum(bot.position.x for bot in swarm_bots) / len(swarm_bots)
                center_y = sum(bot.position.y for bot in swarm_bots) / len(swarm_bots)
                center = Vector2D(center_x, center_y)
                
                desired = center - self.position
                if desired.magnitude() > 0:
                    desired = desired.normalize()
                    desired = desired * (self.max_speed * 0.6)  # Slower patrol speed
                    
                    steer = desired - self.velocity
                    steer = steer.limit(self.max_force * 0.5)
                    self.velocity = self.velocity + steer
        
        # Update position
        self.velocity = self.velocity.limit(self.max_speed)
        self.position = self.position + self.velocity
        
        # Lose energy over time (predators need to hunt to survive)
        self.energy -= 0.08  # Increased energy loss from 0.05 to 0.08
        if self.energy < 0:
            self.energy = 0
        
        # Wrap around edges
        if self.position.x < 0:
            self.position.x = self.screen_width
        elif self.position.x > self.screen_width:
            self.position.x = 0
        if self.position.y < 0:
            self.position.y = self.screen_height
        elif self.position.y > self.screen_height:
            self.position.y = 0
        
        return killed_bots
    
    def draw(self, screen: pygame.Surface) -> None:
        # Main predator body
        color = self.color
        if self.energy < 20:
            color = (150, 0, 0)  # Darker red when low energy
        elif self.attack_cooldown > 0:
            color = (255, 50, 50)  # Bright red when recently attacked
        
        pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), self.radius)
        pygame.draw.circle(screen, (255, 100, 100), (int(self.position.x), int(self.position.y)), self.radius + 2, 1)
        
        # Draw health bar above predator
        bar_width = 30
        bar_height = 4
        bar_x = int(self.position.x - bar_width // 2)
        bar_y = int(self.position.y - self.radius - 10)
        
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
        
        # Draw kill radius when hunting (using regular red)
        if self.attack_cooldown == 0:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.position.x), int(self.position.y)), self.kill_radius, 1)
        
        # Draw hunt radius (faded red)
        pygame.draw.circle(screen, (100, 0, 0), (int(self.position.x), int(self.position.y)), min(self.hunt_radius, 80), 1)
        
        # Show kills count with text
        if self.kills > 0:
            # Create font for kill count display
            font = pygame.font.Font(None, 18)  # Slightly larger font for better visibility
            kill_text = str(self.kills)
            text_surface = font.render(kill_text, True, (255, 255, 0))  # Yellow text for better contrast
            
            # Position text above and to the left of predator
            text_x = int(self.position.x - 15)
            text_y = int(self.position.y - 25)
            
            # Draw the kill count text only
            screen.blit(text_surface, (text_x, text_y))
        
        # Direction indicator (predator facing direction)
        direction = self.velocity.normalize() * 15
        end_x = self.position.x + direction.x
        end_y = self.position.y + direction.y
        pygame.draw.line(screen, WHITE, (self.position.x, self.position.y), (end_x, end_y), 2)

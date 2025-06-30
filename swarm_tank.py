"""
Main game class and entry point for the swarm simulation
"""
from __future__ import annotations
import pygame
import random
from typing import List

from roles import BOT_ROLES, BLACK, WHITE
from entities import Food, PowerUp, Predator
from swarm_bot import SwarmBot


# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60


class Game:
    """Main game class"""
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Swarm Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Game objects
        self.swarm_bots: List[SwarmBot] = []
        self.food_list: List[Food] = []
        self.power_ups: List[PowerUp] = []
        self.predators: List[Predator] = []
        
        # Initialize swarm
        for _ in range(50):
            x = random.uniform(50, SCREEN_WIDTH - 50)
            y = random.uniform(50, SCREEN_HEIGHT - 50)
            self.swarm_bots.append(SwarmBot(x, y, None, SCREEN_WIDTH, SCREEN_HEIGHT))
        
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
                    for _ in range(8):
                        x = random.uniform(20, SCREEN_WIDTH - 20)
                        y = random.uniform(20, SCREEN_HEIGHT - 20)
                        self.food_list.append(Food(x, y))
                elif event.key == pygame.K_p:  # type: ignore
                    # Spawn power-up
                    x = random.uniform(20, SCREEN_WIDTH - 20)
                    y = random.uniform(20, SCREEN_HEIGHT - 20)
                    power_type = random.choice(['energy', 'speed', 'damage'])
                    self.power_ups.append(PowerUp(x, y, power_type))
                elif event.key == pygame.K_b:  # type: ignore
                    # Manually spawn a new bot
                    x = random.uniform(50, SCREEN_WIDTH - 50)
                    y = random.uniform(50, SCREEN_HEIGHT - 50)
                    new_bot = SwarmBot(x, y, None, SCREEN_WIDTH, SCREEN_HEIGHT)
                    
                    # Apply any active swarm buffs to the new bot
                    if self.swarm_bots:  # If there are existing bots to check
                        sample_bot = self.swarm_bots[0]  # Check first bot for active buffs
                        if sample_bot.speed_boost_timer > 0:
                            new_bot.speed_boost_timer = sample_bot.speed_boost_timer
                            new_bot.max_speed = new_bot.base_max_speed * 1.5
                        if sample_bot.damage_boost_timer > 0:
                            new_bot.damage_boost_timer = sample_bot.damage_boost_timer
                    
                    self.swarm_bots.append(new_bot)
        
        return True
    
    def update(self) -> None:
        """Update game state"""
        # Update bots
        new_bots: List[SwarmBot] = []
        for bot in self.swarm_bots[:]:
            bot.update(self.swarm_bots, self.food_list, self.power_ups, self.predators)
            
            # Check for reproduction
            new_bot = bot.attempt_reproduction(self.swarm_bots)
            if new_bot:
                new_bots.append(new_bot)
            
            # Remove starved bots
            if bot.energy <= 0:
                self.swarm_bots.remove(bot)
        
        # Add newly reproduced bots
        self.swarm_bots.extend(new_bots)
        
        # Update predators and handle kills
        dead_predators = []
        for predator in self.predators[:]:
            killed_bots = predator.update(self.swarm_bots)
            # Remove killed bots from the swarm
            for killed_bot in killed_bots:
                if killed_bot in self.swarm_bots:
                    self.swarm_bots.remove(killed_bot)
            
            # Check if predator dies from starvation or damage
            if predator.energy <= 0 or predator.health <= 0:
                dead_predators.append(predator)
        
        # Handle dead predators - they drop food and get removed
        for dead_predator in dead_predators:
            self.predators.remove(dead_predator)
            
            # Drop food where predator died (3-5 food items)
            food_drops = random.randint(3, 5)
            for _ in range(food_drops):
                # Scatter food around the predator's death location
                offset_x = random.uniform(-30, 30)
                offset_y = random.uniform(-30, 30)
                food_x = max(20, min(SCREEN_WIDTH - 20, dead_predator.position.x + offset_x))
                food_y = max(20, min(SCREEN_HEIGHT - 20, dead_predator.position.y + offset_y))
                self.food_list.append(Food(food_x, food_y))
            
            # Respawn a new predator after some time (25% chance per dead predator)
            if random.random() < 0.25:
                x = random.uniform(50, SCREEN_WIDTH - 50)
                y = random.uniform(50, SCREEN_HEIGHT - 50)
                self.predators.append(Predator(x, y, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Update power-ups
        for power_up in self.power_ups:
            power_up.update()
        
        # Check food collection
        for bot in self.swarm_bots:
            # Check food consumption
            for food in self.food_list[:]:
                distance = (bot.position - food.position).magnitude()
                if distance < bot.radius + food.radius:
                    bot.energy = min(100, bot.energy + food.energy_value)
                    self.food_list.remove(food)
                    break
            
            # Check power-up collection
            for power_up in self.power_ups[:]:
                distance = (bot.position - power_up.position).magnitude()
                if distance < bot.radius + power_up.radius:
                    bot.energy = min(100, bot.energy + power_up.energy_value)
                    
                    # Apply power-up effects to ALL bots in the swarm
                    if power_up.power_type == 'speed':
                        for swarm_bot in self.swarm_bots:
                            swarm_bot.speed_boost_timer = 300  # 5 seconds at 60 FPS
                            swarm_bot.max_speed = swarm_bot.base_max_speed * 1.5  # 50% speed boost
                    elif power_up.power_type == 'damage':
                        for swarm_bot in self.swarm_bots:
                            swarm_bot.damage_boost_timer = 300  # 5 seconds at 60 FPS
                    # Energy power-ups still only affect the collector
                    
                    self.power_ups.remove(power_up)
                    break
        
        # Randomly spawn new food (increased spawn rate)
        if random.random() < 0.04:  # Increased from 2% to 4% chance per frame
            x = random.uniform(20, SCREEN_WIDTH - 20)
            y = random.uniform(20, SCREEN_HEIGHT - 20)
            self.food_list.append(Food(x, y))
        
        # Additional food spawning when food is scarce
        if len(self.food_list) < 15:  # Spawn extra food when below 15 items
            if random.random() < 0.06:  # 6% chance when food is scarce
                x = random.uniform(20, SCREEN_WIDTH - 20)
                y = random.uniform(20, SCREEN_HEIGHT - 20)
                self.food_list.append(Food(x, y))
        
        # Randomly spawn power-ups
        if random.random() < 0.005:  # 0.5% chance per frame
            x = random.uniform(20, SCREEN_WIDTH - 20)
            y = random.uniform(20, SCREEN_HEIGHT - 20)
            power_type = random.choice(['energy', 'speed', 'damage'])
            self.power_ups.append(PowerUp(x, y, power_type))
    
    def draw(self) -> None:
        """Draw everything"""
        self.screen.fill(BLACK)
        
        # Draw food
        for food in self.food_list:
            food.draw(self.screen)
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        
        # Draw predators
        for predator in self.predators:
            predator.draw(self.screen)
        
        # Draw bots
        for bot in self.swarm_bots:
            bot.draw(self.screen)
        
        # Draw info
        total_kills = sum(predator.kills for predator in self.predators)
        info_text = f"Bots: {len(self.swarm_bots)} | Food: {len(self.food_list)} | Power-ups: {len(self.power_ups)} | Predator Kills: {total_kills}"
        text_surface = self.font.render(info_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        
        # Role counts
        role_counts: dict[str, int] = {}
        for bot in self.swarm_bots:
            role_counts[bot.role] = role_counts.get(bot.role, 0) + 1
        
        y_offset = 35
        for role, count in role_counts.items():
            role_text = f"{role.title()}: {count}"
            role_surface = self.font.render(role_text, True, BOT_ROLES[role].color)
            self.screen.blit(role_surface, (10, y_offset))
            y_offset += 25
        
        # Active buffs display
        buff_x = SCREEN_WIDTH - 200
        buff_y = 10
        
        # Check if any bot has active buffs (since buffs affect whole swarm)
        has_speed_buff = any(bot.speed_boost_timer > 0 for bot in self.swarm_bots)
        has_damage_buff = any(bot.damage_boost_timer > 0 for bot in self.swarm_bots)
        
        if has_speed_buff or has_damage_buff:
            buff_title = self.font.render("Swarm Buffs:", True, WHITE)
            self.screen.blit(buff_title, (buff_x, buff_y))
            buff_y += 25
            
            if has_speed_buff:
                # Find the remaining timer (should be same for all bots)
                speed_timer = next(bot.speed_boost_timer for bot in self.swarm_bots if bot.speed_boost_timer > 0)
                speed_seconds = speed_timer // 60  # Convert frames to seconds
                speed_text = f"Speed Boost: ALL ({speed_seconds}s)"
                speed_surface = self.font.render(speed_text, True, (0, 255, 255))  # Cyan
                self.screen.blit(speed_surface, (buff_x, buff_y))
                buff_y += 20
            
            if has_damage_buff:
                # Find the remaining timer (should be same for all bots)
                damage_timer = next(bot.damage_boost_timer for bot in self.swarm_bots if bot.damage_boost_timer > 0)
                damage_seconds = damage_timer // 60  # Convert frames to seconds
                damage_text = f"Damage Boost: ALL ({damage_seconds}s)"
                damage_surface = self.font.render(damage_text, True, (255, 165, 0))  # Orange
                self.screen.blit(damage_surface, (buff_x, buff_y))
                buff_y += 20
        
        # Controls
        controls = ["Space: Spawn food", "P: Spawn power-up", "B: Spawn bot", "Escape: Quit"]
        for i, control in enumerate(controls):
            control_surface = self.font.render(control, True, WHITE)
            self.screen.blit(control_surface, (10, SCREEN_HEIGHT - 80 + i * 20))  # Reduced spacing
        
        pygame.display.flip()
    
    def run(self) -> None:
        """Main game loop"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


def main() -> None:
    """Entry point for the swarm tank simulation."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

"""
Main game class and entry point for the swarm simulation
"""
from __future__ import annotations
import pygame
from pygame import SRCALPHA
import random
from typing import List

from roles import BOT_ROLES, BLACK, WHITE
from entities import Food, PowerUp, Predator
from swarm_bot import SwarmBot
from obstacle import Obstacle
from cleanup import handle_dead_predators, remove_dead_bots


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
        self.obstacles: List[Obstacle] = []
        
        # Buffs
        self.speed_buff_stacks = 0
        self.damage_buff_stacks = 0
        self.speed_buff_timer = 0
        self.damage_buff_timer = 0
        
        # Initialize swarm
        for i in range(50):
            x = random.uniform(50, SCREEN_WIDTH - 50)
            y = random.uniform(50, SCREEN_HEIGHT - 50)
            if i == 0:
                self.swarm_bots.append(SwarmBot(x, y, 'leader', SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
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
        
        # Initialize obstacles
        for _ in range(6):
            x = random.uniform(40, SCREEN_WIDTH - 40)
            y = random.uniform(40, SCREEN_HEIGHT - 40)
            self.obstacles.append(Obstacle(x, y))
        
        self.historical_predator_kills = 0  # Track all-time predator kills
        self.screen_flash_timer = 0  # Timer for screen flash effect
        self.leader_down_message_timer = 0  # Timer for leader down message
        self.no_breeders_message_timer = 0  # Timer for no more breeders message
        self.shake_timer = 0  # Frames left for screen shake
        self.shake_magnitude = 0  # Shake intensity
        self.predator_fight_mode = False  # Flag for predator fight event
        self.predator_fight_timer = 0  # Timer for predator fight event
    
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
            # Warriors attack predators if in range
            bot.attack_predators(self.predators)
            # Check for reproduction
            new_bot = bot.attempt_reproduction(self.swarm_bots)
            if new_bot:
                new_bots.append(new_bot)
            # Mark starved bots for removal (do NOT remove here)
            if bot.energy <= 0:
                bots_to_remove.append(bot)
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
        # Remove dead predators and handle respawn/food drop
        handle_dead_predators(self)
        
        # Remove all dead bots and handle leader/harvester events
        remove_dead_bots(self, bots_to_remove)
        
        # Update power-ups
        for power_up in self.power_ups:
            power_up.update()
        
        # Update obstacles with collision
        for obstacle in self.obstacles:
            obstacle.update(SCREEN_WIDTH, SCREEN_HEIGHT, self.obstacles)
        
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
    
    def draw(self) -> None:
        """Draw everything"""
        # Screen shake offset
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            shake_x = random.randint(-self.shake_magnitude, self.shake_magnitude)
            shake_y = random.randint(-self.shake_magnitude, self.shake_magnitude)
            self.shake_timer -= 1
        # Screen flash effect
        if getattr(self, 'screen_flash_timer', 0) > 0:
            if self.screen_flash_timer % 10 < 7:
                self.screen.fill((255, 0, 0))
            else:
                self.screen.fill(BLACK)
            self.screen_flash_timer -= 1
        else:
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
                    buff_rect.center = (int(predator.position.x), int(predator.position.y - predator.radius - 18 - i * 18))
                    self.screen.blit(buff_surface, buff_rect)
        
        # Draw bots
        for bot in self.swarm_bots:
            bot.draw(self.screen, offset=(shake_x, shake_y))
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(self.screen, offset=(shake_x, shake_y))
        
        # Draw info
        total_kills = sum(predator.kills for predator in self.predators if predator.health > 0)
        info_text = (
            f"Bots: {len(self.swarm_bots)} | Food: {len(self.food_list)} | Power-ups: {len(self.power_ups)} | "
            f"Predator Kills: {total_kills} (All-time: {self.historical_predator_kills})"
        )
        text_surface = self.font.render(info_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))

        # Top predator kill streak
        if self.predators:
            top_pred = max(self.predators, key=lambda p: p.kills)
            if top_pred.kills > 0:
                idx = self.predators.index(top_pred) + 1
                streak_text = f"Top Predator Streak: P{idx} - {top_pred.kills}"
                streak_surface = self.font.render(streak_text, True, (255, 215, 0))  # Gold color
                self.screen.blit(streak_surface, (10, 32))
        
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
        has_speed_buff = self.speed_buff_stacks > 0
        has_damage_buff = self.damage_buff_stacks > 0
        if has_speed_buff or has_damage_buff:
            buff_title = self.font.render("Swarm Buffs:", True, WHITE)
            self.screen.blit(buff_title, (buff_x, buff_y))
            buff_y += 25
            if has_speed_buff:
                speed_seconds = self.speed_buff_timer // 60
                speed_mult = 1.5 ** self.speed_buff_stacks
                speed_text = f"Speed: x{speed_mult:.2f} ({self.speed_buff_stacks} stack{'s' if self.speed_buff_stacks > 1 else ''}, {speed_seconds}s)"
                speed_surface = self.font.render(speed_text, True, (0, 255, 255))
                self.screen.blit(speed_surface, (buff_x, buff_y))
                buff_y += 20
            if has_damage_buff:
                damage_seconds = self.damage_buff_timer // 60
                damage_mult = 2 ** self.damage_buff_stacks
                damage_text = f"Damage: x{damage_mult} ({self.damage_buff_stacks} stack{'s' if self.damage_buff_stacks > 1 else ''}, {damage_seconds}s)"
                damage_surface = self.font.render(damage_text, True, (255, 165, 0))
                self.screen.blit(damage_surface, (buff_x, buff_y))
                buff_y += 20
        
        # Predator buffs display
        pred_buff_x = SCREEN_WIDTH - 200
        pred_buff_y = buff_y + 20
        predator_has_buffs = any(
            hasattr(pred, 'buff_timers') and (pred.buff_timers.get('speed', 0) > 0 or pred.buff_timers.get('damage', 0) > 0)
            for pred in self.predators
        )
        if predator_has_buffs:
            pred_title = self.font.render("Predator Buffs:", True, WHITE)
            self.screen.blit(pred_title, (pred_buff_x, pred_buff_y))
            pred_buff_y += 25
            for idx, pred in enumerate(self.predators):
                if hasattr(pred, 'buff_timers'):
                    speed_time = pred.buff_timers.get('speed', 0)
                    damage_time = pred.buff_timers.get('damage', 0)
                    if speed_time > 0 or damage_time > 0:
                        pred_id = f"P{idx+1}"
                        buffs = []
                        if speed_time > 0:
                            buffs.append(f"Speed ({speed_time//60}s)")
                        if damage_time > 0:
                            buffs.append(f"Damage ({damage_time//60}s)")
                        buff_str = ", ".join(buffs)
                        color = (0, 255, 255) if speed_time > 0 else (255, 165, 0)
                        if speed_time > 0 and damage_time > 0:
                            color = (255, 255, 0)  # yellow for both
                        pred_text = f"{pred_id}: {buff_str}"
                        pred_surface = self.font.render(pred_text, True, color)
                        self.screen.blit(pred_surface, (pred_buff_x, pred_buff_y))
                        pred_buff_y += 20
        
        # Controls
        controls = ["Space: Spawn food", "P: Spawn power-up", "B: Spawn bot", "Escape: Quit"]
        for i, control in enumerate(controls):
            control_surface = self.font.render(control, True, WHITE)
            self.screen.blit(control_surface, (10, SCREEN_HEIGHT - 80 + i * 20))
        
        # Simple, bold WAR! overlay
        if getattr(self, 'leader_down_message_timer', 0) > 0:
            big_font = pygame.font.Font(None, 120)
            text = "WAR!"
            text_surf = big_font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect()  # type: ignore[attr-defined]
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.screen.blit(text_surf, text_rect)
            self.leader_down_message_timer -= 1
        # Simple, bold NO MORE BREEDERS! overlay
        if getattr(self, 'no_breeders_message_timer', 0) > 0:
            big_font = pygame.font.Font(None, 80)
            text = "NO MORE BREEDERS!"
            text_surf = big_font.render(text, True, (255, 100, 100))
            text_rect = text_surf.get_rect()  # type: ignore[attr-defined]
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
            self.screen.blit(text_surf, text_rect)
            self.no_breeders_message_timer -= 1
        # MAKE THEM FIGHT overlay
        if getattr(self, 'predator_fight_mode', False):
            big_font = pygame.font.Font(None, 80)
            text = "MAKE THEM FIGHT!"
            text_surf = big_font.render(text, True, (255, 0, 255))
            text_rect = text_surf.get_rect()  # type: ignore[attr-defined]
            text_rect.center = (SCREEN_WIDTH // 2, 120)
            self.screen.blit(text_surf, text_rect)
        
        pygame.display.flip()
    
    def run(self) -> str | None:
        """Main game loop"""
        running = True
        while running:
            result = self.handle_events()
            if result == 'restart':
                return 'restart'
            running = result
            self.update()
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

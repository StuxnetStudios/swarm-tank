import random
import math
import pygame
from vector2d import Vector2D

ROCK_COLOR = (120, 120, 180)
ROCK_OUTLINE = (180, 180, 255)

class Rock:
    """Drifting rock that bounces off screen edges and acts as an ore source"""
    def __init__(self, x: float, y: float, radius: float = 18, ore_amount: int = 10, max_ore: int = 10):
        self.position = Vector2D(x, y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 1.5)
        self.velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
        self.radius = radius
        self.collision_flash_timer = 0  # Frames to flash after collision
        self.ore_amount = ore_amount  # Amount of ore left in this rock
        self.max_ore = max_ore
        self.depleted = False
        self.replenish_timer = random.randint(300, 900)  # 5-15 seconds at 60 FPS

    def mine(self, amount: int = 1) -> int:
        """Mine ore from this rock. Returns the amount actually mined."""
        if self.depleted or self.ore_amount <= 0:
            return 0
        mined = min(amount, self.ore_amount)
        self.ore_amount -= mined
        if self.ore_amount <= 0:
            self.depleted = True
        return mined

    def flash(self) -> None:
        self.collision_flash_timer = 6  # Flash for 6 frames

    def handle_rock_collisions(self, all_rocks: list) -> None:
        """Detect and resolve collisions with other rocks, changing direction on impact."""
        for other in all_rocks:
            if other is self or getattr(other, 'is_home', False):
                continue
            offset = self.position - other.position
            dist = offset.magnitude()
            min_dist = self.radius + other.radius
            if dist < min_dist and dist > 0:
                # Simple elastic collision: swap velocities
                self.velocity, other.velocity = other.velocity, self.velocity
                # Push rocks apart
                push = offset.normalize() * (min_dist - dist + 1)
                self.position += push * 0.5
                other.position -= push * 0.5
                # Flash both rocks
                self.flash()
                other.flash()

    def impact(self, force: Vector2D) -> None:
        """Apply a velocity change to the rock when hit by a bot or predator."""
        self.velocity += force
        self.flash()

    def update(self, screen_width: int, screen_height: int, all_rocks: list | None = None) -> None:
        self.position += self.velocity
        # Bounce off edges
        if self.position.x - self.radius < 0 or self.position.x + self.radius > screen_width:
            self.velocity.x *= -1
        if self.position.y - self.radius < 0 or self.position.y + self.radius > screen_height:
            self.velocity.y *= -1
        # Clamp inside screen
        self.position.x = max(self.radius, min(screen_width - self.radius, self.position.x))
        self.position.y = max(self.radius, min(screen_height - self.radius, self.position.y))
        # Rock-rock collisions
        if all_rocks is not None:
            self.handle_rock_collisions(all_rocks)
        # Decrement flash timer
        if self.collision_flash_timer > 0:
            self.collision_flash_timer -= 1
        # Replenish ore on a randomized timer
        if self.ore_amount < self.max_ore:
            self.replenish_timer -= 1
            if self.replenish_timer <= 0:
                self.ore_amount += 1
                if self.ore_amount > 0:
                    self.depleted = False
                self.replenish_timer = random.randint(300, 900)  # Reset timer

    def draw(self, screen: pygame.Surface, offset: tuple[int, int] = (0, 0)) -> None:
        ox, oy = offset
        color = ROCK_COLOR
        if self.collision_flash_timer > 0:
            color = (255, 255, 120)  # Bright yellow flash
        pygame.draw.circle(screen, color, (int(self.position.x)+ox, int(self.position.y)+oy), int(self.radius))
        pygame.draw.circle(screen, ROCK_OUTLINE, (int(self.position.x)+ox, int(self.position.y)+oy), int(self.radius), 2)
        # Draw ore amount or X inside the rock
        if not self.depleted:
            font = pygame.font.Font(None, 18)
            ore_text = font.render(str(self.ore_amount), True, (200, 220, 255))
            ore_rect = ore_text.get_rect(center=(int(self.position.x)+ox, int(self.position.y)+oy))  # type: ignore
            screen.blit(ore_text, ore_rect)
        else:
            font = pygame.font.Font(None, 18)
            x_text = font.render('X', True, (180, 180, 180))
            x_rect = x_text.get_rect(center=(int(self.position.x)+ox, int(self.position.y)+oy))  # type: ignore
            screen.blit(x_text, x_rect)

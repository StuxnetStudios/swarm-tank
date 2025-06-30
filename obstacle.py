import random
import math
import pygame
from vector2d import Vector2D

OBSTACLE_COLOR = (120, 120, 180)
OBSTACLE_OUTLINE = (180, 180, 255)

class Obstacle:
    """Drifting obstacle that bounces off screen edges"""
    def __init__(self, x: float, y: float, radius: float = 18):
        self.position = Vector2D(x, y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 1.5)
        self.velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
        self.radius = radius
        self.collision_flash_timer = 0  # Frames to flash after collision

    def flash(self) -> None:
        self.collision_flash_timer = 6  # Flash for 6 frames

    def handle_obstacle_collisions(self, all_obstacles: list) -> None:
        """Detect and resolve collisions with other obstacles, changing direction on impact."""
        for other in all_obstacles:
            if other is self:
                continue
            offset = self.position - other.position
            dist = offset.magnitude()
            min_dist = self.radius + other.radius
            if dist < min_dist and dist > 0:
                # Simple elastic collision: swap velocities
                self.velocity, other.velocity = other.velocity, self.velocity
                # Push obstacles apart
                push = offset.normalize() * (min_dist - dist + 1)
                self.position += push * 0.5
                other.position -= push * 0.5
                # Flash both obstacles
                self.flash()
                other.flash()

    def impact(self, force: Vector2D) -> None:
        """Apply a velocity change to the obstacle when hit by a bot or predator."""
        self.velocity += force
        self.flash()

    def update(self, screen_width: int, screen_height: int, all_obstacles: list | None = None) -> None:
        self.position += self.velocity
        # Bounce off edges
        if self.position.x - self.radius < 0 or self.position.x + self.radius > screen_width:
            self.velocity.x *= -1
        if self.position.y - self.radius < 0 or self.position.y + self.radius > screen_height:
            self.velocity.y *= -1
        # Clamp inside screen
        self.position.x = max(self.radius, min(screen_width - self.radius, self.position.x))
        self.position.y = max(self.radius, min(screen_height - self.radius, self.position.y))
        # Obstacle-obstacle collisions
        if all_obstacles is not None:
            self.handle_obstacle_collisions(all_obstacles)
        # Decrement flash timer
        if self.collision_flash_timer > 0:
            self.collision_flash_timer -= 1

    def draw(self, screen: pygame.Surface, offset: tuple[int, int] = (0, 0)) -> None:
        ox, oy = offset
        color = OBSTACLE_COLOR
        if self.collision_flash_timer > 0:
            color = (255, 255, 120)  # Bright yellow flash
        pygame.draw.circle(screen, color, (int(self.position.x)+ox, int(self.position.y)+oy), int(self.radius))
        pygame.draw.circle(screen, OBSTACLE_OUTLINE, (int(self.position.x)+ox, int(self.position.y)+oy), int(self.radius), 2)

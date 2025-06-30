class PredatorFood:
    """Food dropped by a dead predator, edible by both bots and predators."""
    def __init__(self, x: float, y: float):
        from vector2d import Vector2D
        self.position = Vector2D(x, y)
        self.radius = 11  # Larger for visibility
        self.energy_value = 40  # Twice as valuable as normal food (20)
        self.color = (220, 0, 220)  # Brighter purple
        self.glow_intensity = 0
        self.glow_direction = 1

    def draw(self, screen, offset=(0, 0)):
        ox, oy = offset
        import pygame
        # Pulsing glow effect
        self.glow_intensity += self.glow_direction * 5
        if self.glow_intensity >= 80:
            self.glow_intensity = 80
            self.glow_direction = -1
        elif self.glow_intensity <= 0:
            self.glow_intensity = 0
            self.glow_direction = 1
        glow_radius = self.radius + 6 + self.glow_intensity // 20
        glow_color = (255, 100, 255)
        pygame.draw.circle(screen, glow_color, (int(self.position.x)+ox, int(self.position.y)+oy), glow_radius, 2)
        pygame.draw.circle(screen, self.color, (int(self.position.x)+ox, int(self.position.y)+oy), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.position.x)+ox, int(self.position.y)+oy), self.radius+2, 2)

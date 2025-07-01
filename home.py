import pygame
from vector2d import Vector2D

class Home:
    """Food and ore collection point for gatherers and miners"""
    def __init__(self, x: float, y: float, radius: int = 24):
        self.position = Vector2D(x, y)
        self.radius = radius
        self.color = (0, 120, 255)  # Blue, matches gatherer accent
        self.food_collected = 0
        self.ore_collected = 0  # Track ore as well
        self.max_hitpoints = 5000  # Buttload of hitpoints
        self.hitpoints = self.max_hitpoints
        self.repair_cooldown = 0
        self.is_home = True  # Mark this object as Home for collision logic
        self.craft_points = 0  # Ensure craft_points is always present
        # New resources
        self.ration = 0
        self.material = 0
        self.craftsmanship = 0  # Changed from workunit to craftsmanship

    def draw(self, screen: pygame.Surface, offset: tuple[int, int] = (0, 0)) -> None:
        ox, oy = offset
        center = (int(self.position.x) + ox, int(self.position.y) + oy)
        
        # Draw home circle
        pygame.draw.circle(screen, self.color, center, self.radius)
        pygame.draw.circle(screen, (255, 255, 255), center, self.radius - 4, 2)
        
        # Label: Home
        font = pygame.font.Font(None, 28)
        label = font.render("Home", True, (255, 255, 0))
        label_rect = label.get_rect(center=(center[0], center[1] - self.radius - 40))
        screen.blit(label, label_rect)
        
        # Food and Ore stats
        resources_font = pygame.font.Font(None, 22)
        resources_text = f"Food: {self.food_collected} | Ore: {self.ore_collected}"
        resources_surf = resources_font.render(resources_text, True, (200, 200, 200))
        resources_rect = resources_surf.get_rect(center=(center[0], center[1] - self.radius - 20))
        screen.blit(resources_surf, resources_rect)
        
        # Health bar
        bar_width = 80
        bar_height = 8
        bar_x = center[0] - bar_width // 2
        bar_y = center[1] + self.radius + 10
        
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        health_percentage = max(0, self.hitpoints / self.max_hitpoints)
        if health_percentage > 0.6:
            bar_color = (0, 255, 0)
        elif health_percentage > 0.3:
            bar_color = (255, 255, 0)
        else:
            bar_color = (255, 0, 0)
        
        health_bar_width = int(bar_width * health_percentage)
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, health_bar_width, bar_height))

    def deposit_food(self, amount: int = 1) -> None:
        self.food_collected += amount

    def deposit_ore(self, amount: int = 1) -> None:
        self.ore_collected += amount

    def take_damage(self, amount: int = 1) -> None:
        self.hitpoints = max(0, self.hitpoints - amount)

    def repair(self, amount: int = 10) -> None:
        self.hitpoints = min(self.max_hitpoints, self.hitpoints + amount)
        self.repair_cooldown = 10  # Prevent instant repeat repairs

    def update(self, *args: object, **kwargs: object) -> None:
        if self.repair_cooldown > 0:
            self.repair_cooldown -= 1

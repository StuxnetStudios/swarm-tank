import pygame
from typing import Optional, Any
from roles import BOT_ROLES, WHITE

class GameUI:
    def __init__(self, font: Optional[pygame.font.Font] = None):
        self.font = font or pygame.font.Font(None, 24)

    def draw(self, screen: pygame.Surface, game: Any, screen_height: int, screen_width: int) -> None:
        # --- Stat/info line at the very top ---
        total_kills = sum(predator.kills for predator in game.predators if predator.health > 0)
        info_text = (
            f"Bots: {len(game.swarm_bots)} | Predator Kills: {total_kills} | Total Bot Deaths: {getattr(game, 'bots_died', 0)}"
        )
        if not hasattr(game, 'historic_top_predator_streak'):
            game.historic_top_predator_streak = 0
        current_top = max((p.kills for p in game.predators), default=0)
        if current_top > game.historic_top_predator_streak:
            game.historic_top_predator_streak = current_top
        streak_text = f" | Predator Streak: {game.historic_top_predator_streak}"
        info_text += streak_text
        text_surface = self.font.render(info_text, True, WHITE)
        screen.blit(text_surface, (10, 8))

        # --- Combined Roles legend and counts (always visible, acts as color key and live stats) ---
        legend_y = 34
        legend_title = self.font.render("Roles:", True, WHITE)
        screen.blit(legend_title, (10, legend_y))
        legend_y += 22
        # Count bots by role
        role_counts = {role: 0 for role in BOT_ROLES}
        for bot in game.swarm_bots:
            role_counts[bot.role] = role_counts.get(bot.role, 0) + 1
        for role in BOT_ROLES:
            color = BOT_ROLES[role].color
            role_name = role.title()
            count = role_counts.get(role, 0)
            # Draw color circle
            pygame.draw.circle(screen, color, (18, legend_y + 10), 8)
            # Draw role name and count
            role_text = self.font.render(f"{role_name}: {count}", True, color)
            screen.blit(role_text, (32, legend_y))
            legend_y += 22
        legend_y += 8

        # Swarm buffs
        buff_x = 10
        buff_y = legend_y + 5
        has_speed_buff = game.speed_buff_stacks > 0
        has_damage_buff = game.damage_buff_stacks > 0
        if has_speed_buff or has_damage_buff:
            buff_title = self.font.render("Swarm Buffs:", True, WHITE)
            screen.blit(buff_title, (buff_x, buff_y))
            buff_y += 25
            if has_speed_buff:
                speed_seconds = game.speed_buff_timer // 60
                speed_mult = 1.5 ** game.speed_buff_stacks
                speed_text = f"Speed: x{speed_mult:.2f} ({game.speed_buff_stacks} stack{'s' if game.speed_buff_stacks > 1 else ''}, {speed_seconds}s)"
                speed_surface = self.font.render(speed_text, True, (0, 255, 255))
                screen.blit(speed_surface, (buff_x, buff_y))
                buff_y += 20
            if has_damage_buff:
                damage_seconds = game.damage_buff_timer // 60
                damage_mult = 2 ** game.damage_buff_stacks
                damage_text = f"Damage: x{damage_mult} ({game.damage_buff_stacks} stack{'s' if game.damage_buff_stacks > 1 else ''}, {damage_seconds}s)"
                damage_surface = self.font.render(damage_text, True, (255, 165, 0))
                screen.blit(damage_surface, (buff_x, buff_y))
                buff_y += 20
        buff_y += 10

        # Predator buffs
        pred_buff_x = 10
        pred_buff_y = buff_y + 20
        predator_has_buffs = any(
            hasattr(pred, 'buff_timers') and (pred.buff_timers.get('speed', 0) > 0 or pred.buff_timers.get('damage', 0) > 0)
            for pred in game.predators
        )
        if predator_has_buffs:
            pred_title = self.font.render("Predator Buffs:", True, WHITE)
            screen.blit(pred_title, (pred_buff_x, pred_buff_y))
            pred_buff_y += 25
            for idx, pred in enumerate(game.predators):
                if hasattr(pred, 'buff_timers'):
                    speed_time = pred.buff_timers.get('speed', 0)
                    damage_time = pred.buff_timers.get('damage', 0)
                    if speed_time > 0 or damage_time > 0:
                        buffs = []
                        if speed_time > 0:
                            buffs.append(f"Speed ({speed_time//60}s)")
                        if damage_time > 0:
                            buffs.append(f"Damage ({damage_time//60}s)")
                        buff_str = ", ".join(buffs)
                        color = (0, 255, 255) if speed_time > 0 else (255, 165, 0)
                        if speed_time > 0 and damage_time > 0:
                            color = (255, 255, 0)
                        pred_text = f"{buff_str}"
                        pred_surface = self.font.render(pred_text, True, color)
                        screen.blit(pred_surface, (pred_buff_x, pred_buff_y))
                        pred_buff_y += 20
        pred_buff_y += 10

        # Controls
        controls = ["Space: Spawn food", "P: Spawn power-up", "B: Spawn bot", "Escape: Quit"]
        for i, control in enumerate(controls):
            control_surface = self.font.render(control, True, WHITE)
            screen.blit(control_surface, (10, screen_height - 80 + i * 20))

        # Overlays
        if getattr(game, 'leader_down_message_timer', 0) > 0:
            big_font = pygame.font.Font(None, 120)
            war_text = "WAR!"
            war_surface = big_font.render(war_text, True, (255, 255, 255))
            war_rect = war_surface.get_rect()  # type: ignore[attr-defined]
            war_rect.center = (screen_width // 2, screen_height // 2)
            screen.blit(war_surface, war_rect)
        if getattr(game, 'no_breeders_message_timer', 0) > 0:
            big_font = pygame.font.Font(None, 80)
            breeders_text = "NO MORE BREEDERS!"
            breeders_surface = big_font.render(breeders_text, True, (255, 100, 100))
            breeders_rect = breeders_surface.get_rect()  # type: ignore[attr-defined]
            breeders_rect.center = (screen_width // 2, screen_height // 2 + 100)
            screen.blit(breeders_surface, breeders_rect)
        if getattr(game, 'predator_fight_mode', False):
            big_font = pygame.font.Font(None, 80)
            fight_text = "MAKE THEM FIGHT!"
            fight_surface = big_font.render(fight_text, True, (255, 0, 255))
            fight_rect = fight_surface.get_rect()  # type: ignore[attr-defined]
            fight_rect.center = (screen_width // 2, 120)
            screen.blit(fight_surface, fight_rect)

        # --- Starvation indicators ---
        for i, (x, y, timer, role) in enumerate(game.starvation_events[:] if hasattr(game, 'starvation_events') else []):
            if timer > 0:
                alpha = int(255 * (timer / 60))
                color = BOT_ROLES[role].color if role in BOT_ROLES else (255, 255, 255)
                s = pygame.Surface((80, 30,))
                pygame.draw.rect(s, (*color, alpha), (0, 0, 80, 30), border_radius=8)  # type: ignore[attr-defined]
                starved_surface = self.font.render("Starved!", True, (255, 255, 255))
                s.blit(starved_surface, (10, 5))
                screen.blit(s, (int(x) - 40, int(y) - 40))
                # Decrement timer for next frame
                game.starvation_events[i] = (x, y, timer - 1, role)
        # Remove finished events
        if hasattr(game, 'starvation_events'):
            game.starvation_events[:] = [e for e in game.starvation_events if e[2] > 0]
